# Servicio Decodificador CV - Lumina Talent Group

## Descripción

Servicio en Python con FastAPI para extraer y procesar información de CVs de candidatos. Este servicio se integra con el sistema principal de Lumina Talent Group para automatizar la extracción de datos de CVs y almacenarlos en una base de datos estructurada.

## Características

- ✅ **Extracción de texto** de archivos PDF, DOC, DOCX y TXT
- ✅ **Procesamiento inteligente** de información estructurada
- ✅ **API REST** completa con FastAPI
- ✅ **Almacenamiento en base de datos** MySQL
- ✅ **Procesamiento asíncrono** en segundo plano
- ✅ **Logging completo** y monitoreo
- ✅ **Validación de datos** con Pydantic
- ✅ **CORS configurado** para integración con frontend

## Información Extraída

### Datos Personales
- Nombre completo
- Email
- Teléfono
- Dirección
- LinkedIn
- Portfolio/Website

### Experiencia Laboral
- Empresa
- Posición
- Fechas de inicio y fin
- Descripción
- Logros
- Tecnologías utilizadas

### Educación
- Institución
- Grado/Diploma
- Campo de estudio
- Fechas
- GPA (si disponible)

### Habilidades y Competencias
- Habilidades técnicas
- Habilidades blandas
- Nivel de experiencia
- Categorización automática

### Idiomas
- Idioma
- Nivel de dominio
- Certificaciones

### Certificaciones
- Nombre de la certificación
- Emisor
- Fechas de emisión y expiración
- ID de credencial

### Proyectos
- Nombre del proyecto
- Descripción
- Tecnologías utilizadas
- Rol desempeñado
- URL del proyecto

## Instalación

### Prerrequisitos

- Python 3.8+
- MySQL 5.7+
- pip

### Instalación de Dependencias

```bash
# Clonar el repositorio
cd Servicio_Decodificador_CV

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar modelos de spaCy (opcional, para mejor procesamiento)
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm
```

### Configuración

1. Copiar el archivo de configuración:
```bash
cp env.example .env
```

2. Editar `.env` con tus configuraciones:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=lumina_consultora
```

## Uso

### Ejecutar el Servicio

```bash
# Ejecutar en modo desarrollo
python main.py

# O con uvicorn directamente
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Endpoints Disponibles

#### 1. Salud del Servicio
```http
GET /
GET /health
```

#### 2. Extraer CV desde Ruta de Archivo
```http
POST /api/cv/extract
Content-Type: application/json

{
  "candidate_id": "uuid-del-candidato",
  "file_path": "/ruta/al/archivo/cv.pdf",
  "candidate_data": {
    "firstName": "Juan",
    "lastName": "Pérez",
    "email": "juan@example.com"
  }
}
```

#### 3. Subir y Procesar CV
```http
POST /api/cv/upload
Content-Type: multipart/form-data

file: [archivo CV]
candidate_id: uuid-del-candidato
candidate_data: {"firstName": "Juan", "lastName": "Pérez"}
```

#### 4. Obtener Datos Extraídos
```http
GET /api/cv/{candidate_id}
```

#### 5. Eliminar Datos
```http
DELETE /api/cv/{candidate_id}
```

### Documentación de la API

Una vez ejecutado el servicio, puedes acceder a la documentación automática en:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Integración con el Sistema Principal

### Flujo de Integración

1. **Frontend** envía datos del candidato al **Backend Node.js**
2. **Backend Node.js** almacena el CV y llama al **Servicio Python**
3. **Servicio Python** procesa el CV y extrae información estructurada
4. **Servicio Python** almacena los datos en la tabla `cv_extracted_data`
5. **Backend Node.js** obtiene los datos procesados y los presenta en el frontend

### Nuevo Endpoint en Backend Node.js

Agregar al controlador de candidatos:

```typescript
// En candidate.controller.ts

/**
 * Procesar CV con servicio Python
 */
export const processCVWithPython = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    
    const candidate = await prisma.candidate.findUnique({
      where: { id }
    });

    if (!candidate || !candidate.cvPath) {
      return res.status(404).json({
        status: 'error',
        message: 'Candidato o CV no encontrado'
      });
    }

    // Llamar al servicio Python
    const pythonServiceUrl = process.env.PYTHON_SERVICE_URL || 'http://localhost:8001';
    const response = await fetch(`${pythonServiceUrl}/api/cv/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        candidate_id: id,
        file_path: path.resolve(candidate.cvPath),
        candidate_data: {
          firstName: candidate.firstName,
          lastName: candidate.lastName,
          email: candidate.email,
          phone: candidate.phone,
          address: candidate.address,
          city: candidate.city,
          state: candidate.state,
          linkedIn: candidate.linkedIn,
          portfolio: candidate.portfolio
        }
      })
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || 'Error procesando CV');
    }

    res.status(200).json({
      status: 'success',
      message: 'CV enviado para procesamiento',
      data: result
    });

  } catch (error) {
    logger.error('Error procesando CV con Python:', error);
    next(error);
  }
};

/**
 * Obtener datos extraídos del CV
 */
export const getExtractedCVData = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    
    const pythonServiceUrl = process.env.PYTHON_SERVICE_URL || 'http://localhost:8001';
    const response = await fetch(`${pythonServiceUrl}/api/cv/${id}`);

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({
          status: 'error',
          message: 'Datos de CV no encontrados'
        });
      }
      throw new Error('Error obteniendo datos de CV');
    }

    const cvData = await response.json();

    res.status(200).json({
      status: 'success',
      data: cvData
    });

  } catch (error) {
    logger.error('Error obteniendo datos de CV:', error);
    next(error);
  }
};
```

### Nuevas Rutas en Backend Node.js

```typescript
// En candidate.routes.ts

/**
 * @route POST /api/candidates/:id/process-cv
 * @desc Procesar CV con servicio Python
 */
router.post('/:id/process-cv', processCVWithPython);

/**
 * @route GET /api/candidates/:id/cv-data
 * @desc Obtener datos extraídos del CV
 */
router.get('/:id/cv-data', getExtractedCVData);
```

## Estructura de Base de Datos

### Tabla `cv_extracted_data`

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

## Desarrollo

### Estructura del Proyecto

```
Servicio_Decodificador_CV/
├── main.py                 # Aplicación principal FastAPI
├── requirements.txt        # Dependencias de Python
├── env.example            # Variables de entorno de ejemplo
├── README.md              # Documentación
├── services/              # Servicios de la aplicación
│   ├── __init__.py
│   ├── cv_processor.py    # Procesamiento de CVs
│   └── database_service.py # Servicio de base de datos
├── models/                # Modelos de datos
│   ├── __init__.py
│   └── cv_data.py         # Modelos Pydantic
├── utils/                 # Utilidades
│   ├── __init__.py
│   └── logger.py          # Configuración de logging
├── logs/                  # Archivos de log
└── temp_uploads/          # Archivos temporales
```

### Agregar Nuevos Procesadores

Para agregar soporte para nuevos tipos de archivo:

1. Agregar método en `CVProcessor`:
```python
def _extract_text_from_new_format(self, file_path: str) -> str:
    # Implementar extracción de texto
    pass
```

2. Actualizar `process_file()` para incluir el nuevo formato

### Mejorar Extracción de Datos

Para mejorar la extracción de información específica:

1. Modificar métodos de extracción en `CVProcessor`
2. Agregar nuevos patrones regex
3. Implementar procesamiento con NLP más avanzado

## Monitoreo y Logs

### Logs Disponibles

- **Archivo**: `logs/cv_decoder_YYYYMMDD.log`
- **Consola**: Salida estándar
- **Nivel**: INFO por defecto

### Métricas Importantes

- Tiempo de procesamiento por archivo
- Tasa de éxito de extracción
- Errores por tipo de archivo
- Uso de memoria y CPU

## Producción

### Configuración de Producción

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

3. **Proxy reverso** (Nginx):
```nginx
location /api/cv/ {
    proxy_pass http://localhost:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Seguridad

- Validar tipos de archivo
- Limitar tamaño de archivos
- Sanitizar rutas de archivos
- Implementar autenticación si es necesario
- Configurar CORS apropiadamente

## Troubleshooting

### Problemas Comunes

1. **Error de conexión a base de datos**:
   - Verificar credenciales en `.env`
   - Asegurar que MySQL esté ejecutándose

2. **Error procesando archivos**:
   - Verificar que las dependencias estén instaladas
   - Revisar permisos de archivos

3. **Memoria insuficiente**:
   - Reducir tamaño máximo de archivos
   - Implementar procesamiento por chunks

### Logs de Debug

Para habilitar logs detallados:
```env
LOG_LEVEL=DEBUG
```

## Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto es parte de Lumina Talent Group y está bajo licencia privada. 