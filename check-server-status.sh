#!/bin/bash

echo "🔍 VERIFICANDO ESTADO ACTUAL DEL SERVIDOR"
echo "=========================================="

# Verificar servicios actuales
echo "📊 Servicios PM2 actuales:"
pm2 list

echo ""
echo "🌐 Servicios Nginx activos:"
sudo nginx -t
sudo systemctl status nginx --no-pager -l

echo ""
echo "🗄️ Base de datos MySQL:"
sudo systemctl status mysql --no-pager -l

echo ""
echo "💾 Espacio en disco:"
df -h

echo ""
echo "🧠 Memoria disponible:"
free -h

echo ""
echo "🌡️ CPU y procesos:"
top -bn1 | head -20

echo ""
echo "📁 Directorios del proyecto:"
ls -la /var/www/
ls -la /home/ubuntu/ 2>/dev/null || echo "No hay directorio /home/ubuntu/"

echo ""
echo "✅ Verificación completada" 