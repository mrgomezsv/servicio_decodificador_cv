# 🚀 Guía de Deployment - Servicio Decodificador CV

## 📋 Resumen

Esta guía te ayudará a desplegar el **Servicio Decodificador CV** en tu servidor de producción. El servicio se ejecutará en el subdominio `api.luminatalentgroup.com` y se integrará con el sistema existente.

## 🎯 Arquitectura del Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Python        │
│   Angular       │◄──►│   Node.js       │◄──►│   FastAPI       │
│   (Puerto 80)   │    │   (Puerto 3000) │    │   (Puerto 8001) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Nginx         │
                    │   (Proxy)       │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MySQL         │
                    │   Database      │
                    └─────────────────┘
```

## 🛠️ Prerrequisitos

### Servidor
- **Sistema Operativo**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: Mínimo 2GB (recomendado 4GB+)
- **CPU**: 2 cores mínimo
- **Espacio**: 10GB+ disponible

### Software Requerido
- **Python**: 3.8+ (se instalará automáticamente)
- **Node.js**: 18+ (para PM2)
- **Nginx**: (se instalará automáticamente)
- **MySQL**: 8.0+ (ya configurado)
- **PM2**: (se instalará automáticamente)

### DNS
- **Subdominio**: `api.luminatalentgroup.com` apuntando al servidor
- **Registro A**: `api.luminatalentgroup.com` → IP del servidor

## 📦 Preparación del Servidor

### 1. Clonar el Repositorio

```bash
# Navegar al directorio del servidor
cd /var/www/

# Clonar el repositorio
git clone https://github.com/mrgomezsv/servicio_decodificador_cv.git
cd servicio_decodificador_cv

# Cambiar a la rama de producción
git checkout mrg_production
```

### 2. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con las credenciales correctas
nano .env
```

**Contenido del archivo `.env`:**

```env
# Configuración de Base de Datos
DB_HOST=66.179.82.132
DB_PORT=3306
DB_NAME=consultora_db
DB_USER=mrgomez
DB_PASSWORD=tu_password_aqui

# Configuración del Servicio
SERVICE_PORT=8001
SERVICE_HOST=0.0.0.0

# Configuración de Logs
LOG_LEVEL=INFO
LOG_FILE=logs/cv_decoder.log

# Configuración de CORS
ALLOWED_ORIGINS=https://luminatalentgroup.com,https://api.luminatalentgroup.com

# Configuración de Archivos
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=temp_uploads

# Configuración de Procesamiento
PROCESSING_TIMEOUT=300  # 5 minutos
CONFIDENCE_THRESHOLD=0.6
```

## 🚀 Deployment Automático

### Opción 1: Deployment Completo (Recomendado)

```bash
# Ejecutar el script de deployment
./deploy.sh
```

Este script realizará automáticamente:
- ✅ Instalación de Python y dependencias
- ✅ Configuración del entorno virtual
- ✅ Instalación de dependencias Python
- ✅ Configuración de la base de datos
- ✅ Inicio del servicio con PM2
- ✅ Verificación de health check

### Opción 2: Deployment Manual

Si prefieres hacer el deployment paso a paso:

```bash
# 1. Instalar Python y dependencias
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configurar base de datos
python3 -c "
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

connection = pymysql.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

with connection.cursor() as cursor:
    cursor.execute('''
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    connection.commit()

connection.close()
print('Base de datos configurada correctamente')
"

# 5. Iniciar con PM2
pm2 start ecosystem.config.js
pm2 save
```

## 🌐 Configuración de Nginx y SSL

### 1. Configurar Nginx

```bash
# Ejecutar como root
sudo ./setup-nginx-ssl.sh
```

Este script:
- ✅ Instala Certbot para SSL
- ✅ Configura Nginx para el subdominio
- ✅ Obtiene certificado SSL de Let's Encrypt
- ✅ Configura renovación automática

### 2. Configuración Manual de Nginx (Alternativa)

```bash
# Copiar configuración
sudo cp nginx-config.conf /etc/nginx/sites-available/api.luminatalentgroup.com

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/api.luminatalentgroup.com /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

### 3. Obtener Certificado SSL

```bash
# Obtener certificado SSL
sudo certbot --nginx -d api.luminatalentgroup.com --non-interactive --agree-tos --email admin@luminatalentgroup.com

# Verificar renovación automática
sudo crontab -l | grep certbot
```

## 🔧 Configuración del Backend Node.js

### Actualizar Variables de Entorno

En el archivo `.env` del backend (`Consultora_BackendJS/.env`):

```env
# Agregar esta línea
PYTHON_SERVICE_URL=https://api.luminatalentgroup.com
```

### Verificar Integración

```bash
# Probar la conexión desde el backend
curl -X GET https://api.luminatalentgroup.com/health
```

## 📊 Verificación del Deployment

### 1. Health Check

```bash
# Verificar que el servicio responde
curl https://api.luminatalentgroup.com/health

# Respuesta esperada:
# {"status": "healthy", "service": "CV Decoder", "timestamp": "2024-01-15T10:30:00Z"}
```

### 2. Documentación de la API

```bash
# Acceder a la documentación Swagger
curl https://api.luminatalentgroup.com/docs

# Acceder a la documentación ReDoc
curl https://api.luminatalentgroup.com/redoc
```

### 3. Estado de PM2

```bash
# Ver estado del servicio
pm2 status Servicio_Decodificador_CV

# Ver logs
pm2 logs Servicio_Decodificador_CV
```

### 4. Verificar Base de Datos

```bash
# Conectar a MySQL
mysql -h 66.179.82.132 -u mrgomez -p consultora_db

# Verificar tabla
SHOW TABLES LIKE 'cv_extracted_data';
DESCRIBE cv_extracted_data;
```

## 🔄 Mantenimiento

### Comandos Útiles

```bash
# Reiniciar servicio
pm2 restart Servicio_Decodificador_CV

# Ver logs en tiempo real
pm2 logs Servicio_Decodificador_CV -f

# Monitorear recursos
pm2 monit

# Actualizar código
git pull origin mrg_production
./deploy.sh

# Verificar certificados SSL
sudo certbot certificates

# Renovar certificados manualmente
sudo certbot renew
```

### Logs y Monitoreo

```bash
# Logs del servicio Python
tail -f logs/cv_decoder_$(date +%Y%m%d).log

# Logs de Nginx
sudo tail -f /var/log/nginx/api.luminatalentgroup.com.access.log
sudo tail -f /var/log/nginx/api.luminatalentgroup.com.error.log

# Logs de PM2
pm2 logs Servicio_Decodificador_CV --lines 100
```

### Backup y Restauración

```bash
# Backup de la tabla de CVs
mysqldump -h 66.179.82.132 -u mrgomez -p consultora_db cv_extracted_data > backup_cv_data_$(date +%Y%m%d).sql

# Restaurar backup
mysql -h 66.179.82.132 -u mrgomez -p consultora_db < backup_cv_data_20240115.sql
```

## 🐛 Solución de Problemas

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos

```bash
# Verificar conectividad
mysql -h 66.179.82.132 -u mrgomez -p -e "SELECT 1;"

# Verificar variables de entorno
cat .env | grep DB_
```

#### 2. Error de Permisos

```bash
# Verificar permisos del directorio
ls -la /var/www/api.luminatalentgroup.com/

# Corregir permisos
sudo chown -R www-data:www-data /var/www/api.luminatalentgroup.com/
sudo chmod -R 755 /var/www/api.luminatalentgroup.com/
```

#### 3. Error de SSL

```bash
# Verificar certificado
sudo certbot certificates

# Renovar certificado
sudo certbot renew --force-renewal
```

#### 4. Error de Puerto

```bash
# Verificar puerto en uso
sudo netstat -tlnp | grep :8001

# Matar proceso si es necesario
sudo pkill -f "main.py"
```

### Logs de Debug

```bash
# Habilitar logs detallados
export LOG_LEVEL=DEBUG
pm2 restart Servicio_Decodificador_CV

# Ver logs detallados
pm2 logs Servicio_Decodificador_CV --lines 50
```

## 📈 Métricas y Monitoreo

### Consultas Útiles

```sql
-- CVs procesados por día
SELECT 
    DATE(extraction_date) as fecha,
    COUNT(*) as cvs_procesados
FROM cv_extracted_data 
GROUP BY DATE(extraction_date)
ORDER BY fecha DESC;

-- Promedio de confianza
SELECT 
    AVG(JSON_EXTRACT(metadata, '$.confidence_score')) as confianza_promedio
FROM cv_extracted_data;

-- Errores de procesamiento
SELECT 
    COUNT(*) as total_errores,
    DATE(extraction_date) as fecha
FROM cv_extracted_data 
WHERE JSON_EXTRACT(metadata, '$.confidence_score') < 0.6
GROUP BY DATE(extraction_date);
```

## 🔒 Seguridad

### Configuraciones Recomendadas

1. **Firewall**: Solo puertos 80, 443, 22 abiertos
2. **SSL**: Certificado válido y renovación automática
3. **Logs**: Rotación automática de logs
4. **Backup**: Backup diario de la base de datos
5. **Monitoreo**: Alertas para caídas del servicio

### Comandos de Seguridad

```bash
# Verificar puertos abiertos
sudo netstat -tlnp

# Verificar logs de acceso
sudo tail -f /var/log/nginx/api.luminatalentgroup.com.access.log

# Verificar intentos de acceso fallidos
sudo grep "401\|403\|404" /var/log/nginx/api.luminatalentgroup.com.access.log
```

## 📞 Soporte

### Contacto
- **Desarrollador**: Equipo de Desarrollo Lumina
- **Email**: desarrollo@luminatalentgroup.com
- **Documentación**: [GitHub Repository](https://github.com/mrgomezsv/servicio_decodificador_cv.git)

### Recursos Adicionales
- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de PM2](https://pm2.keymetrics.io/docs/)
- [Documentación de Nginx](https://nginx.org/en/docs/)

---

**¡El Servicio Decodificador CV está listo para producción! 🚀**

Con esta configuración tendrás:
- ✅ Servicio Python funcionando en `api.luminatalentgroup.com`
- ✅ SSL configurado automáticamente
- ✅ Integración completa con el sistema existente
- ✅ Monitoreo y logs configurados
- ✅ Backup y mantenimiento automatizado 