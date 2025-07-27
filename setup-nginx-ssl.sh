#!/bin/bash

# 🔧 SCRIPT DE CONFIGURACIÓN DE NGINX Y SSL
# Para el subdominio api.luminatalentgroup.com

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

# Configuración
DOMAIN="api.luminatalentgroup.com"
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"

log "🔧 CONFIGURACIÓN DE NGINX Y SSL PARA $DOMAIN"

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    error "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

log "📋 FASE 1: Verificación de dependencias"

# Verificar si Nginx está instalado
if ! command -v nginx &> /dev/null; then
    error "Nginx no está instalado. Instálalo primero."
    exit 1
fi

# Verificar si Certbot está instalado
if ! command -v certbot &> /dev/null; then
    warning "Certbot no está instalado. Instalando..."
    if [ -f /etc/debian_version ]; then
        apt update
        apt install -y certbot python3-certbot-nginx
    elif [ -f /etc/redhat-release ]; then
        yum install -y certbot python3-certbot-nginx
    else
        error "Sistema operativo no soportado para instalación automática de Certbot"
        exit 1
    fi
fi

success "Dependencias verificadas"

log "📄 FASE 2: Configuración de Nginx"

# Crear directorio para el sitio
mkdir -p /var/www/$DOMAIN

# Copiar configuración de Nginx
if [ -f "nginx-config.conf" ]; then
    log "Copiando configuración de Nginx..."
    cp nginx-config.conf "$NGINX_CONFIG"
else
    error "No se encontró nginx-config.conf"
    exit 1
fi

# Habilitar el sitio
log "Habilitando sitio en Nginx..."
ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"

# Verificar configuración de Nginx
log "Verificando configuración de Nginx..."
if nginx -t; then
    success "Configuración de Nginx válida"
else
    error "Error en la configuración de Nginx"
    exit 1
fi

# Recargar Nginx
log "Recargando Nginx..."
systemctl reload nginx

success "Configuración de Nginx completada"

log "🔒 FASE 3: Configuración de SSL con Let's Encrypt"

# Verificar si el dominio resuelve correctamente
log "Verificando resolución del dominio..."
if ! nslookup $DOMAIN > /dev/null 2>&1; then
    warning "⚠️  El dominio $DOMAIN no resuelve correctamente"
    warning "Asegúrate de que el DNS esté configurado antes de continuar"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Obtener certificado SSL
log "Obteniendo certificado SSL para $DOMAIN..."
if certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@luminatalentgroup.com; then
    success "Certificado SSL obtenido exitosamente"
else
    error "Error obteniendo certificado SSL"
    log "Intentando obtener certificado sin configuración automática de Nginx..."
    if certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email admin@luminatalentgroup.com; then
        success "Certificado SSL obtenido manualmente"
    else
        error "No se pudo obtener el certificado SSL"
        exit 1
    fi
fi

# Verificar que el certificado se obtuvo correctamente
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    success "Certificado SSL verificado"
else
    error "Certificado SSL no encontrado"
    exit 1
fi

log "🔄 FASE 4: Configuración final"

# Recargar Nginx con la nueva configuración SSL
log "Recargando Nginx con configuración SSL..."
systemctl reload nginx

# Verificar que el sitio responde
log "Verificando que el sitio responde..."
sleep 5
if curl -f -s -I "https://$DOMAIN/health" | grep -q "200 OK"; then
    success "✅ Sitio HTTPS funcionando correctamente"
else
    warning "⚠️  El sitio HTTPS no responde correctamente"
    log "Verificando logs de Nginx..."
    tail -n 10 /var/log/nginx/error.log
fi

# Configurar renovación automática de certificados
log "Configurando renovación automática de certificados..."
if [ ! -f "/etc/cron.d/certbot-renew" ]; then
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | tee /etc/cron.d/certbot-renew
fi

success "🎉 CONFIGURACIÓN COMPLETADA EXITOSAMENTE!"

log "📊 Resumen de la configuración:"
log "  • Dominio: $DOMAIN"
log "  • Configuración Nginx: $NGINX_CONFIG"
log "  • Certificado SSL: /etc/letsencrypt/live/$DOMAIN/"
log "  • Logs: /var/log/nginx/$DOMAIN.*.log"

log "🔗 URLs disponibles:"
log "  • HTTPS: https://$DOMAIN"
log "  • Health Check: https://$DOMAIN/health"
log "  • API Docs: https://$DOMAIN/docs"

log "📋 Comandos útiles:"
log "  • Ver estado de Nginx: systemctl status nginx"
log "  • Ver logs de Nginx: tail -f /var/log/nginx/$DOMAIN.error.log"
log "  • Renovar certificado: certbot renew"
log "  • Ver certificados: certbot certificates"

log "⚠️  IMPORTANTE:"
log "  • El certificado SSL se renovará automáticamente"
log "  • Asegúrate de que el servicio Python esté corriendo en el puerto 8001"
log "  • Verifica que el firewall permita tráfico en puertos 80 y 443"

exit 0 