import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor

from models.cv_data import CVData

logger = logging.getLogger(__name__)

class DatabaseService:
    """Servicio para manejar la base de datos de datos extraídos de CVs"""
    
    def __init__(self):
        """Inicializar el servicio de base de datos"""
        self.connection = None
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'lumina_consultora')
        
        # Crear tabla si no existe
        self._ensure_table_exists()
    
    async def connect(self):
        """Conectar a la base de datos"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=DictCursor,
                charset='utf8mb4'
            )
            logger.info("✅ Conexión a base de datos establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            raise
    
    async def disconnect(self):
        """Desconectar de la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Conexión a base de datos cerrada")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud de la base de datos"""
        try:
            if not self.connection or not self.connection.open:
                return {"status": "disconnected"}
            
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            return {
                "status": "connected",
                "database": self.database,
                "host": self.host
            }
        except Exception as e:
            logger.error(f"Error en health check: {e}")
            return {"status": "error", "message": str(e)}
    
    def _ensure_table_exists(self):
        """Asegurar que la tabla de datos de CV existe"""
        try:
            # Crear conexión temporal para crear la tabla
            temp_connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            
            with temp_connection.cursor() as cursor:
                # Crear tabla si no existe
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS cv_extracted_data (
                    id VARCHAR(36) PRIMARY KEY,
                    candidate_id VARCHAR(36) NOT NULL,
                    personal_info JSON,
                    summary TEXT,
                    objective TEXT,
                    work_experience JSON,
                    education JSON,
                    skills JSON,
                    languages JSON,
                    certifications JSON,
                    projects JSON,
                    achievements JSON,
                    metadata JSON,
                    extraction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_candidate_id (candidate_id),
                    INDEX idx_extraction_date (extraction_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """
                
                cursor.execute(create_table_sql)
                temp_connection.commit()
                
            temp_connection.close()
            logger.info("✅ Tabla cv_extracted_data verificada/creada")
            
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            # No lanzar excepción aquí, el servicio puede funcionar sin la tabla
    
    async def save_cv_data(self, candidate_id: str, cv_data: CVData) -> bool:
        """
        Guarda los datos extraídos del CV en la base de datos
        
        Args:
            candidate_id: ID del candidato
            cv_data: Datos extraídos del CV
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            if not self.connection or not self.connection.open:
                await self.connect()
            
            # Generar ID único para el registro
            import uuid
            record_id = str(uuid.uuid4())
            
            # Preparar datos para guardar
            data_dict = cv_data.dict()
            
            # Separar datos en columnas específicas
            personal_info = json.dumps(data_dict.get('personal_info', {}), ensure_ascii=False)
            work_experience = json.dumps(data_dict.get('work_experience', []), ensure_ascii=False)
            education = json.dumps(data_dict.get('education', []), ensure_ascii=False)
            skills = json.dumps(data_dict.get('skills', []), ensure_ascii=False)
            languages = json.dumps(data_dict.get('languages', []), ensure_ascii=False)
            certifications = json.dumps(data_dict.get('certifications', []), ensure_ascii=False)
            projects = json.dumps(data_dict.get('projects', []), ensure_ascii=False)
            achievements = json.dumps(data_dict.get('achievements', []), ensure_ascii=False)
            
            # Metadatos adicionales
            metadata = {
                'file_path': cv_data.file_path,
                'file_type': cv_data.file_type,
                'confidence_score': cv_data.confidence_score,
                'total_years_experience': cv_data.total_years_experience,
                'highest_education_level': cv_data.highest_education_level.value if cv_data.highest_education_level else None,
                'primary_skills': cv_data.primary_skills,
                'industry_experience': cv_data.industry_experience
            }
            
            with self.connection.cursor() as cursor:
                # Verificar si ya existe un registro para este candidato
                cursor.execute(
                    "SELECT id FROM cv_extracted_data WHERE candidate_id = %s",
                    (candidate_id,)
                )
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # Actualizar registro existente
                    update_sql = """
                    UPDATE cv_extracted_data SET
                        personal_info = %s,
                        summary = %s,
                        objective = %s,
                        work_experience = %s,
                        education = %s,
                        skills = %s,
                        languages = %s,
                        certifications = %s,
                        projects = %s,
                        achievements = %s,
                        metadata = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE candidate_id = %s
                    """
                    
                    cursor.execute(update_sql, (
                        personal_info,
                        data_dict.get('summary'),
                        data_dict.get('objective'),
                        work_experience,
                        education,
                        skills,
                        languages,
                        certifications,
                        projects,
                        achievements,
                        json.dumps(metadata, ensure_ascii=False),
                        candidate_id
                    ))
                    
                    logger.info(f"📝 Datos de CV actualizados para candidato: {candidate_id}")
                else:
                    # Insertar nuevo registro
                    insert_sql = """
                    INSERT INTO cv_extracted_data (
                        id, candidate_id, personal_info, summary, objective,
                        work_experience, education, skills, languages,
                        certifications, projects, achievements, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_sql, (
                        record_id,
                        candidate_id,
                        personal_info,
                        data_dict.get('summary'),
                        data_dict.get('objective'),
                        work_experience,
                        education,
                        skills,
                        languages,
                        certifications,
                        projects,
                        achievements,
                        json.dumps(metadata, ensure_ascii=False)
                    ))
                    
                    logger.info(f"💾 Datos de CV guardados para candidato: {candidate_id}")
                
                self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error guardando datos de CV para candidato {candidate_id}: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    async def get_cv_data(self, candidate_id: str) -> Optional[CVData]:
        """
        Obtiene los datos extraídos del CV de un candidato
        
        Args:
            candidate_id: ID del candidato
            
        Returns:
            CVData: Datos extraídos del CV o None si no se encuentra
        """
        try:
            if not self.connection or not self.connection.open:
                await self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM cv_extracted_data WHERE candidate_id = %s",
                    (candidate_id,)
                )
                record = cursor.fetchone()
                
                if not record:
                    return None
                
                # Reconstruir objeto CVData
                cv_data = CVData()
                
                # Cargar datos personales
                if record['personal_info']:
                    personal_info = json.loads(record['personal_info'])
                    cv_data.personal_info = personal_info
                
                # Cargar datos básicos
                cv_data.summary = record['summary']
                cv_data.objective = record['objective']
                
                # Cargar arrays JSON
                if record['work_experience']:
                    cv_data.work_experience = json.loads(record['work_experience'])
                
                if record['education']:
                    cv_data.education = json.loads(record['education'])
                
                if record['skills']:
                    cv_data.skills = json.loads(record['skills'])
                
                if record['languages']:
                    cv_data.languages = json.loads(record['languages'])
                
                if record['certifications']:
                    cv_data.certifications = json.loads(record['certifications'])
                
                if record['projects']:
                    cv_data.projects = json.loads(record['projects'])
                
                if record['achievements']:
                    cv_data.achievements = json.loads(record['achievements'])
                
                # Cargar metadatos
                if record['metadata']:
                    metadata = json.loads(record['metadata'])
                    cv_data.file_path = metadata.get('file_path')
                    cv_data.file_type = metadata.get('file_type')
                    cv_data.confidence_score = metadata.get('confidence_score')
                    cv_data.total_years_experience = metadata.get('total_years_experience')
                    cv_data.primary_skills = metadata.get('primary_skills', [])
                    cv_data.industry_experience = metadata.get('industry_experience', [])
                
                cv_data.extraction_date = record['extraction_date']
                
                return cv_data
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de CV para candidato {candidate_id}: {e}")
            return None
    
    async def delete_cv_data(self, candidate_id: str) -> bool:
        """
        Elimina los datos extraídos del CV de un candidato
        
        Args:
            candidate_id: ID del candidato
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            if not self.connection or not self.connection.open:
                await self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM cv_extracted_data WHERE candidate_id = %s",
                    (candidate_id,)
                )
                
                self.connection.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"🗑️ Datos de CV eliminados para candidato: {candidate_id}")
                    return True
                else:
                    logger.warning(f"⚠️ No se encontraron datos de CV para eliminar: {candidate_id}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Error eliminando datos de CV para candidato {candidate_id}: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    async def get_all_cv_data(self, limit: int = 100, offset: int = 0) -> list:
        """
        Obtiene todos los datos de CV con paginación
        
        Args:
            limit: Límite de registros
            offset: Desplazamiento
            
        Returns:
            list: Lista de datos de CV
        """
        try:
            if not self.connection or not self.connection.open:
                await self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM cv_extracted_data ORDER BY extraction_date DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
                
                records = cursor.fetchall()
                cv_data_list = []
                
                for record in records:
                    cv_data = await self._record_to_cv_data(record)
                    if cv_data:
                        cv_data_list.append(cv_data)
                
                return cv_data_list
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo todos los datos de CV: {e}")
            return []
    
    async def _record_to_cv_data(self, record: Dict[str, Any]) -> Optional[CVData]:
        """Convierte un registro de la base de datos a objeto CVData"""
        try:
            cv_data = CVData()
            
            # Cargar datos personales
            if record['personal_info']:
                personal_info = json.loads(record['personal_info'])
                cv_data.personal_info = personal_info
            
            # Cargar datos básicos
            cv_data.summary = record['summary']
            cv_data.objective = record['objective']
            
            # Cargar arrays JSON
            if record['work_experience']:
                cv_data.work_experience = json.loads(record['work_experience'])
            
            if record['education']:
                cv_data.education = json.loads(record['education'])
            
            if record['skills']:
                cv_data.skills = json.loads(record['skills'])
            
            if record['languages']:
                cv_data.languages = json.loads(record['languages'])
            
            if record['certifications']:
                cv_data.certifications = json.loads(record['certifications'])
            
            if record['projects']:
                cv_data.projects = json.loads(record['projects'])
            
            if record['achievements']:
                cv_data.achievements = json.loads(record['achievements'])
            
            # Cargar metadatos
            if record['metadata']:
                metadata = json.loads(record['metadata'])
                cv_data.file_path = metadata.get('file_path')
                cv_data.file_type = metadata.get('file_type')
                cv_data.confidence_score = metadata.get('confidence_score')
                cv_data.total_years_experience = metadata.get('total_years_experience')
                cv_data.primary_skills = metadata.get('primary_skills', [])
                cv_data.industry_experience = metadata.get('industry_experience', [])
            
            cv_data.extraction_date = record['extraction_date']
            
            return cv_data
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo registro a CVData: {e}")
            return None 