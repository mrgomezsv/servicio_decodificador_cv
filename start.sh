#!/bin/bash

# Script de inicio para el Servicio Decodificador CV
# Lumina Talent Group

echo "🚀 Iniciando Servicio Decodificador CV..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    exit 1
fi

# Verificar si el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias si no están instaladas
if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
    echo "📥 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Crear directorios necesarios
echo "📁 Creando directorios necesarios..."
mkdir -p logs
mkdir -p temp_uploads

# Verificar archivo de configuración
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado. Copiando desde env.example..."
    cp env.example .env
    echo "📝 Por favor, edita el archivo .env con tus configuraciones antes de continuar."
    echo "   Especialmente las credenciales de la base de datos."
    exit 1
fi

# Cargar variables de entorno
echo "⚙️  Cargando configuración..."
export $(cat .env | xargs)

# Verificar conexión a base de datos
echo "🔍 Verificando conexión a base de datos..."
python3 -c "
import pymysql
import os
try:
    connection = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'lumina_consultora')
    )
    connection.close()
    print('✅ Conexión a base de datos exitosa')
except Exception as e:
    print(f'❌ Error conectando a la base de datos: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ No se pudo conectar a la base de datos. Verifica tu configuración en .env"
    exit 1
fi

# Iniciar el servicio
echo "🌟 Iniciando servicio en puerto ${SERVICE_PORT:-8001}..."
echo "📖 Documentación disponible en: http://localhost:${SERVICE_PORT:-8001}/docs"
echo "🔍 Health check en: http://localhost:${SERVICE_PORT:-8001}/health"
echo ""
echo "Presiona Ctrl+C para detener el servicio"
echo ""

# Ejecutar el servicio
python3 main.py 