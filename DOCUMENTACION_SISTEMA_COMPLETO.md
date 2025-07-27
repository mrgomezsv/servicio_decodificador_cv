# Sistema Completo de Decodificación de CVs - Lumina Talent Group

## Resumen del Sistema

Se ha implementado un sistema completo de decodificación y procesamiento automático de CVs que incluye:

- ✅ **Servicio Python con FastAPI** para procesamiento de CVs
- ✅ **Integración con Backend Node.js** existente
- ✅ **Componente Frontend Angular** para visualización
- ✅ **Base de datos MySQL** para almacenamiento estructurado
- ✅ **API REST completa** con documentación automática
- ✅ **Procesamiento asíncrono** en segundo plano
- ✅ **Interfaz moderna** para visualización de datos extraídos

## Arquitectura del Sistema

### Diagrama de Flujo

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend        │    │   Servicio      │
│   Angular       │    │   Node.js        │    │   Python        │
│                 │    │                  │    │   FastAPI       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │ 1. Usuario hace clic  │                       │
         │    en "Procesar CV"   │                       │
         │                       │                       │
         │──────────────────────▶│                       │
         │                       │                       │
         │                       │ 2. Busca candidato    │
         │                       │    y ruta del CV      │
         │                       │                       │
         │                       │ 3. Envía a servicio   │
         │                       │    Python             │
         │                       │──────────────────────▶│
         │                       │                       │
         │                       │                       │ 4. Procesa CV
         │                       │                       │    (PDF/DOC/DOCX)
         │                       │                       │
         │                       │                       │ 5. Extrae datos
         │                       │                       │    estructurados
         │                       │                       │
         │                       │                       │ 6. Guarda en DB
         │                       │                       │
         │                       │ 7. Respuesta exitosa  │
         │                       │◀──────────────────────│
         │                       │                       │
         │ 8. Muestra estado     │                       │
         │◀──────────────────────│                       │
         │                       │                       │
         │ 9. Usuario hace clic  │                       │
         │    en "Ver Datos"     │                       │
         │                       │                       │
         │──────────────────────▶│                       │
         │                       │                       │
         │                       │ 10. Obtiene datos     │
         │                       │    del servicio       │
         │                       │──────────────────────▶│
         │                       │                       │
         │                       │                       │ 11. Consulta DB
         │                       │                       │
         │                       │                       │ 12. Retorna datos
         │                       │                       │
         │                       │ 13. Datos estructurados
         │                       │◀──────────────────────│
         │                       │                       │
         │ 14. Muestra datos     │                       │
         │    extraídos          │                       │
         │◀──────────────────────│                       │
```

## Componentes del Sistema

### 1. Servicio Python (FastAPI)

**Ubicación**: `Servicio_Decodificador_CV/`

#### Características:
- **Framework**: FastAPI con Python 3.8+
- **Puerto**: 8001 (configurable)
- **Procesamiento**: Asíncrono en segundo plano
- **Formatos soportados**: PDF, DOC, DOCX, TXT
- **Base de datos**: MySQL con tabla `cv_extracted_data`

#### Estructura del Proyecto:
```
Servicio_Decodificador_CV/
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias Python
├── env.example            # Variables de entorno
├── start.sh               # Script de inicio
├── ecosystem.config.js    # Configuración PM2
├── test_service.py        # Script de pruebas
├── README.md              # Documentación
├── services/              # Servicios de la aplicación
│   ├── cv_processor.py    # Procesamiento de CVs
│   └── database_service.py # Servicio de base de datos
├── models/                # Modelos de datos
│   └── cv_data.py         # Modelos Pydantic
├── utils/                 # Utilidades
│   └── logger.py          # Configuración de logging
├── logs/                  # Archivos de log
└── temp_uploads/          # Archivos temporales
```

#### Endpoints Disponibles:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Salud del servicio |
| `GET` | `/health` | Verificación de salud |
| `POST` | `/api/cv/extract` | Extraer datos de CV desde ruta |
| `POST` | `/api/cv/upload` | Subir y procesar CV |
| `GET` | `/api/cv/{candidate_id}` | Obtener datos extraídos |
| `DELETE` | `/api/cv/{candidate_id}` | Eliminar datos |

#### Información Extraída:

**Datos Personales:**
- Nombre completo
- Email, teléfono, dirección
- LinkedIn, portfolio, website

**Experiencia Laboral:**
- Empresa, posición, fechas
- Descripción, logros, tecnologías
- Nivel de experiencia

**Educación:**
- Institución, grado, campo de estudio
- Fechas, GPA, nivel educativo

**Habilidades:**
- Habilidades técnicas y blandas
- Nivel de dominio, años de experiencia
- Categorización automática

**Idiomas:**
- Idioma, nivel, certificaciones

**Certificaciones:**
- Nombre, emisor, fechas
- ID de credencial

**Proyectos:**
- Nombre, descripción, tecnologías
- Rol, fechas, URL

**Logros:**
- Reconocimientos y logros

### 2. Integración Backend Node.js

**Archivos modificados:**
- `src/controllers/candidate.controller.ts`
- `src/routes/candidate.routes.ts`

#### Nuevos Endpoints:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/candidates/:id/process-cv` | Procesar CV con servicio Python |
| `GET` | `/api/candidates/:id/cv-data` | Obtener datos extraídos del CV |

#### Funciones Agregadas:

```typescript
// Procesar CV con servicio Python
export const processCVWithPython = async (req: Request, res: Response, next: NextFunction)

// Obtener datos extraídos del CV
export const getExtractedCVData = async (req: Request, res: Response, next: NextFunction)
```

### 3. Componente Frontend Angular

**Archivos creados:**
- `src/app/services/cv-data.service.ts`
- `src/app/components/cv-data-viewer/`

#### Servicio CVDataService:

```typescript
// Interfaces para tipos de datos
export interface CVData { ... }
export interface CVPersonalInfo { ... }
export interface CVWorkExperience { ... }
// ... más interfaces

// Métodos del servicio
processCandidateCV(candidateId: string): Observable<CVProcessingResponse>
getCandidateCVData(candidateId: string): Observable<CVData>
hasProcessedCVData(candidateId: string): Observable<boolean>
```

#### Componente CVDataViewer:

**Características:**
- Visualización completa de datos extraídos
- Estados de carga, error y sin datos
- Botón para procesar CV
- Botón para generar PDF (en desarrollo)
- Diseño responsive y moderno

**Funcionalidades:**
- Carga automática de datos al inicializar
- Procesamiento de CV con feedback visual
- Formateo de fechas y niveles
- Categorización de habilidades
- Cálculo de años de experiencia

### 4. Base de Datos

#### Tabla `cv_extracted_data`:

```sql
CREATE TABLE cv_extracted_data (
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
```

#### Estructura de Datos JSON:

```json
{
  "personal_info": {
    "full_name": "Juan Carlos Pérez González",
    "email": "juan.perez@email.com",
    "phone": "+52 55 1234 5678",
    "linkedin": "linkedin.com/in/juanperez"
  },
  "work_experience": [
    {
      "company": "TechCorp",
      "position": "Desarrollador Full Stack",
      "start_date": "2020-01-01",
      "current": true,
      "description": "Desarrollo de aplicaciones web...",
      "achievements": ["Logro 1", "Logro 2"],
      "technologies": ["React", "Node.js", "MySQL"]
    }
  ],
  "skills": [
    {
      "name": "JavaScript",
      "category": "programming",
      "level": "advanced",
      "years_experience": 5
    }
  ],
  "metadata": {
    "file_path": "/uploads/cv.pdf",
    "confidence_score": 0.85,
    "total_years_experience": 5,
    "primary_skills": ["JavaScript", "React", "Node.js"]
  }
}
```

## Instalación y Configuración

### 1. Servicio Python

```bash
# Navegar al directorio del servicio
cd Servicio_Decodificador_CV

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp env.example .env
# Editar .env con tus configuraciones

# Ejecutar servicio
./start.sh
```

### 2. Configuración de Base de Datos

```bash
# Crear tabla en MySQL
mysql -u root -p lumina_consultora

# La tabla se crea automáticamente al iniciar el servicio
```

### 3. Variables de Entorno

**Backend Node.js** (`Consultora_BackendJS/.env`):
```env
# Agregar esta variable
PYTHON_SERVICE_URL=http://localhost:8001
```

**Servicio Python** (`Servicio_Decodificador_CV/.env`):
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=lumina_consultora
SERVICE_PORT=8001
```

### 4. Integración Frontend

El componente `CVDataViewer` se puede usar en cualquier parte del frontend:

```html
<app-cv-data-viewer 
  [candidateId]="candidate.id"
  [candidateName]="candidate.firstName + ' ' + candidate.lastName">
</app-cv-data-viewer>
```

## Uso del Sistema

### Flujo de Trabajo Típico:

1. **Candidato sube CV** → Se almacena en el sistema
2. **Administrador hace clic en "Procesar CV"** → Se envía al servicio Python
3. **Servicio Python procesa el CV** → Extrae información estructurada
4. **Datos se almacenan en DB** → Tabla `cv_extracted_data`
5. **Administrador hace clic en "Ver Datos"** → Se muestran los datos extraídos
6. **Administrador puede generar PDF** → (Funcionalidad en desarrollo)

### Ejemplo de Uso:

```typescript
// En un componente Angular
export class CandidateDetailComponent {
  candidateId = 'uuid-del-candidato';
  
  // El componente CVDataViewer maneja todo automáticamente
}
```

```html
<!-- En el template -->
<app-cv-data-viewer 
  [candidateId]="candidateId"
  [candidateName]="candidateName">
</app-cv-data-viewer>
```

## Características Avanzadas

### 1. Procesamiento Inteligente

- **Extracción de texto** de múltiples formatos
- **Análisis de patrones** para identificar secciones
- **Procesamiento de fechas** con normalización
- **Categorización automática** de habilidades
- **Cálculo de experiencia** total

### 2. Manejo de Errores

- **Validación de archivos** antes del procesamiento
- **Logging detallado** para debugging
- **Estados de error** en la interfaz
- **Reintentos automáticos** en caso de fallo

### 3. Rendimiento

- **Procesamiento asíncrono** en segundo plano
- **Límites de tamaño** de archivo (10MB)
- **Limpieza automática** de archivos temporales
- **Caché de datos** para consultas frecuentes

### 4. Seguridad

- **Validación de tipos** de archivo
- **Sanitización de rutas** de archivos
- **Límites de tamaño** para prevenir ataques
- **Configuración CORS** apropiada

## Monitoreo y Logs

### Logs del Servicio Python:

- **Archivo**: `logs/cv_decoder_YYYYMMDD.log`
- **Consola**: Salida estándar
- **Nivel**: INFO por defecto

### Métricas Importantes:

- Tiempo de procesamiento por archivo
- Tasa de éxito de extracción
- Errores por tipo de archivo
- Uso de memoria y CPU

### Health Check:

```bash
# Verificar salud del servicio
curl http://localhost:8001/health

# Respuesta esperada:
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "database": "lumina_consultora",
    "host": "localhost"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

## Pruebas

### Script de Pruebas Automáticas:

```bash
# Ejecutar pruebas
cd Servicio_Decodificador_CV
python3 test_service.py
```

### Pruebas Manuales:

1. **Health Check**: `GET http://localhost:8001/health`
2. **Documentación**: `http://localhost:8001/docs`
3. **Procesar CV**: Usar el endpoint `/api/cv/extract`
4. **Obtener Datos**: Usar el endpoint `/api/cv/{candidate_id}`

## Producción

### Configuración de Producción:

1. **Variables de entorno**:
```env
DB_HOST=tu-servidor-db
DB_PASSWORD=password-seguro
ALLOWED_ORIGINS=https://tu-dominio.com
```

2. **Servidor WSGI**:
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

3. **PM2** (recomendado):
```bash
pm2 start ecosystem.config.js --env production
```

4. **Proxy reverso** (Nginx):
```nginx
location /api/cv/ {
    proxy_pass http://localhost:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Escalabilidad:

- **Múltiples instancias** del servicio Python
- **Load balancer** para distribución de carga
- **Base de datos** con replicación
- **Caché Redis** para datos frecuentes

## Mantenimiento

### Tareas de Mantenimiento:

1. **Limpieza de logs**:
```bash
# Limpiar logs antiguos (más de 30 días)
find logs/ -name "*.log" -mtime +30 -delete
```

2. **Limpieza de archivos temporales**:
```bash
# Limpiar archivos temporales
rm -rf temp_uploads/*
```

3. **Backup de base de datos**:
```sql
-- Backup de la tabla de datos extraídos
mysqldump -u root -p lumina_consultora cv_extracted_data > backup_cv_data.sql
```

### Actualizaciones:

1. **Dependencias Python**:
```bash
pip install -r requirements.txt --upgrade
```

2. **Modelos de spaCy**:
```bash
python -m spacy download es_core_news_sm --upgrade
python -m spacy download en_core_web_sm --upgrade
```

## Troubleshooting

### Problemas Comunes:

1. **Error de conexión a base de datos**:
   - Verificar credenciales en `.env`
   - Asegurar que MySQL esté ejecutándose
   - Verificar permisos de usuario

2. **Error procesando archivos**:
   - Verificar que las dependencias estén instaladas
   - Revisar permisos de archivos
   - Verificar espacio en disco

3. **Memoria insuficiente**:
   - Reducir tamaño máximo de archivos
   - Implementar procesamiento por chunks
   - Aumentar memoria del servidor

4. **Error de CORS**:
   - Configurar `ALLOWED_ORIGINS` correctamente
   - Verificar configuración del proxy reverso

### Logs de Debug:

```env
# Habilitar logs detallados
LOG_LEVEL=DEBUG
```

## Roadmap Futuro

### Funcionalidades Planificadas:

1. **Generación de PDF** de datos extraídos
2. **Análisis de sentimientos** en descripciones
3. **Comparación automática** entre candidatos
4. **Integración con ATS** externos
5. **Machine Learning** para mejor extracción
6. **API para terceros** con autenticación
7. **Dashboard de métricas** de procesamiento
8. **Notificaciones** de procesamiento completado

### Mejoras Técnicas:

1. **Microservicios** para diferentes tipos de procesamiento
2. **Queue system** (Redis/RabbitMQ) para mejor escalabilidad
3. **Docker containers** para despliegue simplificado
4. **Kubernetes** para orquestación
5. **Monitoreo con Prometheus/Grafana**
6. **Tests unitarios y de integración** completos

## Conclusión

El sistema de decodificación de CVs proporciona una solución completa y escalable para automatizar la extracción de información de CVs. Con su arquitectura modular, procesamiento asíncrono y interfaz moderna, mejora significativamente la eficiencia del proceso de reclutamiento en Lumina Talent Group.

La integración perfecta con el sistema existente y la capacidad de extensión hacen de esta solución una base sólida para futuras mejoras y funcionalidades avanzadas. 