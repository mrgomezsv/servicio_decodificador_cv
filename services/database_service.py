import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

from models.cv_data import CVData

logger = logging.getLogger(__name__)

class DatabaseService:
    """Servicio para manejar la base de datos de datos extraídos de CVs"""
    
    def __init__(self):
        """Inicializar el servicio de base de datos"""
        self.connection = None
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 5432))  # Puerto por defecto de PostgreSQL
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'consultora_db')
        
        # Crear tabla si no existe
        self._ensure_table_exists()
    
    async def connect(self):
        """Conectar a la base de datos"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursor_factory=RealDictCursor
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
    
    async def health_check(self) -> bool:
        """Verificar la salud de la base de datos"""
        try:
            await self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"❌ Error en health check: {e}")
            return False
        finally:
            await self.disconnect()
    
    def _ensure_table_exists(self):
        """Crear la tabla cv_extracted_data si no existe"""
        try:
            with psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS cv_extracted_data (
                            id VARCHAR(36) PRIMARY KEY,
                            candidate_id VARCHAR(36) NOT NULL,
                            personal_info JSONB,
                            summary TEXT,
                            objective TEXT,
                            work_experience JSONB,
                            education JSONB,
                            skills JSONB,
                            languages JSONB,
                            certifications JSONB,
                            projects JSONB,
                            achievements JSONB,
                            metadata JSONB,
                            extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT fk_candidate FOREIGN KEY (candidate_id) REFERENCES "Candidate"(id) ON DELETE CASCADE
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_cv_candidate_id ON cv_extracted_data(candidate_id);
                        CREATE INDEX IF NOT EXISTS idx_cv_extraction_date ON cv_extracted_data(extraction_date);
                    """)
                    conn.commit()
                    logger.info("✅ Tabla cv_extracted_data verificada/creada")
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            raise
    
    async def save_cv_data(self, cv_data: CVData) -> bool:
        """Guardar datos extraídos del CV"""
        try:
            await self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO cv_extracted_data (
                        id, candidate_id, personal_info, summary, objective,
                        work_experience, education, skills, languages,
                        certifications, projects, achievements, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT (id) DO UPDATE SET
                        personal_info = EXCLUDED.personal_info,
                        summary = EXCLUDED.summary,
                        objective = EXCLUDED.objective,
                        work_experience = EXCLUDED.work_experience,
                        education = EXCLUDED.education,
                        skills = EXCLUDED.skills,
                        languages = EXCLUDED.languages,
                        certifications = EXCLUDED.certifications,
                        projects = EXCLUDED.projects,
                        achievements = EXCLUDED.achievements,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    cv_data.id,
                    cv_data.candidate_id,
                    json.dumps(cv_data.personal_info.dict()) if cv_data.personal_info else None,
                    cv_data.summary,
                    cv_data.objective,
                    json.dumps([exp.dict() for exp in cv_data.work_experience]) if cv_data.work_experience else None,
                    json.dumps([edu.dict() for edu in cv_data.education]) if cv_data.education else None,
                    json.dumps([skill.dict() for skill in cv_data.skills]) if cv_data.skills else None,
                    json.dumps([lang.dict() for lang in cv_data.languages]) if cv_data.languages else None,
                    json.dumps([cert.dict() for cert in cv_data.certifications]) if cv_data.certifications else None,
                    json.dumps([proj.dict() for proj in cv_data.projects]) if cv_data.projects else None,
                    json.dumps(cv_data.achievements) if cv_data.achievements else None,
                    json.dumps(cv_data.metadata.dict()) if cv_data.metadata else None
                ))
                self.connection.commit()
                logger.info(f"✅ Datos de CV guardados para candidato {cv_data.candidate_id}")
                return True
        except Exception as e:
            logger.error(f"❌ Error guardando datos de CV: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def get_cv_data(self, candidate_id: str) -> Optional[CVData]:
        """Obtener datos extraídos del CV de un candidato"""
        try:
            await self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM cv_extracted_data 
                    WHERE candidate_id = %s 
                    ORDER BY extraction_date DESC 
                    LIMIT 1
                """, (candidate_id,))
                result = cursor.fetchone()
                
                if result:
                    return CVData(
                        id=result['id'],
                        candidate_id=result['candidate_id'],
                        personal_info=result['personal_info'],
                        summary=result['summary'],
                        objective=result['objective'],
                        work_experience=result['work_experience'],
                        education=result['education'],
                        skills=result['skills'],
                        languages=result['languages'],
                        certifications=result['certifications'],
                        projects=result['projects'],
                        achievements=result['achievements'],
                        metadata=result['metadata']
                    )
                return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de CV: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def delete_cv_data(self, candidate_id: str) -> bool:
        """Eliminar datos extraídos del CV de un candidato"""
        try:
            await self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM cv_extracted_data WHERE candidate_id = %s", (candidate_id,))
                self.connection.commit()
                logger.info(f"✅ Datos de CV eliminados para candidato {candidate_id}")
                return True
        except Exception as e:
            logger.error(f"❌ Error eliminando datos de CV: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def get_all_cv_data(self, limit: int = 100, offset: int = 0) -> list[CVData]:
        """Obtener todos los datos de CV con paginación"""
        try:
            await self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM cv_extracted_data 
                    ORDER BY extraction_date DESC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                results = cursor.fetchall()
                
                cv_data_list = []
                for result in results:
                    cv_data_list.append(CVData(
                        id=result['id'],
                        candidate_id=result['candidate_id'],
                        personal_info=result['personal_info'],
                        summary=result['summary'],
                        objective=result['objective'],
                        work_experience=result['work_experience'],
                        education=result['education'],
                        skills=result['skills'],
                        languages=result['languages'],
                        certifications=result['certifications'],
                        projects=result['projects'],
                        achievements=result['achievements'],
                        metadata=result['metadata']
                    ))
                return cv_data_list
        except Exception as e:
            logger.error(f"❌ Error obteniendo todos los datos de CV: {e}")
            return []
        finally:
            await self.disconnect() 