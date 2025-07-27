import os
import re
import logging
from typing import List, Dict, Any, Optional
import PyPDF2
from docx import Document
import spacy
import nltk
from datetime import datetime

from models.cv_data import CVData, PersonalInfo, Education, WorkExperience, Skill, Language, Certification, Project

logger = logging.getLogger(__name__)

class CVProcessor:
    """Servicio para procesar y extraer información de CVs"""
    
    def __init__(self):
        """Inicializar el procesador de CVs"""
        self.nlp = None
        self._load_nlp_model()
        self._download_nltk_data()
    
    def _load_nlp_model(self):
        """Cargar modelo de spaCy para procesamiento de lenguaje natural"""
        try:
            # Intentar cargar modelo en español, si no está disponible usar inglés
            self.nlp = spacy.load("es_core_news_sm")
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("Modelo spaCy no disponible. Instalando...")
                # En producción, esto debería instalarse previamente
                self.nlp = None
    
    def _download_nltk_data(self):
        """Descargar datos necesarios de NLTK"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
    
    async def process_file(self, file_path: str) -> CVData:
        """
        Procesa un archivo CV y extrae la información
        
        Args:
            file_path: Ruta del archivo a procesar
            
        Returns:
            CVData: Datos extraídos del CV
        """
        try:
            logger.info(f"Procesando archivo: {file_path}")
            
            # Determinar tipo de archivo
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Extraer texto según el tipo de archivo
            if file_extension == '.pdf':
                text = self._extract_text_from_pdf(file_path)
            elif file_extension in ['.doc', '.docx']:
                text = self._extract_text_from_docx(file_path)
            elif file_extension == '.txt':
                text = self._extract_text_from_txt(file_path)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_extension}")
            
            # Procesar el texto extraído
            cv_data = self._process_text(text)
            cv_data.file_path = file_path
            cv_data.file_type = file_extension
            
            logger.info(f"CV procesado exitosamente: {file_path}")
            return cv_data
            
        except Exception as e:
            logger.error(f"Error procesando archivo {file_path}: {e}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extrae texto de un archivo PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {e}")
            raise
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extrae texto de un archivo DOCX"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extrayendo texto de DOCX: {e}")
            raise
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extrae texto de un archivo TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extrayendo texto de TXT: {e}")
            raise
    
    def _process_text(self, text: str) -> CVData:
        """
        Procesa el texto extraído y extrae la información estructurada
        
        Args:
            text: Texto extraído del CV
            
        Returns:
            CVData: Datos estructurados del CV
        """
        cv_data = CVData()
        
        # Dividir texto en secciones
        sections = self._split_into_sections(text)
        
        # Extraer información personal
        cv_data.personal_info = self._extract_personal_info(text, sections)
        
        # Extraer resumen/objetivo
        cv_data.summary = self._extract_summary(sections)
        cv_data.objective = self._extract_objective(sections)
        
        # Extraer experiencia laboral
        cv_data.work_experience = self._extract_work_experience(sections)
        
        # Extraer educación
        cv_data.education = self._extract_education(sections)
        
        # Extraer habilidades
        cv_data.skills = self._extract_skills(sections)
        
        # Extraer idiomas
        cv_data.languages = self._extract_languages(sections)
        
        # Extraer certificaciones
        cv_data.certifications = self._extract_certifications(sections)
        
        # Extraer proyectos
        cv_data.projects = self._extract_projects(sections)
        
        # Extraer logros
        cv_data.achievements = self._extract_achievements(sections)
        
        return cv_data
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Divide el texto en secciones basándose en encabezados"""
        sections = {}
        
        # Patrones comunes de encabezados
        headers = [
            r'(?i)(experiencia|experience|trabajo|work|laboral)',
            r'(?i)(educación|education|estudios|academic)',
            r'(?i)(habilidades|skills|competencias|competencies)',
            r'(?i)(idiomas|languages)',
            r'(?i)(certificaciones|certifications)',
            r'(?i)(proyectos|projects)',
            r'(?i)(logros|achievements|accomplishments)',
            r'(?i)(resumen|summary|perfil|profile)',
            r'(?i)(objetivo|objective|objetivos)'
        ]
        
        lines = text.split('\n')
        current_section = 'general'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Verificar si es un encabezado
            is_header = False
            for header_pattern in headers:
                if re.search(header_pattern, line):
                    # Guardar sección anterior
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Iniciar nueva sección
                    current_section = line.lower().replace(' ', '_')
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Guardar última sección
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_personal_info(self, text: str, sections: Dict[str, str]) -> PersonalInfo:
        """Extrae información personal del CV"""
        personal_info = PersonalInfo()
        
        # Patrones para email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            personal_info.email = email_match.group()
        
        # Patrones para teléfono
        phone_patterns = [
            r'\+?[\d\s\-\(\)]{10,}',  # Formato general
            r'\(\d{3}\)\s*\d{3}-\d{4}',  # (123) 456-7890
            r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
            r'\d{10}',  # 1234567890
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                personal_info.phone = phone_match.group()
                break
        
        # Patrones para LinkedIn
        linkedin_pattern = r'(?i)linkedin\.com/in/[\w\-]+'
        linkedin_match = re.search(linkedin_pattern, text)
        if linkedin_match:
            personal_info.linkedin = linkedin_match.group()
        
        # Patrones para portfolio/website
        website_patterns = [
            r'(?i)github\.com/[\w\-]+',
            r'(?i)portfolio\.com/[\w\-]+',
            r'(?i)www\.[\w\-\.]+\.com',
        ]
        
        for pattern in website_patterns:
            website_match = re.search(pattern, text)
            if website_match:
                personal_info.portfolio = website_match.group()
                break
        
        return personal_info
    
    def _extract_summary(self, sections: Dict[str, str]) -> Optional[str]:
        """Extrae el resumen del CV"""
        summary_sections = ['resumen', 'summary', 'perfil', 'profile']
        
        for section_name in summary_sections:
            if section_name in sections:
                return sections[section_name][:500]  # Limitar a 500 caracteres
        
        return None
    
    def _extract_objective(self, sections: Dict[str, str]) -> Optional[str]:
        """Extrae el objetivo del CV"""
        objective_sections = ['objetivo', 'objective', 'objetivos']
        
        for section_name in objective_sections:
            if section_name in sections:
                return sections[section_name][:500]
        
        return None
    
    def _extract_work_experience(self, sections: Dict[str, str]) -> List[WorkExperience]:
        """Extrae la experiencia laboral"""
        experience_list = []
        
        # Buscar en secciones de experiencia
        exp_sections = ['experiencia', 'experience', 'trabajo', 'work', 'laboral']
        
        for section_name in exp_sections:
            if section_name in sections:
                section_text = sections[section_name]
                experiences = self._parse_experience_section(section_text)
                experience_list.extend(experiences)
        
        return experience_list
    
    def _parse_experience_section(self, text: str) -> List[WorkExperience]:
        """Parsea una sección de experiencia laboral"""
        experiences = []
        
        # Dividir por líneas y buscar patrones de experiencia
        lines = text.split('\n')
        current_exp = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Patrón para nueva experiencia (empresa - posición - fechas)
            exp_pattern = r'^(.+?)\s*[-–—]\s*(.+?)\s*[-–—]\s*(.+?)$'
            match = re.search(exp_pattern, line)
            
            if match:
                # Guardar experiencia anterior si existe
                if current_exp:
                    experiences.append(current_exp)
                
                # Crear nueva experiencia
                company = match.group(1).strip()
                position = match.group(2).strip()
                dates = match.group(3).strip()
                
                current_exp = WorkExperience(
                    company=company,
                    position=position
                )
                
                # Parsear fechas
                date_info = self._parse_dates(dates)
                if date_info:
                    current_exp.start_date = date_info.get('start')
                    current_exp.end_date = date_info.get('end')
                    current_exp.current = date_info.get('current', False)
        
        # Agregar última experiencia
        if current_exp:
            experiences.append(current_exp)
        
        return experiences
    
    def _parse_dates(self, date_text: str) -> Optional[Dict[str, Any]]:
        """Parsea fechas de experiencia"""
        # Patrones comunes de fechas
        patterns = [
            r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4})',  # Jan 2020 - Dec 2021
            r'(\d{1,2}/\d{4})\s*[-–—]\s*(\d{1,2}/\d{4})',  # 01/2020 - 12/2021
            r'(\w+\s+\d{4})\s*[-–—]\s*(presente|actual|now|current)',  # Jan 2020 - Present
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_text, re.IGNORECASE)
            if match:
                start_date = match.group(1)
                end_date = match.group(2)
                
                # Verificar si es actual
                current = any(word in end_date.lower() for word in ['presente', 'actual', 'now', 'current'])
                
                return {
                    'start': self._normalize_date(start_date),
                    'end': None if current else self._normalize_date(end_date),
                    'current': current
                }
        
        return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normaliza fechas a formato YYYY-MM-DD"""
        try:
            # Implementar lógica de normalización de fechas
            # Por simplicidad, retornamos la fecha original
            return date_str
        except:
            return None
    
    def _extract_education(self, sections: Dict[str, str]) -> List[Education]:
        """Extrae información de educación"""
        education_list = []
        
        edu_sections = ['educación', 'education', 'estudios', 'academic']
        
        for section_name in edu_sections:
            if section_name in sections:
                section_text = sections[section_name]
                education = self._parse_education_section(section_text)
                education_list.extend(education)
        
        return education_list
    
    def _parse_education_section(self, text: str) -> List[Education]:
        """Parsea sección de educación"""
        education_list = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Patrón básico: institución - grado - fechas
            edu_pattern = r'^(.+?)\s*[-–—]\s*(.+?)\s*[-–—]\s*(.+?)$'
            match = re.search(edu_pattern, line)
            
            if match:
                institution = match.group(1).strip()
                degree = match.group(2).strip()
                dates = match.group(3).strip()
                
                education = Education(
                    institution=institution,
                    degree=degree
                )
                
                # Parsear fechas
                date_info = self._parse_dates(dates)
                if date_info:
                    education.start_date = date_info.get('start')
                    education.end_date = date_info.get('end')
                
                education_list.append(education)
        
        return education_list
    
    def _extract_skills(self, sections: Dict[str, str]) -> List[Skill]:
        """Extrae habilidades del CV"""
        skills_list = []
        
        skill_sections = ['habilidades', 'skills', 'competencias', 'competencies']
        
        for section_name in skill_sections:
            if section_name in sections:
                section_text = sections[section_name]
                skills = self._parse_skills_section(section_text)
                skills_list.extend(skills)
        
        return skills_list
    
    def _parse_skills_section(self, text: str) -> List[Skill]:
        """Parsea sección de habilidades"""
        skills_list = []
        
        # Dividir por comas, puntos, o líneas
        skill_items = re.split(r'[,;•\n]', text)
        
        for item in skill_items:
            item = item.strip()
            if item and len(item) > 2:  # Filtrar items muy cortos
                skill = Skill(name=item)
                skills_list.append(skill)
        
        return skills_list
    
    def _extract_languages(self, sections: Dict[str, str]) -> List[Language]:
        """Extrae idiomas del CV"""
        languages_list = []
        
        lang_sections = ['idiomas', 'languages']
        
        for section_name in lang_sections:
            if section_name in sections:
                section_text = sections[section_name]
                languages = self._parse_languages_section(section_text)
                languages_list.extend(languages)
        
        return languages_list
    
    def _parse_languages_section(self, text: str) -> List[Language]:
        """Parsea sección de idiomas"""
        languages_list = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Patrón: idioma - nivel
            lang_pattern = r'^(.+?)\s*[-–—]\s*(.+?)$'
            match = re.search(lang_pattern, line)
            
            if match:
                language_name = match.group(1).strip()
                level = match.group(2).strip()
                
                language = Language(
                    name=language_name,
                    level=level
                )
                languages_list.append(language)
        
        return languages_list
    
    def _extract_certifications(self, sections: Dict[str, str]) -> List[Certification]:
        """Extrae certificaciones del CV"""
        cert_list = []
        
        cert_sections = ['certificaciones', 'certifications']
        
        for section_name in cert_sections:
            if section_name in sections:
                section_text = sections[section_name]
                certifications = self._parse_certifications_section(section_text)
                cert_list.extend(certifications)
        
        return cert_list
    
    def _parse_certifications_section(self, text: str) -> List[Certification]:
        """Parsea sección de certificaciones"""
        cert_list = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Patrón básico: certificación - emisor - fecha
            cert_pattern = r'^(.+?)\s*[-–—]\s*(.+?)\s*[-–—]\s*(.+?)$'
            match = re.search(cert_pattern, line)
            
            if match:
                cert_name = match.group(1).strip()
                issuer = match.group(2).strip()
                date = match.group(3).strip()
                
                certification = Certification(
                    name=cert_name,
                    issuer=issuer
                )
                
                # Parsear fecha si es válida
                if re.match(r'\d{4}', date):
                    certification.issue_date = date
                
                cert_list.append(certification)
        
        return cert_list
    
    def _extract_projects(self, sections: Dict[str, str]) -> List[Project]:
        """Extrae proyectos del CV"""
        projects_list = []
        
        proj_sections = ['proyectos', 'projects']
        
        for section_name in proj_sections:
            if section_name in sections:
                section_text = sections[section_name]
                projects = self._parse_projects_section(section_text)
                projects_list.extend(projects)
        
        return projects_list
    
    def _parse_projects_section(self, text: str) -> List[Project]:
        """Parsea sección de proyectos"""
        projects_list = []
        
        lines = text.split('\n')
        current_project = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Patrón para nuevo proyecto
            proj_pattern = r'^(.+?)\s*[-–—]\s*(.+?)$'
            match = re.search(proj_pattern, line)
            
            if match:
                # Guardar proyecto anterior
                if current_project:
                    projects_list.append(current_project)
                
                # Crear nuevo proyecto
                name = match.group(1).strip()
                description = match.group(2).strip()
                
                current_project = Project(
                    name=name,
                    description=description
                )
        
        # Agregar último proyecto
        if current_project:
            projects_list.append(current_project)
        
        return projects_list
    
    def _extract_achievements(self, sections: Dict[str, str]) -> List[str]:
        """Extrae logros del CV"""
        achievements_list = []
        
        ach_sections = ['logros', 'achievements', 'accomplishments']
        
        for section_name in ach_sections:
            if section_name in sections:
                section_text = sections[section_name]
                achievements = self._parse_achievements_section(section_text)
                achievements_list.extend(achievements)
        
        return achievements_list
    
    def _parse_achievements_section(self, text: str) -> List[str]:
        """Parsea sección de logros"""
        achievements = []
        
        # Dividir por líneas o bullets
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Filtrar líneas muy cortas
                # Remover bullets comunes
                line = re.sub(r'^[•\-\*]\s*', '', line)
                achievements.append(line)
        
        return achievements 