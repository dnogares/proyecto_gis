#!/bin/bash
# ============================================================================
# SCRIPT DE INICIALIZACIÓN - GIS API v2.0
# Crea base de datos PostGIS desde cero
# ============================================================================
#
# USO:
#   bash scripts/init_db.sh
#
# O si necesitas especificar credenciales:
#   bash scripts/init_db.sh -h localhost -p 5432 -u postgres
#
# ============================================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Valores por defecto
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGPASSWORD="${PGPASSWORD:-}"
DB_USER="manuel"
DB_NAME="GIS"

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            PGHOST="$2"
            shift 2
            ;;
        -p|--port)
            PGPORT="$2"
            shift 2
            ;;
        -u|--user)
            PGUSER="$2"
            shift 2
            ;;
        -pw|--password)
            PGPASSWORD="$2"
            shift 2
            ;;
        *)
            echo "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}GIS API v2.0 - Database Init${NC}"
echo -e "${BLUE}=================================${NC}\n"

echo -e "${YELLOW}Configuración:${NC}"
echo "  Host: $PGHOST"
echo "  Puerto: $PGPORT"
echo "  Usuario: $PGUSER"
echo "  Base de datos: $DB_NAME"
echo "  Owner: $DB_USER"
echo ""

# Verificar conexión a PostgreSQL
echo -e "${YELLOW}1. Verificando conexión a PostgreSQL...${NC}"
if PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Conexión exitosa${NC}\n"
else
    echo -e "${RED}✗ No se pudo conectar a PostgreSQL${NC}"
    echo "  Verifica:"
    echo "    - PostgreSQL está ejecutándose en $PGHOST:$PGPORT"
    echo "    - Credenciales de usuario: $PGUSER"
    echo "    - Variable PGPASSWORD está configurada si se requiere contraseña"
    exit 1
fi

# Verificar PostGIS
echo -e "${YELLOW}2. Verificando disponibilidad de PostGIS...${NC}"
if PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostGIS disponible${NC}\n"
else
    echo -e "${RED}✗ PostGIS no está instalado${NC}"
    echo "  Instala PostGIS:"
    echo "    Ubuntu/Debian: sudo apt-get install postgresql-postgis"
    echo "    macOS: brew install postgis"
    exit 1
fi

# Verificar si el usuario manuel existe
echo -e "${YELLOW}3. Verificando usuario $DB_USER...${NC}"
if PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -c "SELECT 1 FROM pg_user WHERE usename='$DB_USER'" | grep -q 1; then
    echo -e "${GREEN}✓ Usuario $DB_USER existe${NC}\n"
else
    echo -e "${YELLOW}→ Creando usuario $DB_USER...${NC}"
    # Crear usuario (sin contraseña requerida en trust mode, o con contraseña configurada)
    PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -c \
        "CREATE USER $DB_USER WITH CREATEDB CREATEROLE;" 2>/dev/null || true
    echo -e "${GREEN}✓ Usuario $DB_USER creado/verificado${NC}\n"
fi

# Eliminar base de datos existente si la opción está habilitada
if [ "${RESET_DB:-false}" = "true" ]; then
    echo -e "${YELLOW}4. Eliminando base de datos existente $DB_NAME...${NC}"
    PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres \
        -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
    echo -e "${GREEN}✓ Base de datos eliminada${NC}\n"
else
    echo -e "${YELLOW}4. Saltando eliminación de BD existente (usa RESET_DB=true para forzar)${NC}\n"
fi

# Ejecutar script SQL de inicialización
echo -e "${YELLOW}5. Ejecutando script de inicialización SQL...${NC}"

if [ ! -f "scripts/init_db.sql" ]; then
    echo -e "${RED}✗ Archivo scripts/init_db.sql no encontrado${NC}"
    echo "  Asegúrate de ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Crear archivo temporal con credenciales
TEMP_SQL="/tmp/gis_init_$$.sql"
cat scripts/init_db.sql > "$TEMP_SQL"

# Ejecutar SQL como superusuario
PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -f "$TEMP_SQL"

# Limpiar archivo temporal
rm -f "$TEMP_SQL"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Script SQL ejecutado correctamente${NC}\n"
else
    echo -e "${RED}✗ Error ejecutando script SQL${NC}"
    exit 1
fi

# Verificar resultado
echo -e "${YELLOW}6. Verificando resultado...${NC}"
PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DB_NAME" << EOF
SELECT 
    'Database' as componente,
    current_database() as valor
UNION ALL
SELECT 
    'PostGIS Version',
    postgis_version()
UNION ALL
SELECT 
    'Tables',
    COUNT(*)::text
FROM information_schema.tables
WHERE table_schema = 'capas';
EOF

echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}✓ INICIALIZACIÓN COMPLETADA${NC}"
echo -e "${GREEN}=================================${NC}\n"

echo -e "${BLUE}Próximos pasos:${NC}"
echo "  1. Configura las variables de entorno en .env:"
echo "     POSTGIS_HOST=$PGHOST"
echo "     POSTGIS_PORT=$PGPORT"
echo "     POSTGIS_DATABASE=$DB_NAME"
echo "     POSTGIS_USER=$DB_USER"
echo "     POSTGIS_PASSWORD=<contraseña>"
echo ""
echo "  2. Carga datos desde FlatGeobuf/GeoPackage:"
echo "     python scripts/export_postgis_to_fgb.py"
echo ""
echo "  3. Inicia la API:"
echo "     python main.py"
echo ""

