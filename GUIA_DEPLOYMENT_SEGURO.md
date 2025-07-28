# 🚀 Guía de Deployment Seguro - Servicio Python CV

## 📋 **Resumen Ejecutivo**

Esta guía te permitirá desplegar el Servicio Python CV **sin afectar** los servicios existentes en tu servidor. El deployment es completamente independiente y seguro.

## 🎯 **Objetivos**

- ✅ Desplegar servicio Python sin interrumpir servicios existentes
- ✅ Usar puerto independiente (8001)
- ✅ Configurar subdominio separado (api.luminatalentgroup.com)
- ✅ Mantener base de datos existente
- ✅ Crear backups automáticos
- ✅ Verificación de salud del servicio

## 🔧 **Prerrequisitos**

### **En el Servidor:**
- Usuario con permisos sudo
- Git instalado
- Acceso a internet
- Espacio en disco: mínimo 2GB libre

### **Información Necesaria:**
- Credenciales de MySQL (usuario, contraseña, base de datos)
- Acceso al repositorio Git
- Dominio configurado (api.luminatalentgroup.com)

## 📝 **PASO 1: PREPARACIÓN**

### **1.1 Conectarse al servidor**
```bash
ssh usuario@tu-servidor.com
```

### **1.2 Verificar estado actual**
```bash
# Descargar script de verificación
wget https://raw.githubusercontent.com/mrgomezsv/servicio_decodificador_cv/mrg_production/check-server-status.sh
chmod +x check-server-status.sh
./check-server-status.sh
```

### **1.3 Crear directorio de trabajo**
```bash
sudo mkdir -p /var/www/cv-decoder-service
sudo chown $USER:$USER /var/www/cv-decoder-service
```

## 🚀 **PASO 2: DEPLOYMENT AUTOMÁTICO**

### **2.1 Descargar script de deployment**
```bash
cd /var/www/cv-decoder-service
wget https://raw.githubusercontent.com/mrgomezsv/servicio_decodificador_cv/mrg_production/deploy-seguro.sh
chmod +x deploy-seguro.sh
```

### **2.2 Ejecutar deployment**
```bash
./deploy-seguro.sh
```

**El script hará automáticamente:**
- ✅ Verificar servicios existentes
- ✅ Crear backup del directorio (si existe)
- ✅ Instalar Python 3 (si no está instalado)
- ✅ Clonar/actualizar repositorio
- ✅ Configurar entorno virtual
- ✅ Instalar dependencias Python
- ✅ Configurar variables de entorno
- ✅ Verificar conexión a base de datos
- ✅ Configurar PM2
- ✅ Configurar Nginx
- ✅ Verificar SSL
- ✅ Health check del servicio

## ⚙️ **PASO 3: CONFIGURACIÓN MANUAL**

### **3.1 Configurar variables de entorno**
El script te pedirá editar el archivo `.env`:

```bash
nano /var/www/cv-decoder-service/.env
```

**Variables importantes:**
```env
# Base de datos (usar la misma que el backend)
DB_HOST=localhost
DB_PORT=5432
DB_USER=mrgomez  # o el usuario que uses
DB_PASSWORD=Karin2100  # tu contraseña
DB_NAME=consultora_db

# Servicio
SERVICE_PORT=8001
SERVICE_HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/cv-decoder.log

# CORS
CORS_ORIGINS=*

# Límites de archivo
MAX_FILE_SIZE=10485760  # 10MB
```

### **3.2 Configurar SSL (si no está automático)**
```bash
# Opción 1: Automático
sudo bash /var/www/cv-decoder-service/setup-nginx-ssl.sh

# Opción 2: Manual
sudo certbot --nginx -d api.luminatalentgroup.com
```

## 🔍 **PASO 4: VERIFICACIÓN**

### **4.1 Verificar servicios**
```bash
# Verificar PM2
pm2 list
pm2 logs cv-decoder-service

# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Verificar puerto
netstat -tuln | grep 8001
```

### **4.2 Health check**
```bash
# Local
curl http://localhost:8001/health

# Con SSL
curl https://api.luminatalentgroup.com/health
```

### **4.3 Verificar API docs**
```bash
# Abrir en navegador
https://api.luminatalentgroup.com/docs
```

## 🔗 **PASO 5: INTEGRACIÓN CON BACKEND**

### **5.1 Actualizar backend Node.js**
Editar el archivo `.env` del backend:

```bash
nano /var/www/Consultora_BackendJS/.env
```

**Agregar:**
```env
PYTHON_SERVICE_URL=https://api.luminatalentgroup.com
```

### **5.2 Reiniciar backend**
```bash
cd /var/www/Consultora_BackendJS
pm2 restart all
```

## 🧪 **PASO 6: PRUEBAS**

### **6.1 Probar endpoints**
```bash
# Health check
curl https://api.luminatalentgroup.com/health

# API docs
curl https://api.luminatalentgroup.com/docs

# Probar con un CV
curl -X POST https://api.luminatalentgroup.com/api/cv/upload \
  -F "file=@test-cv.pdf" \
  -F "candidate_id=123"
```

### **6.2 Probar desde frontend**
1. Ir a la sección de candidatos
2. Seleccionar un candidato con CV
3. Hacer clic en "Procesar CV"
4. Verificar que se extraen los datos
5. Generar PDF del CV

## 📊 **PASO 7: MONITOREO**

### **7.1 Comandos de monitoreo**
```bash
# Ver logs en tiempo real
pm2 logs cv-decoder-service --lines 100

# Ver estado de servicios
pm2 status
sudo systemctl status nginx

# Ver uso de recursos
htop
df -h
free -h
```

### **7.2 Logs importantes**
```bash
# Logs del servicio Python
tail -f /var/www/cv-decoder-service/logs/cv-decoder.log

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs de PM2
pm2 logs cv-decoder-service
```

## 🔧 **MANTENIMIENTO**

### **Actualizar servicio**
```bash
cd /var/www/cv-decoder-service
git pull origin mrg_production
pm2 restart cv-decoder-service
```

### **Reiniciar servicios**
```bash
# Reiniciar solo Python
pm2 restart cv-decoder-service

# Reiniciar Nginx
sudo systemctl restart nginx

# Reiniciar todo
pm2 restart all
sudo systemctl restart nginx
```

### **Backup manual**
```bash
sudo cp -r /var/www/cv-decoder-service /var/backups/cv-decoder-service/backup-manual-$(date +%Y%m%d-%H%M%S)
```

## 🚨 **TROUBLESHOOTING**

### **Problema: Puerto 8001 en uso**
```bash
# Ver qué usa el puerto
sudo lsof -i :8001

# Matar proceso si es necesario
sudo kill -9 PID
```

### **Problema: Error de base de datos**
```bash
# Verificar conexión
psql -U mrgomez -d consultora_db -h localhost

# Verificar tabla
\dt cv_extracted_data

# Verificar conexión desde Python
python3 -c "import psycopg2; conn = psycopg2.connect('postgresql://mrgomez:Karin2100@localhost:5432/consultora_db'); print('OK')"
```

### **Problema: SSL no funciona**
```bash
# Verificar certificado
sudo certbot certificates

# Renovar certificado
sudo certbot renew

# Verificar configuración Nginx
sudo nginx -t
```

### **Problema: Servicio no inicia**
```bash
# Ver logs detallados
pm2 logs cv-decoder-service --lines 200

# Verificar entorno virtual
cd /var/www/cv-decoder-service
source venv/bin/activate
python main.py
```

## 📞 **SOPORTE**

### **Información útil para debugging:**
```bash
# Información del sistema
uname -a
python3 --version
nginx -v
pm2 --version

# Estado de servicios
systemctl list-units --type=service --state=running | grep -E "(nginx|postgresql|pm2)"

# Logs del sistema
sudo journalctl -u nginx -f
sudo journalctl -u postgresql -f
```

### **Contacto:**
- Documentación: `/var/www/cv-decoder-service/DEPLOYMENT_GUIDE.md`
- Logs: `/var/www/cv-decoder-service/logs/`
- Configuración: `/var/www/cv-decoder-service/.env`

## ✅ **CHECKLIST FINAL**

- [ ] Servicio Python desplegado en puerto 8001
- [ ] Nginx configurado para api.luminatalentgroup.com
- [ ] SSL configurado y funcionando
- [ ] Base de datos PostgreSQL conectada y tabla creada
- [ ] PM2 ejecutando el servicio
- [ ] Health check responde correctamente
- [ ] Backend Node.js actualizado con PYTHON_SERVICE_URL
- [ ] Frontend puede procesar CVs
- [ ] PDFs se generan correctamente
- [ ] Logs funcionando
- [ ] Backup creado

## 🎉 **¡DEPLOYMENT COMPLETADO!**

Tu servicio Python CV está ahora desplegado y funcionando de forma independiente, sin afectar los servicios existentes.

**URLs importantes:**
- 🌐 Servicio: https://api.luminatalentgroup.com
- 📚 API Docs: https://api.luminatalentgroup.com/docs
- 🏥 Health: https://api.luminatalentgroup.com/health