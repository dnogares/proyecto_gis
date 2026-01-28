# Dockerfile para GIS API v2.0
FROM python:3.11-slim

# Instalar dependencias del sistema para GDAL, PostgreSQL y utilidades
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establecer variables de entorno para GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios y asegurar permisos
RUN mkdir -p capas/fgb capas/gpkg capas/shp descargas_catastro temp_catastro && \
    chmod +x start.sh

# Exponer puerto
EXPOSE 8000

# Health check usando curl (más fiable en Docker)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Usar script de inicio
CMD ["./start.sh"]
