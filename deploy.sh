#!/bin/bash

# 🚀 SCRIPT DE DEPLOYMENT SEGURO - SERVICIO DECODIFICADOR CV
# Este script garantiza un deployment limpio del servicio Python

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# Configuración
SERVICE_NAME="Servicio_Decodificador_CV"
SERVICE_PORT="8001"
DOMAIN="api.luminatalentgroup.com"
PROJECT_DIR="/var/www/$DOMAIN"
BACKUP_DIR="/var/backups/python-service"
LOG_FILE="/var/log/deploy-python-cv.log"

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    error "No se encontró main.py o requirements.txt. Ejecuta desde el directorio del servicio Python."
    exit 1
fi

log "🔍 FASE 0: Verificación de sistema y dependencias"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    warning "Python3 no está instalado. Instalando..."
    
    # Detectar el sistema operativo
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        log "Instalando Python3 en sistema Debian/Ubuntu..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        log "Instalando Python3 en sistema CentOS/RHEL..."
        sudo yum update -y
        sudo yum install -y python3 python3-pip python3-devel gcc
    else
        error "Sistema operativo no soportado para instalación automática de Python"
        error "Instala Python 3.8+ manualmente y ejecuta este script nuevamente"
        exit 1
    fi
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
log "Python versión detectada: $PYTHON_VERSION"

# Verificar si PM2 está instalado
if ! command -v pm2 &> /dev/null; then
    warning "PM2 no está instalado. Instalando..."
    sudo npm install -g pm2
fi

# Verificar si Nginx está instalado
if ! command -v nginx &> /dev/null; then
    warning "Nginx no está instalado. Instalando..."
    if [ -f /etc/debian_version ]; then
        sudo apt install -y nginx
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y nginx
    fi
fi

success "Verificación de dependencias completada"

log "📄 FASE 1: Configuración de variables de entorno"

# Cargar variables de entorno si existe el archivo .env
if [ -f ".env" ]; then
    log "📄 Cargando configuración desde .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    log "⚠️  Archivo .env no encontrado, creando desde env.example"
    if [ -f "env.example" ]; then
        cp env.example .env
        warning "Archivo .env creado desde env.example. Edítalo con tus credenciales antes de continuar."
        error "Por favor, edita el archivo .env con las credenciales correctas y ejecuta este script nuevamente."
        exit 1
    else
        error "No se encontró env.example. Crea manualmente el archivo .env con las credenciales de la base de datos."
        exit 1
    fi
fi

# Verificar variables críticas
if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    error "Variables de entorno críticas no configuradas en .env"
    error "Asegúrate de configurar: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD"
    exit 1
fi

log "📋 Configuración de base de datos:"
log "  • Host: $DB_HOST"
log "  • Base de datos: $DB_NAME"
log "  • Usuario: $DB_USER"
log "  • Puerto: ${DB_PORT:-3306}"

# Verificar conectividad con la base de datos
log "🔍 Verificando conectividad con la base de datos..."
if command -v mysql &> /dev/null; then
    if mysql -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" 2>/dev/null; then
        success "✅ Conexión a la base de datos verificada"
    else
        error "❌ No se puede conectar a la base de datos"
        exit 1
    fi
else
    warning "MySQL client no instalado, saltando verificación de conexión"
fi

log "🧹 FASE 2: Limpieza del sistema PM2"

# Parar y limpiar procesos PM2 del servicio Python
log "Deteniendo procesos PM2 del servicio Python..."
pm2 stop "$SERVICE_NAME" 2>/dev/null || warning "No había procesos PM2 del servicio Python corriendo"
pm2 delete "$SERVICE_NAME" 2>/dev/null || warning "No había procesos PM2 del servicio Python para eliminar"

# Matar cualquier proceso Python huérfano relacionado
log "Eliminando procesos Python huérfanos..."
pkill -f "main.py" 2>/dev/null || warning "No había procesos main.py"
pkill -f "uvicorn" 2>/dev/null || warning "No había procesos uvicorn"

# Verificar que no hay procesos corriendo
log "Verificando que no hay procesos Python corriendo..."
if pgrep -f "main.py\|uvicorn" > /dev/null; then
    error "Aún hay procesos Python corriendo. Abortando deployment."
    exit 1
fi

success "Limpieza completa terminada"

log "📦 FASE 3: Actualización del código"

# Actualizar código desde Git
log "Obteniendo últimos cambios desde mrg_production..."
git pull origin mrg_production --no-edit

# Crear directorio de logs si no existe
log "Creando directorio de logs..."
mkdir -p logs

# Crear directorio de uploads temporales si no existe
log "Creando directorio de uploads temporales..."
mkdir -p temp_uploads

success "Actualización del código completada"

log "🐍 FASE 4: Configuración del entorno virtual Python"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    log "Creando entorno virtual Python..."
    python3 -m venv venv
    success "Entorno virtual creado"
else
    log "Entorno virtual ya existe"
fi

# Activar entorno virtual
log "Activando entorno virtual..."
source venv/bin/activate

# Verificar que estamos en el entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    error "No se pudo activar el entorno virtual"
    exit 1
fi

log "Entorno virtual activado: $VIRTUAL_ENV"

# Actualizar pip
log "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
log "Instalando dependencias Python..."
pip install -r requirements.txt

# Verificar instalación de dependencias críticas
log "Verificando instalación de dependencias críticas..."
python3 -c "import fastapi, uvicorn, pymysql, spacy" 2>/dev/null || {
    error "Error: No se pudieron importar dependencias críticas"
    log "Reintentando instalación..."
    pip install --force-reinstall -r requirements.txt
}

success "Configuración del entorno virtual completada"

log "🗄️ FASE 5: Configuración de la base de datos"

# Crear tabla cv_extracted_data si no existe
log "Verificando tabla cv_extracted_data..."
python3 -c "
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

try:
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
        print('Tabla cv_extracted_data verificada/creada correctamente')
    
    connection.close()
except Exception as e:
    print(f'Error configurando base de datos: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    error "Error configurando la base de datos"
    exit 1
fi

success "Configuración de base de datos completada"

log "🚀 FASE 6: Inicio del servicio"

# Verificar que el archivo ecosystem existe
if [ ! -f "ecosystem.config.js" ]; then
    error "No se encontró ecosystem.config.js"
    exit 1
fi

# Iniciar con PM2
log "Iniciando servicio con PM2..."
pm2 start ecosystem.config.js

# Esperar un momento para que se estabilice
log "Esperando estabilización del servicio..."
sleep 5

# Verificar estado
log "Verificando estado del servicio..."
pm2 status "$SERVICE_NAME"

# Verificar health check
log "Realizando health check..."
if curl -f -s "http://localhost:$SERVICE_PORT/health" > /dev/null; then
    success "✅ Health check OK"
else
    error "❌ Health check falló"
    pm2 logs "$SERVICE_NAME" --lines 20
    exit 1
fi

# Guardar configuración PM2
log "Guardando configuración PM2..."
pm2 save

success "🎉 ¡DEPLOYMENT COMPLETADO EXITOSAMENTE!"

log "📊 Estado final:"
pm2 status "$SERVICE_NAME"

log "🔗 URLs disponibles:"
log "  • Local: http://localhost:$SERVICE_PORT/health"
log "  • API Docs: http://localhost:$SERVICE_PORT/docs"
log "  • Producción: https://$DOMAIN/health"

log "📋 Comandos útiles:"
log "  • Ver logs: pm2 logs $SERVICE_NAME"
log "  • Reiniciar: pm2 restart $SERVICE_NAME"
log "  • Detener: pm2 stop $SERVICE_NAME"
log "  • Estado: pm2 status $SERVICE_NAME"
log "  • Monitoreo: pm2 monit"

log "🔧 Configuración de Nginx:"
log "  • Asegúrate de configurar Nginx para el subdominio $DOMAIN"
log "  • Proxy pass a http://localhost:$SERVICE_PORT"
log "  • Configurar SSL para https://$DOMAIN"

log "⚠️  IMPORTANTE:"
log "  • Servicio Python desplegado en puerto $SERVICE_PORT"
log "  • Entorno virtual configurado en ./venv"
log "  • Base de datos configurada y verificada"
log "  • PM2 gestionando el proceso"
log "  • Logs disponibles en ./logs/"

exit 0 