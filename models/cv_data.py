from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EducationLevel(str, Enum):
    """Niveles de educación"""
    PRIMARY = "primaria"
    SECONDARY = "secundaria"
    HIGH_SCHOOL = "preparatoria"
    BACHELOR = "licenciatura"
    MASTER = "maestría"
    DOCTORATE = "doctorado"
    TECHNICAL = "técnico"
    CERTIFICATION = "certificación"

class ExperienceLevel(str, Enum):
    """Niveles de experiencia"""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"

class PersonalInfo(BaseModel):
    """Información personal extraída del CV"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    birth_date: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    website: Optional[str] = None

class Education(BaseModel):
    """Información de educación"""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    level: Optional[EducationLevel] = None
    gpa: Optional[float] = None
    description: Optional[str] = None

class WorkExperience(BaseModel):
    """Experiencia laboral"""
    company: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    level: Optional[ExperienceLevel] = None

class Skill(BaseModel):
    """Habilidad o competencia"""
    name: str
    category: Optional[str] = None  # programming, soft_skills, languages, etc.
    level: Optional[str] = None  # beginner, intermediate, advanced, expert
    years_experience: Optional[int] = None

class Language(BaseModel):
    """Idioma"""
    name: str
    level: Optional[str] = None  # basic, intermediate, advanced, native
    certification: Optional[str] = None

class Certification(BaseModel):
    """Certificación"""
    name: str
    issuer: str
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None

class Project(BaseModel):
    """Proyecto"""
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    url: Optional[str] = None
    role: Optional[str] = None

class CVData(BaseModel):
    """Datos completos extraídos del CV"""
    # Información básica
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    
    # Secciones principales
    summary: Optional[str] = None
    objective: Optional[str] = None
    
    # Experiencia y educación
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    
    # Habilidades y competencias
    skills: List[Skill] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    
    # Proyectos y logros
    projects: List[Project] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    
    # Metadatos
    extraction_date: datetime = Field(default_factory=datetime.now)
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    confidence_score: Optional[float] = None
    
    # Datos enriquecidos
    total_years_experience: Optional[int] = None
    highest_education_level: Optional[EducationLevel] = None
    primary_skills: List[str] = Field(default_factory=list)
    industry_experience: List[str] = Field(default_factory=list)
    
    def enrich_with_candidate_data(self, candidate_data: Dict[str, Any]):
        """Enriquece los datos del CV con información del candidato"""
        if candidate_data.get('firstName') and candidate_data.get('lastName'):
            self.personal_info.full_name = f"{candidate_data['firstName']} {candidate_data['lastName']}"
        
        if candidate_data.get('email'):
            self.personal_info.email = candidate_data['email']
        
        if candidate_data.get('phone'):
            self.personal_info.phone = candidate_data['phone']
        
        if candidate_data.get('address'):
            self.personal_info.address = candidate_data['address']
        
        if candidate_data.get('city'):
            self.personal_info.city = candidate_data['city']
        
        if candidate_data.get('state'):
            self.personal_info.state = candidate_data['state']
        
        if candidate_data.get('linkedIn'):
            self.personal_info.linkedin = candidate_data['linkedIn']
        
        if candidate_data.get('portfolio'):
            self.personal_info.portfolio = candidate_data['portfolio']
        
        # Calcular años totales de experiencia
        if self.work_experience:
            total_years = 0
            for exp in self.work_experience:
                if exp.start_date and exp.end_date:
                    try:
                        start = datetime.strptime(exp.start_date, "%Y-%m-%d")
                        end = datetime.strptime(exp.end_date, "%Y-%m-%d") if not exp.current else datetime.now()
                        total_years += (end - start).days / 365.25
                    except:
                        pass
            self.total_years_experience = int(total_years)
        
        # Determinar nivel de educación más alto
        if self.education:
            education_levels = {
                EducationLevel.PRIMARY: 1,
                EducationLevel.SECONDARY: 2,
                EducationLevel.HIGH_SCHOOL: 3,
                EducationLevel.TECHNICAL: 4,
                EducationLevel.BACHELOR: 5,
                EducationLevel.MASTER: 6,
                EducationLevel.DOCTORATE: 7
            }
            
            highest_level = None
            highest_score = 0
            
            for edu in self.education:
                if edu.level and education_levels.get(edu.level, 0) > highest_score:
                    highest_score = education_levels[edu.level]
                    highest_level = edu.level
            
            self.highest_education_level = highest_level
        
        # Extraer habilidades principales
        if self.skills:
            self.primary_skills = [skill.name for skill in self.skills[:10]]  # Top 10 habilidades
        
        # Extraer industrias de experiencia
        if self.work_experience:
            industries = set()
            for exp in self.work_experience:
                if exp.company:
                    # Aquí podrías implementar lógica para detectar industria por nombre de empresa
                    industries.add(exp.company)
            self.industry_experience = list(industries)

class CVExtractionRequest(BaseModel):
    """Solicitud de extracción de CV"""
    candidate_id: str
    file_path: str
    candidate_data: Optional[Dict[str, Any]] = None

class CVExtractionResponse(BaseModel):
    """Respuesta de extracción de CV"""
    success: bool
    message: str
    candidate_id: Optional[str] = None
    processing_id: Optional[str] = None
    cv_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 