#!/bin/bash

# Script de inicio para producción con Gunicorn
# GIS Platform v3.0 - Solo Gunicorn

echo "🚀 Iniciando GIS Platform con Gunicorn..."
echo "========================================="

# Configuración
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-80}
export WORKERS=${WORKERS:-4}
export LOG_LEVEL=${LOG_LEVEL:-info}

# Variables de entorno para producción
export DEBUG=false

echo "📋 Configuración:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Log Level: $LOG_LEVEL"
echo ""

# Crear directorios necesarios
mkdir -p descargas_catastro
mkdir -p static/informes
mkdir -p logs

echo "🔧 Iniciando Gunicorn..."

# Ejecutar Gunicorn con configuración optimizada
gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w $WORKERS \
    -b $HOST:$PORT \
    --timeout 120 \
    --graceful-timeout 30 \
    --log-level $LOG_LEVEL \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    main:app

echo "✅ Servidor detenido"
