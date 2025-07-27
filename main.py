from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import asyncio
from datetime import datetime
import logging
from typing import Optional, Dict, Any

from services.cv_processor import CVProcessor
from services.database_service import DatabaseService
from models.cv_data import CVData, CVExtractionRequest, CVExtractionResponse
from utils.logger import setup_logger

# Configurar logging
logger = setup_logger()

# Crear aplicación FastAPI
app = FastAPI(
    title="Servicio Decodificador CV - Lumina Talent Group",
    description="Servicio para extraer y procesar información de CVs de candidatos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servicios
cv_processor = CVProcessor()
db_service = DatabaseService()

@app.on_event("startup")
async def startup_event():
    """Evento de inicio del servicio"""
    logger.info("🚀 Iniciando Servicio Decodificador CV...")
    try:
        await db_service.connect()
        logger.info("✅ Conexión a base de datos establecida")
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre del servicio"""
    logger.info("🛑 Cerrando Servicio Decodificador CV...")
    await db_service.disconnect()

@app.get("/")
async def root():
    """Endpoint de salud del servicio"""
    return {
        "message": "Servicio Decodificador CV - Lumina Talent Group",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    try:
        # Verificar conexión a base de datos
        db_status = await db_service.health_check()
        
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/api/cv/extract", response_model=CVExtractionResponse)
async def extract_cv_data(
    request: CVExtractionRequest,
    background_tasks: BackgroundTasks
):
    """
    Extrae información de un CV desde una URL o ruta de archivo
    
    Args:
        request: Datos de la solicitud con información del candidato y archivo
        background_tasks: Tareas en segundo plano
    
    Returns:
        CVExtractionResponse: Respuesta con el estado del procesamiento
    """
    try:
        logger.info(f"📄 Iniciando extracción de CV para candidato: {request.candidate_id}")
        
        # Validar que el archivo existe
        if not os.path.exists(request.file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Archivo no encontrado: {request.file_path}"
            )
        
        # Procesar CV en segundo plano
        background_tasks.add_task(
            process_cv_background,
            request.candidate_id,
            request.file_path,
            request.candidate_data
        )
        
        return CVExtractionResponse(
            success=True,
            message="Procesamiento de CV iniciado correctamente",
            candidate_id=request.candidate_id,
            processing_id=f"cv_{request.candidate_id}_{datetime.now().timestamp()}"
        )
        
    except Exception as e:
        logger.error(f"Error en extracción de CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cv/upload", response_model=CVExtractionResponse)
async def upload_and_extract_cv(
    file: UploadFile = File(...),
    candidate_id: str = None,
    candidate_data: Optional[Dict[str, Any]] = None
):
    """
    Sube un archivo CV y extrae su información
    
    Args:
        file: Archivo CV a procesar
        candidate_id: ID del candidato
        candidate_data: Datos adicionales del candidato
    
    Returns:
        CVExtractionResponse: Respuesta con el estado del procesamiento
    """
    try:
        logger.info(f"📤 Subiendo CV: {file.filename}")
        
        # Validar tipo de archivo
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado. Permitidos: {', '.join(allowed_extensions)}"
            )
        
        # Guardar archivo temporalmente
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, f"cv_{candidate_id}_{datetime.now().timestamp()}{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Procesar CV
        cv_data = await cv_processor.process_file(temp_file_path)
        
        # Guardar en base de datos
        if candidate_id:
            await db_service.save_cv_data(candidate_id, cv_data)
        
        # Limpiar archivo temporal
        os.remove(temp_file_path)
        
        return CVExtractionResponse(
            success=True,
            message="CV procesado y guardado correctamente",
            candidate_id=candidate_id,
            cv_data=cv_data.dict()
        )
        
    except Exception as e:
        logger.error(f"Error procesando CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cv/{candidate_id}")
async def get_cv_data(candidate_id: str):
    """
    Obtiene los datos extraídos del CV de un candidato
    
    Args:
        candidate_id: ID del candidato
    
    Returns:
        CVData: Datos extraídos del CV
    """
    try:
        cv_data = await db_service.get_cv_data(candidate_id)
        
        if not cv_data:
            raise HTTPException(
                status_code=404,
                detail="Datos de CV no encontrados para este candidato"
            )
        
        return cv_data
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/cv/{candidate_id}")
async def delete_cv_data(candidate_id: str):
    """
    Elimina los datos extraídos del CV de un candidato
    
    Args:
        candidate_id: ID del candidato
    
    Returns:
        Dict: Respuesta de confirmación
    """
    try:
        await db_service.delete_cv_data(candidate_id)
        
        return {
            "success": True,
            "message": f"Datos de CV eliminados para candidato {candidate_id}"
        }
        
    except Exception as e:
        logger.error(f"Error eliminando datos de CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_cv_background(candidate_id: str, file_path: str, candidate_data: Dict[str, Any]):
    """
    Procesa un CV en segundo plano
    
    Args:
        candidate_id: ID del candidato
        file_path: Ruta del archivo CV
        candidate_data: Datos del candidato
    """
    try:
        logger.info(f"🔄 Procesando CV en segundo plano para candidato: {candidate_id}")
        
        # Extraer información del CV
        cv_data = await cv_processor.process_file(file_path)
        
        # Enriquecer con datos del candidato si están disponibles
        if candidate_data:
            cv_data.enrich_with_candidate_data(candidate_data)
        
        # Guardar en base de datos
        await db_service.save_cv_data(candidate_id, cv_data)
        
        logger.info(f"✅ CV procesado exitosamente para candidato: {candidate_id}")
        
    except Exception as e:
        logger.error(f"❌ Error procesando CV para candidato {candidate_id}: {e}")
        # Aquí podrías implementar notificaciones o reintentos

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 