#!/bin/bash

# Script de Rollback para Servicio Python CV
# Revierte todos los cambios si algo sale mal

set -e

echo "🔄 ROLLBACK - SERVICIO PYTHON CV"
echo "================================"

# Variables
PYTHON_SERVICE_NAME="cv-decoder-service"
PROJECT_DIR="/var/www/cv-decoder-service"
BACKUP_DIR="/var/backups/cv-decoder-service"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Función para detener servicios
stop_services() {
    log "🛑 Deteniendo servicios..."
    
    # Detener proceso PM2
    if pm2 list | grep "$PYTHON_SERVICE_NAME" > /dev/null; then
        log "Deteniendo proceso PM2..."
        pm2 stop "$PYTHON_SERVICE_NAME" 2>/dev/null || true
        pm2 delete "$PYTHON_SERVICE_NAME" 2>/dev/null || true
        pm2 save
    fi
    
    # Matar procesos Python en el puerto 8001
    if netstat -tuln | grep ":8001 " > /dev/null; then
        log "Matando procesos en puerto 8001..."
        sudo lsof -ti:8001 | xargs sudo kill -9 2>/dev/null || true
    fi
}

# Función para remover configuración Nginx
remove_nginx_config() {
    log "🗑️ Removiendo configuración Nginx..."
    
    # Remover enlace simbólico
    if [ -L "/etc/nginx/sites-enabled/api.luminatalentgroup.com" ]; then
        sudo rm -f "/etc/nginx/sites-enabled/api.luminatalentgroup.com"
        log "Enlace simbólico removido"
    fi
    
    # Remover archivo de configuración
    if [ -f "/etc/nginx/sites-available/api.luminatalentgroup.com" ]; then
        sudo rm -f "/etc/nginx/sites-available/api.luminatalentgroup.com"
        log "Archivo de configuración removido"
    fi
    
    # Recargar Nginx
    if sudo nginx -t; then
        sudo systemctl reload nginx
        log "Nginx recargado"
    fi
}

# Función para remover directorio del proyecto
remove_project_directory() {
    log "🗑️ Removiendo directorio del proyecto..."
    
    if [ -d "$PROJECT_DIR" ]; then
        # Crear backup antes de eliminar
        if [ -d "$BACKUP_DIR" ]; then
            sudo cp -r "$PROJECT_DIR" "$BACKUP_DIR/rollback-$(date +%Y%m%d-%H%M%S)"
            log "Backup creado antes de eliminar"
        fi
        
        sudo rm -rf "$PROJECT_DIR"
        log "Directorio del proyecto eliminado"
    fi
}

# Función para restaurar desde backup
restore_from_backup() {
    log "📦 Buscando backups disponibles..."
    
    if [ -d "$BACKUP_DIR" ]; then
        # Listar backups disponibles
        echo "Backups disponibles:"
        ls -la "$BACKUP_DIR" | grep "backup\|rollback"
        
        echo ""
        read -p "¿Quieres restaurar desde un backup? (y/n): " restore_choice
        
        if [ "$restore_choice" = "y" ] || [ "$restore_choice" = "Y" ]; then
            echo "Backups disponibles:"
            ls -la "$BACKUP_DIR" | grep "backup\|rollback" | awk '{print $9}'
            
            read -p "Ingresa el nombre del backup a restaurar: " backup_name
            
            if [ -d "$BACKUP_DIR/$backup_name" ]; then
                log "Restaurando desde backup: $backup_name"
                sudo cp -r "$BACKUP_DIR/$backup_name" "$PROJECT_DIR"
                sudo chown -R $USER:$USER "$PROJECT_DIR"
                log "Backup restaurado"
            else
                error "Backup no encontrado: $backup_name"
            fi
        fi
    fi
}

# Función para limpiar logs
cleanup_logs() {
    log "🧹 Limpiando logs..."
    
    # Limpiar logs de PM2
    pm2 flush 2>/dev/null || true
    
    # Limpiar logs del sistema relacionados
    sudo journalctl --vacuum-time=1d 2>/dev/null || true
}

# Función para verificar estado final
check_final_status() {
    log "🔍 Verificando estado final..."
    
    # Verificar que no hay procesos Python corriendo
    if pgrep -f "cv-decoder-service" > /dev/null; then
        warn "Aún hay procesos Python corriendo"
        pgrep -f "cv-decoder-service"
    else
        log "✅ No hay procesos Python corriendo"
    fi
    
    # Verificar que el puerto 8001 está libre
    if netstat -tuln | grep ":8001 " > /dev/null; then
        warn "Puerto 8001 aún está en uso"
        netstat -tuln | grep ":8001"
    else
        log "✅ Puerto 8001 está libre"
    fi
    
    # Verificar que Nginx funciona
    if sudo nginx -t; then
        log "✅ Nginx funciona correctamente"
    else
        error "❌ Nginx tiene errores de configuración"
    fi
    
    # Verificar servicios existentes
    echo ""
    echo "📊 Estado de servicios existentes:"
    pm2 list
    echo ""
    sudo systemctl status nginx --no-pager -l
}

# Función principal
main() {
    echo "⚠️ ADVERTENCIA: Este script eliminará completamente el servicio Python CV"
    echo "Los servicios existentes (backend, frontend) NO se verán afectados"
    echo ""
    read -p "¿Estás seguro de que quieres hacer rollback? (y/n): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Rollback cancelado"
        exit 0
    fi
    
    log "Iniciando rollback..."
    
    # 1. Detener servicios
    stop_services
    
    # 2. Remover configuración Nginx
    remove_nginx_config
    
    # 3. Remover directorio del proyecto
    remove_project_directory
    
    # 4. Limpiar logs
    cleanup_logs
    
    # 5. Verificar estado final
    check_final_status
    
    echo ""
    echo "🔄 ROLLBACK COMPLETADO"
    echo "======================"
    echo ""
    echo "✅ Servicios Python detenidos"
    echo "✅ Configuración Nginx removida"
    echo "✅ Directorio del proyecto eliminado"
    echo "✅ Logs limpiados"
    echo ""
    echo "📋 Servicios que siguen funcionando:"
    echo "- Backend Node.js"
    echo "- Frontend Angular"
    echo "- Base de datos MySQL"
    echo "- Nginx (sin configuración Python)"
    echo ""
    echo "🔧 Para restaurar desde backup, ejecuta:"
    echo "sudo bash $0 --restore"
    echo ""
    echo "🎉 Rollback completado exitosamente!"
}

# Función para restaurar
restore() {
    log "Iniciando restauración desde backup..."
    restore_from_backup
}

# Verificar argumentos
if [ "$1" = "--restore" ]; then
    restore
else
    main
fi 