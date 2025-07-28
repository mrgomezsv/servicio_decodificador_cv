#!/bin/bash

# Script de Deployment Seguro para Servicio Python CV
# Usa la ubicación actual del directorio

set -e  # Salir si hay algún error

echo "🚀 DEPLOYMENT SEGURO - SERVICIO PYTHON CV (UBICACIÓN ACTUAL)"
echo "============================================================="

# Variables de configuración
PYTHON_SERVICE_NAME="cv-decoder-service"
PYTHON_SERVICE_PORT="8001"
PROJECT_DIR="$(pwd)"  # Usar directorio actual
BACKUP_DIR="/var/backups/cv-decoder-service"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para crear backup
create_backup() {
    log "📦 Creando backup del directorio actual..."
    sudo mkdir -p "$BACKUP_DIR"
    sudo cp -r "$PROJECT_DIR" "$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S)"
    log "✅ Backup creado en $BACKUP_DIR"
}

# Función para verificar servicios existentes
check_existing_services() {
    log "🔍 Verificando servicios existentes..."
    
    # Verificar si el puerto ya está en uso
    if netstat -tuln | grep ":$PYTHON_SERVICE_PORT " > /dev/null; then
        warn "Puerto $PYTHON_SERVICE_PORT ya está en uso"
        netstat -tuln | grep ":$PYTHON_SERVICE_PORT"
    fi
    
    # Verificar si ya existe el proceso PM2
    if pm2 list | grep "$PYTHON_SERVICE_NAME" > /dev/null; then
        warn "Proceso PM2 '$PYTHON_SERVICE_NAME' ya existe"
        pm2 list | grep "$PYTHON_SERVICE_NAME"
    fi
    
    # Verificar configuración Nginx
    if [ -f "/etc/nginx/sites-available/api.luminatalentgroup.com" ]; then
        warn "Configuración Nginx para api.luminatalentgroup.com ya existe"
    fi
}

# Función para instalar Python si no existe
install_python() {
    if ! command_exists python3; then
        log "🐍 Instalando Python 3..."
        
        # Detectar sistema operativo
        if [ -f /etc/debian_version ]; then
            # Debian/Ubuntu
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv build-essential
        elif [ -f /etc/redhat-release ]; then
            # CentOS/RHEL
            sudo yum update -y
            sudo yum install -y python3 python3-pip python3-devel gcc
        else
            error "Sistema operativo no soportado"
        fi
        
        log "✅ Python 3 instalado"
    else
        log "✅ Python 3 ya está instalado: $(python3 --version)"
    fi
}

# Función para configurar entorno virtual
setup_virtual_env() {
    log "🔧 Configurando entorno virtual..."
    
    if [ ! -d "venv" ]; then
        log "Creando entorno virtual..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar dependencias
    log "📦 Instalando dependencias Python..."
    pip install -r requirements.txt
    
    log "✅ Entorno virtual configurado"
}

# Función para configurar variables de entorno
setup_environment() {
    log "⚙️ Configurando variables de entorno..."
    
    if [ ! -f ".env" ]; then
        log "Creando archivo .env desde ejemplo..."
        cp env.example .env
        
        # Solicitar configuración al usuario
        echo ""
        echo "🔧 CONFIGURACIÓN DE VARIABLES DE ENTORNO"
        echo "========================================"
        echo "Por favor, edita el archivo .env con los valores correctos:"
        echo "nano $PROJECT_DIR/.env"
        echo ""
        echo "Variables importantes a configurar:"
        echo "- DB_HOST: localhost"
        echo "- DB_USER: mrgomez"
        echo "- DB_PASSWORD: Karin2100"
        echo "- DB_NAME: consultora_db"
        echo "- SERVICE_PORT: $PYTHON_SERVICE_PORT"
        echo ""
        read -p "Presiona Enter cuando hayas configurado el archivo .env..."
    else
        log "✅ Archivo .env ya existe"
    fi
}

# Función para crear directorios necesarios
create_directories() {
    log "📁 Creando directorios necesarios..."
    
    # Crear directorios
    mkdir -p logs
    mkdir -p temp_uploads
    
    # Configurar permisos
    chmod 755 logs
    chmod 755 temp_uploads
    
    log "✅ Directorios creados"
}

# Función para verificar base de datos
check_database() {
    log "🗄️ Verificando conexión a base de datos..."
    
    source venv/bin/activate
    
    # Cargar variables de entorno
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Verificar conexión
    python3 -c "
import psycopg2
import os
try:
    connection = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    print('✅ Conexión a base de datos PostgreSQL exitosa')
    connection.close()
except Exception as e:
    print(f'❌ Error de conexión: {e}')
    exit(1)
"
    
    if [ $? -ne 0 ]; then
        error "No se pudo conectar a la base de datos PostgreSQL"
    fi
}

# Función para configurar PM2
setup_pm2() {
    log "⚡ Configurando PM2..."
    
    # Detener proceso existente si existe
    if pm2 list | grep "$PYTHON_SERVICE_NAME" > /dev/null; then
        log "Deteniendo proceso PM2 existente..."
        pm2 stop "$PYTHON_SERVICE_NAME"
        pm2 delete "$PYTHON_SERVICE_NAME"
    fi
    
    # Iniciar nuevo proceso
    pm2 start ecosystem.config.js
    
    # Guardar configuración PM2
    pm2 save
    
    log "✅ PM2 configurado"
}

# Función para configurar Nginx
setup_nginx() {
    log "🌐 Configurando Nginx..."
    
    # Copiar configuración
    sudo cp "$PROJECT_DIR/nginx-config.conf" "/etc/nginx/sites-available/api.luminatalentgroup.com"
    
    # Crear enlace simbólico si no existe
    if [ ! -L "/etc/nginx/sites-enabled/api.luminatalentgroup.com" ]; then
        sudo ln -s "/etc/nginx/sites-available/api.luminatalentgroup.com" "/etc/nginx/sites-enabled/"
    fi
    
    # Verificar configuración
    if sudo nginx -t; then
        sudo systemctl reload nginx
        log "✅ Nginx configurado y recargado"
    else
        error "Error en la configuración de Nginx"
    fi
}

# Función para verificar SSL
check_ssl() {
    log "🔒 Verificando certificado SSL..."
    
    if [ ! -f "/etc/letsencrypt/live/api.luminatalentgroup.com/fullchain.pem" ]; then
        warn "Certificado SSL no encontrado para api.luminatalentgroup.com"
        echo ""
        echo "🔧 Para obtener el certificado SSL, ejecuta:"
        echo "sudo certbot --nginx -d api.luminatalentgroup.com"
        echo ""
        echo "O usa el script automático:"
        echo "sudo bash $PROJECT_DIR/setup-nginx-ssl.sh"
        echo ""
    else
        log "✅ Certificado SSL encontrado"
    fi
}

# Función para health check
health_check() {
    log "🏥 Realizando health check..."
    
    # Esperar un momento para que el servicio se inicie
    sleep 5
    
    # Verificar proceso PM2
    if pm2 list | grep "$PYTHON_SERVICE_NAME" | grep "online" > /dev/null; then
        log "✅ Proceso PM2 está online"
    else
        error "❌ Proceso PM2 no está online"
    fi
    
    # Verificar puerto
    if netstat -tuln | grep ":$PYTHON_SERVICE_PORT " > /dev/null; then
        log "✅ Puerto $PYTHON_SERVICE_PORT está activo"
    else
        error "❌ Puerto $PYTHON_SERVICE_PORT no está activo"
    fi
    
    # Verificar endpoint de health
    if command_exists curl; then
        if curl -f http://localhost:$PYTHON_SERVICE_PORT/health > /dev/null 2>&1; then
            log "✅ Health check endpoint responde correctamente"
        else
            warn "⚠️ Health check endpoint no responde (puede ser normal si SSL está configurado)"
        fi
    fi
}

# Función para mostrar información final
show_final_info() {
    echo ""
    echo "🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE"
    echo "====================================="
    echo ""
    echo "📊 INFORMACIÓN DEL SERVICIO:"
    echo "- Nombre: $PYTHON_SERVICE_NAME"
    echo "- Puerto: $PYTHON_SERVICE_PORT"
    echo "- Directorio: $PROJECT_DIR"
    echo "- URL: https://api.luminatalentgroup.com"
    echo ""
    echo "🔧 COMANDOS ÚTILES:"
    echo "- Ver logs: pm2 logs $PYTHON_SERVICE_NAME"
    echo "- Reiniciar: pm2 restart $PYTHON_SERVICE_NAME"
    echo "- Estado: pm2 status"
    echo "- Nginx status: sudo systemctl status nginx"
    echo ""
    echo "📚 DOCUMENTACIÓN:"
    echo "- Guía completa: $PROJECT_DIR/DEPLOYMENT_GUIDE.md"
    echo "- API docs: https://api.luminatalentgroup.com/docs"
    echo ""
    echo "⚠️ PRÓXIMOS PASOS:"
    echo "1. Configurar SSL si no está configurado"
    echo "2. Actualizar PYTHON_SERVICE_URL en el backend Node.js"
    echo "3. Probar la integración completa"
    echo ""
}

# Función principal
main() {
    log "Iniciando deployment seguro desde ubicación actual..."
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "main.py" ]; then
        error "No se encontró main.py. Asegúrate de estar en el directorio del servicio Python."
    fi
    
    # Verificar servicios existentes
    check_existing_services
    
    # Crear backup
    create_backup
    
    # Instalar Python
    install_python
    
    # Configurar entorno virtual
    setup_virtual_env
    
    # Configurar variables de entorno
    setup_environment
    
    # Crear directorios
    create_directories
    
    # Verificar base de datos
    check_database
    
    # Configurar PM2
    setup_pm2
    
    # Configurar Nginx
    setup_nginx
    
    # Verificar SSL
    check_ssl
    
    # Health check
    health_check
    
    # Mostrar información final
    show_final_info
    
    log "🎉 Deployment completado exitosamente!"
}

# Ejecutar función principal
main "$@" 