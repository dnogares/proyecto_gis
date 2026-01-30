-- ============================================================================
-- SCRIPT DE INICIALIZACIÓN - GIS API v2.0
-- Base de datos PostGIS con esquemas e índices GIST
-- ============================================================================
-- Crear base de datos GIS
-- Ejecutar como superusuario PostgreSQL
--
-- Uso (desde terminal):
--   psql -U postgres -h localhost -f scripts/init_db.sql
--
-- O desde psql interactivo:
--   \i scripts/init_db.sql
--
-- ============================================================================

-- ============================================================================
-- 1. CREAR BASE DE DATOS
-- ============================================================================
-- CREATE DATABASE GIS 
-- WITH 
--    OWNER = manuel
--    ENCODING = 'UTF8'
--    LOCALE = 'es_ES.UTF-8'
--    TEMPLATE = template0;

-- ============================================================================
-- 2. CONECTAR A LA BASE DE DATOS GIS
-- ============================================================================
-- Nota: En psql, usar: \c GIS
-- En scripts SQL batch, continuar en el mismo script

-- ============================================================================
-- 3. CREAR EXTENSIÓN POSTGIS (asegura que está habilitada)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Para búsquedas de texto full-text

-- Verificar versión
SELECT postgis_full_version();

-- ============================================================================
-- 4. CREAR ESQUEMA PARA CAPAS GEOESPACIALES
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS capas AUTHORIZATION manuel;
COMMENT ON SCHEMA capas IS 'Esquema para capas geoespaciales (Red Natura, Inundables, etc.)';

-- ============================================================================
-- 5. CREAR TABLAS PRINCIPALES
-- ============================================================================

-- -------  Red Natura 2000  -------
CREATE TABLE IF NOT EXISTS capas.rednatura (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(100),  -- LIC, ZEC, ZEPA, etc.
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    superficie_ha NUMERIC(10, 2),
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.rednatura IS 'Red Natura 2000 - Espacios protegidos LIC/ZEC/ZEPA';
COMMENT ON COLUMN capas.rednatura.geom IS 'Geometría MultiPolygon en EPSG:4326';

-- ------- Zonas Inundables -------
CREATE TABLE IF NOT EXISTS capas.zonasinundables (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    peligrosidad VARCHAR(50),  -- Alta, Media, Baja
    periodo_retorno INT,  -- 10, 100, 500 años
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.zonasinundables IS 'Mapa de Peligrosidad por Inundación - SNCZI';
COMMENT ON COLUMN capas.zonasinundables.geom IS 'Geometría en EPSG:4326';

-- ------- Espacios Naturales Protegidos -------
CREATE TABLE IF NOT EXISTS capas.espaciosnaturales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(100),  -- Parque Natural, Reserva, Monumento, etc.
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    superficie_ha NUMERIC(10, 2),
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.espaciosnaturales IS 'Espacios naturales protegidos a nivel estatal/autonómico';

-- ------- Vías Pecuarias -------
CREATE TABLE IF NOT EXISTS capas.viaspocuarias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(50),  -- Vereda, Cordel, Cañada
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    longitud_km NUMERIC(10, 2),
    geom GEOMETRY(MultiLineString, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.viaspocuarias IS 'Vías pecuarias públicas';

-- ------- Masas de Agua -------
CREATE TABLE IF NOT EXISTS capas.masasagua (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(100),  -- Río, Embalse, Lago, etc.
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    superficie_ha NUMERIC(10, 2),
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.masasagua IS 'Cursos de agua y cauces';

-- ------- SEVESO (Industrias peligrosas) -------
CREATE TABLE IF NOT EXISTS capas.seveso (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(50),  -- SEVESO II, SEVESO III
    categoria VARCHAR(50),  -- Alto riesgo, Riesgo, etc.
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    distancia_restriccion_m INT,
    geom GEOMETRY(Point, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.seveso IS 'Establecimientos SEVESO - industrias peligrosas';

-- ------- Dominio Público Hidráulico (DPH) -------
CREATE TABLE IF NOT EXISTS capas.dph (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(100),  -- Cauce, Ribera, Servidumbre, etc.
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    ancho_servidumbre_m INT DEFAULT 100,
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.dph IS 'Dominio Público Hidráulico - Cauces y servidumbres';

-- ------- Riesgo de Incendios -------
CREATE TABLE IF NOT EXISTS capas.riesgoincendios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo_riesgo VARCHAR(50),  -- Bajo, Medio, Alto, Muy Alto
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    indice_riesgo NUMERIC(5, 2),
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.riesgoincendios IS 'Mapa de Riesgo de Incendios Forestales';

-- ------- Riesgos Geológicos -------
CREATE TABLE IF NOT EXISTS capas.riesgosgeologicos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo_riesgo VARCHAR(100),  -- Deslizamiento, Subsidencia, Sismicidad, etc.
    magnitud VARCHAR(50),  -- Alto, Medio, Bajo
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.riesgosgeologicos IS 'Mapa de Riesgos Geológicos - Deslizamientos, subsidencia, sismicidad';

-- ------- Zonificación Sísmica -------
CREATE TABLE IF NOT EXISTS capas.sismicidad (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    zona_sismica VARCHAR(100),  -- Z1, Z2, Z3, Z4, Z5
    aceleracion_sismica NUMERIC(5, 3),
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.sismicidad IS 'Zonificación Sísmica de España';

-- ------- Líneas Eléctricas de Alta Tensión -------
CREATE TABLE IF NOT EXISTS capas.lineaselectricas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    voltaje_kv INT,  -- 132, 220, 380, etc.
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    distancia_restriccion_m INT DEFAULT 50,
    geom GEOMETRY(MultiLineString, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.lineaselectricas IS 'Líneas eléctricas de alta tensión (servidumbres)';

-- ------- Hábitats (NATURA 2000) -------
CREATE TABLE IF NOT EXISTS capas.habitats (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50),  -- 92A0, 9230, etc. (códigos NATURA 2000)
    nombre VARCHAR(255),
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    superficie_ha NUMERIC(10, 2),
    estado_conservacion VARCHAR(50),  -- Favorable, Desfavorable, etc.
    geom GEOMETRY(MultiPolygon, 4326),
    fecha_actualizacion DATE,
    metadatos JSONB
);
COMMENT ON TABLE capas.habitats IS 'Hábitats de Interés Comunitario (HIC)';

-- ============================================================================
-- 6. CREAR ÍNDICES GIST (Spatial Indexing)
-- ============================================================================
-- Los índices GIST aceleran búsquedas espaciales como ST_Intersects, ST_Contains, etc.

CREATE INDEX IF NOT EXISTS idx_rednatura_geom 
  ON capas.rednatura USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_zonasinundables_geom 
  ON capas.zonasinundables USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_espaciosnaturales_geom 
  ON capas.espaciosnaturales USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_viaspocuarias_geom 
  ON capas.viaspocuarias USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_masasagua_geom 
  ON capas.masasagua USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_seveso_geom 
  ON capas.seveso USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_dph_geom 
  ON capas.dph USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_riesgoincendios_geom 
  ON capas.riesgoincendios USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_riesgosgeologicos_geom 
  ON capas.riesgosgeologicos USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_sismicidad_geom 
  ON capas.sismicidad USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_lineaselectricas_geom 
  ON capas.lineaselectricas USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_habitats_geom 
  ON capas.habitats USING GIST (geom);

-- Índices adicionales para búsquedas por atributos
CREATE INDEX IF NOT EXISTS idx_rednatura_tipo 
  ON capas.rednatura (tipo);

CREATE INDEX IF NOT EXISTS idx_zonasinundables_peligrosidad 
  ON capas.zonasinundables (peligrosidad);

CREATE INDEX IF NOT EXISTS idx_riesgoincendios_tipo_riesgo 
  ON capas.riesgoincendios (tipo_riesgo);

-- ============================================================================
-- 7. CREAR TABLA DE METADATOS PARA CAPAS
-- ============================================================================
CREATE TABLE IF NOT EXISTS capas.metadata (
    id SERIAL PRIMARY KEY,
    nombre_capa VARCHAR(255) UNIQUE NOT NULL,
    tabla_postgis VARCHAR(100),
    titulo VARCHAR(255),
    descripcion TEXT,
    fuente VARCHAR(255),
    fecha_ultima_actualizacion DATE,
    epsg INT DEFAULT 4326,
    num_features INT,
    area_ha NUMERIC(15, 2),
    disponible_fgb BOOLEAN DEFAULT FALSE,
    disponible_gpkg BOOLEAN DEFAULT FALSE,
    disponible_postgis BOOLEAN DEFAULT FALSE,
    ruta_fgb VARCHAR(255),
    ruta_gpkg VARCHAR(255),
    metadata_json JSONB,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE capas.metadata IS 'Metadatos de capas disponibles (control de qué existe dónde)';

-- Insertar metadatos iniciales
INSERT INTO capas.metadata (nombre_capa, tabla_postgis, titulo, descripcion, fuente, disponible_postgis, epsg)
VALUES 
    ('rednatura', 'capas.rednatura', 'Red Natura 2000', 'Espacios protegidos europeos', 'MITERD', FALSE, 4326),
    ('zonasinundables', 'capas.zonasinundables', 'Zonas Inundables', 'Mapas de peligrosidad por inundación', 'Confederaciones Hidrográficas', FALSE, 4326),
    ('espaciosnaturales', 'capas.espaciosnaturales', 'Espacios Naturales Protegidos', 'Parques, reservas y monumentos naturales', 'MITERD', FALSE, 4326),
    ('viaspocuarias', 'capas.viaspocuarias', 'Vías Pecuarias', 'Vías de uso público para tránsito de ganado', 'CCAA', FALSE, 4326),
    ('masasagua', 'capas.masasagua', 'Masas de Agua', 'Cursos de agua y cauces', 'Confederaciones Hidrográficas', FALSE, 4326),
    ('seveso', 'capas.seveso', 'Establecimientos SEVESO', 'Industrias peligrosas', 'MITERD / CCAA', FALSE, 4326),
    ('dph', 'capas.dph', 'Dominio Público Hidráulico', 'Cauces y servidumbres', 'Confederaciones Hidrográficas', FALSE, 4326),
    ('riesgoincendios', 'capas.riesgoincendios', 'Riesgo de Incendios Forestales', 'Índice de riesgo de incendios', 'MITERD / MAPA', FALSE, 4326),
    ('riesgosgeologicos', 'capas.riesgosgeologicos', 'Riesgos Geológicos', 'Deslizamientos, subsidencia, sismicidad', 'IGN / IGME', FALSE, 4326),
    ('sismicidad', 'capas.sismicidad', 'Zonificación Sísmica', 'Zonas de riesgo sísmico', 'IGN', FALSE, 4326),
    ('lineaselectricas', 'capas.lineaselectricas', 'Líneas Eléctricas AT', 'Líneas de alta tensión (servidumbres)', 'REE', FALSE, 4326),
    ('habitats', 'capas.habitats', 'Hábitats de Interés Comunitario', 'HIC en NATURA 2000', 'MITERD', FALSE, 4326)
ON CONFLICT (nombre_capa) DO NOTHING;

-- ============================================================================
-- 8. CREAR TABLA DE AUDITORÍA (OPCIONAL)
-- ============================================================================
CREATE TABLE IF NOT EXISTS capas.audit_log (
    id SERIAL PRIMARY KEY,
    tabla VARCHAR(255),
    operacion VARCHAR(50),  -- INSERT, UPDATE, DELETE
    registro_id INT,
    usuario VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detalles JSONB
);
COMMENT ON TABLE capas.audit_log IS 'Log de auditoría para cambios en capas';

-- ============================================================================
-- 9. CREAR VISTA PARA ESTADÍSTICAS RÁPIDAS
-- ============================================================================
CREATE OR REPLACE VIEW capas.estadisticas_capas AS
SELECT 
    'rednatura' as capa,
    COUNT(*) as num_features,
    ROUND(SUM(superficie_ha)::numeric, 2) as superficie_total_ha,
    ST_AsText(ST_Envelope(ST_Collect(geom))) as bbox
FROM capas.rednatura
UNION ALL
SELECT 
    'zonasinundables' as capa,
    COUNT(*) as num_features,
    NULL as superficie_total_ha,
    ST_AsText(ST_Envelope(ST_Collect(geom))) as bbox
FROM capas.zonasinundables
UNION ALL
SELECT 
    'espaciosnaturales' as capa,
    COUNT(*) as num_features,
    ROUND(SUM(superficie_ha)::numeric, 2) as superficie_total_ha,
    ST_AsText(ST_Envelope(ST_Collect(geom))) as bbox
FROM capas.espaciosnaturales
UNION ALL
SELECT 
    'seveso' as capa,
    COUNT(*) as num_features,
    NULL as superficie_total_ha,
    ST_AsText(ST_Envelope(ST_Collect(geom))) as bbox
FROM capas.seveso
UNION ALL
SELECT 
    'dph' as capa,
    COUNT(*) as num_features,
    NULL as superficie_total_ha,
    ST_AsText(ST_Envelope(ST_Collect(geom))) as bbox
FROM capas.dph;

-- ============================================================================
-- 10. PERMISOS Y SEGURIDAD
-- ============================================================================
-- Conceder permisos al usuario manuel
GRANT CONNECT ON DATABASE GIS TO manuel;
GRANT USAGE ON SCHEMA capas TO manuel;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA capas TO manuel;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA capas TO manuel;

-- Permitir que manuel cree nuevas tablas en el esquema capas
ALTER DEFAULT PRIVILEGES IN SCHEMA capas GRANT ALL ON TABLES TO manuel;
ALTER DEFAULT PRIVILEGES IN SCHEMA capas GRANT ALL ON SEQUENCES TO manuel;

-- ============================================================================
-- 11. VERIFICACIÓN FINAL
-- ============================================================================
SELECT 
    'PostgreSQL Version' as verificacion,
    version() as resultado
UNION ALL
SELECT 
    'PostGIS Installation',
    postgis_version()
UNION ALL
SELECT 
    'Tables Created',
    COUNT(*)::text
FROM information_schema.tables
WHERE table_schema = 'capas'
UNION ALL
SELECT 
    'Indexes Created',
    COUNT(*)::text
FROM pg_indexes
WHERE schemaname = 'capas';SELECT 
    'PostgreSQL Version' as verificacion,
    version() as resultado
UNION ALL
SELECT 
    'PostGIS Installation',
    postgis_version()
UNION ALL
SELECT 
    'Tables Created',
    COUNT(*)::text
FROM information_schema.tables
WHERE table_schema = 'capas'
UNION ALL
SELECT 
    'Indexes Created',
    COUNT(*)::text
FROM pg_indexes
WHERE schemaname = 'capas';

-- ============================================================================
-- FIN DE SCRIPT
-- ============================================================================
-- 
-- Si todo salió bien, deberías ver:
--  ✅ PostgreSQL Version: ...
--  ✅ PostGIS Installation: PostGIS 3.x
--  ✅ Tables Created: 12
--  ✅ Indexes Created: 19+
--
-- Para conectar desde la app:
--   POSTGIS_HOST=localhost (o IP del servidor)
--   POSTGIS_PORT=5432
--   POSTGIS_DATABASE=GIS
--   POSTGIS_USER=manuel
--   POSTGIS_PASSWORD=tu_contraseña
--
