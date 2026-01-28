#!/bin/bash
# start.sh - Script de inicio para producción

set -e

echo "🚀 Iniciando GIS API v2.0..."

# Verificar variables de entorno
echo "📋 Verificando configuración..."

if [ -z "$POSTGIS_HOST" ]; then
    echo "⚠️  POSTGIS_HOST no configurado - usando valores por defecto"
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p capas/fgb capas/gpkg capas/shp descargas_catastro temp_catastro

# Verificar instalación de GDAL
echo "🔍 Verificando GDAL..."
if command -v gdalinfo &> /dev/null; then
    echo "✅ GDAL instalado: $(gdalinfo --version)"
else
    echo "❌ GDAL no encontrado"
    exit 1
fi

# Verificar Python y dependencias
echo "🐍 Verificando Python..."
python --version

echo "📦 Verificando dependencias..."
pip list | grep -E "(geopandas|fastapi|uvicorn)"

# Mostrar configuración
echo ""
echo "========================================"
echo "🌍 Configuración del Servidor"
echo "========================================"
echo "Puerto: 80"
echo "Workers: ${WORKERS:-4}"
echo "PostGIS Host: ${POSTGIS_HOST:-localhost}"
echo "Debug: ${DEBUG:-false}"
echo "========================================"
echo ""

# Iniciar servidor
echo "🚀 Iniciando Uvicorn..."

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 80 \
    --workers ${WORKERS:-4} \
    --log-level ${LOG_LEVEL:-info} \
    --no-access-log \
    --proxy-headers \
    --forwarded-allow-ips='*'
