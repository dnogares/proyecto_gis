#!/usr/bin/env python3
"""
Script para exportar capas de PostGIS a formato FlatGeobuf (.fgb)

FlatGeobuf es superior a GPKG/Shapefile para visualización web porque:
- Soporta HTTP Range Requests (descarga solo lo visible)
- Índice R-tree integrado
- Streaming de features
- Lectura directa desde navegador sin backend

Uso:
    python export_postgis_to_fgb.py
"""

import geopandas as gpd
from pathlib import Path
import sys
import logging
from typing import List, Dict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de PostGIS
POSTGIS_CONFIG = {
    "host": "localhost",
    "database": "GIS",
    "user": "manuel",
    "password": "Aa123456",
    "port": 5432
}

# Capas a exportar
CAPAS_EXPORTAR = [
    {
        "schema": "public",
        "tabla": "biodiversidad:RedNatura",
        "nombre": "rednatura",
        "descripcion": "Red Natura 2000"
    },
    {
        "schema": "public",
        "tabla": "biodiversidad:VP_ViasPecuarias",
        "nombre": "viaspocuarias",
        "descripcion": "Vías Pecuarias"
    },
    {
        "schema": "public",
        "tabla": "biodiversidad:EspaciosNaturalesProtegidos",
        "nombre": "espaciosnaturales",
        "descripcion": "Espacios Naturales Protegidos"
    },
    {
        "schema": "public",
        "tabla": "hidrologia:MasasAgua",
        "nombre": "masasagua",
        "descripcion": "Masas de Agua"
    },
    {
        "schema": "public",
        "tabla": "hidrologia:ZonasInundables",
        "nombre": "zonasinundables",
        "descripcion": "Zonas Inundables"
    }
]


def crear_connection_string(config: Dict[str, str]) -> str:
    """Crear connection string para PostgreSQL"""
    return (
        f"postgresql://{config['user']}:{config['password']}@"
        f"{config['host']}:{config['port']}/{config['database']}"
    )


def exportar_capa_a_fgb(
    capa_info: Dict[str, str],
    output_dir: Path,
    connection_string: str
) -> bool:
    """
    Exporta una capa de PostGIS a FlatGeobuf
    
    Args:
        capa_info: Diccionario con info de la capa (schema, tabla, nombre)
        output_dir: Directorio de salida
        connection_string: String de conexión a PostgreSQL
        
    Returns:
        True si la exportación fue exitosa
    """
    nombre = capa_info["nombre"]
    tabla = capa_info["tabla"]
    schema = capa_info["schema"]
    
    logger.info(f"📥 Exportando {nombre} ({capa_info['descripcion']})...")
    
    try:
        # Construir query SQL
        query = f'SELECT * FROM {schema}."{tabla}"'
        
        # Leer desde PostGIS
        logger.info(f"  → Leyendo desde PostGIS...")
        gdf = gpd.read_postgis(
            query,
            connection_string,
            geom_col='geom'
        )
        
        if gdf.empty:
            logger.warning(f"  ⚠️  Capa vacía: {nombre}")
            return False
        
        # Validar geometrías
        logger.info(f"  → Validando geometrías...")
        invalid_geoms = ~gdf.geometry.is_valid
        if invalid_geoms.any():
            logger.warning(f"  ⚠️  {invalid_geoms.sum()} geometrías inválidas, reparando...")
            gdf.geometry = gdf.geometry.buffer(0)
        
        # Asegurar CRS correcto (EPSG:4326 para web)
        if gdf.crs is None:
            logger.warning(f"  ⚠️  CRS no definido, asignando EPSG:25830")
            gdf.set_crs("EPSG:25830", inplace=True)
        
        if gdf.crs.to_epsg() != 4326:
            logger.info(f"  → Reproyectando a EPSG:4326...")
            gdf = gdf.to_crs("EPSG:4326")
        
        # Exportar a FlatGeobuf
        output_path = output_dir / f"{nombre}.fgb"
        logger.info(f"  → Exportando a {output_path.name}...")
        
        gdf.to_file(
            output_path,
            driver="FlatGeobuf",
            engine="pyogrio"  # Más rápido que fiona
        )
        
        # Estadísticas
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(
            f"  ✅ {output_path.name} "
            f"({size_mb:.2f} MB, {len(gdf):,} features)"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Error exportando {nombre}: {e}")
        return False


def exportar_todas_las_capas(
    capas: List[Dict[str, str]],
    output_dir: Path,
    connection_string: str
) -> Dict[str, int]:
    """
    Exporta todas las capas especificadas
    
    Returns:
        Diccionario con estadísticas de exportación
    """
    stats = {
        "exitosas": 0,
        "fallidas": 0,
        "total": len(capas)
    }
    
    for capa in capas:
        if exportar_capa_a_fgb(capa, output_dir, connection_string):
            stats["exitosas"] += 1
        else:
            stats["fallidas"] += 1
    
    return stats


def main():
    """Función principal"""
    logger.info("=" * 70)
    logger.info("EXPORTACIÓN DE POSTGIS A FLATGEOBUF")
    logger.info("=" * 70)
    
    # Crear directorio de salida
    output_dir = Path(__file__).parent.parent / "capas" / "fgb"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Directorio de salida: {output_dir}")
    
    # Crear connection string
    connection_string = crear_connection_string(POSTGIS_CONFIG)
    
    # Verificar conexión
    logger.info(f"🔌 Conectando a PostgreSQL...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=POSTGIS_CONFIG["host"],
            database=POSTGIS_CONFIG["database"],
            user=POSTGIS_CONFIG["user"],
            password=POSTGIS_CONFIG["password"],
            port=POSTGIS_CONFIG["port"]
        )
        conn.close()
        logger.info("  ✅ Conexión exitosa")
    except Exception as e:
        logger.error(f"  ❌ Error de conexión: {e}")
        logger.error("Verifica que PostgreSQL esté corriendo y las credenciales sean correctas")
        sys.exit(1)
    
    # Exportar capas
    logger.info(f"\n🚀 Exportando {len(CAPAS_EXPORTAR)} capas...")
    logger.info("-" * 70)
    
    stats = exportar_todas_las_capas(
        CAPAS_EXPORTAR,
        output_dir,
        connection_string
    )
    
    # Resumen
    logger.info("-" * 70)
    logger.info("\n📊 RESUMEN DE EXPORTACIÓN:")
    logger.info(f"  ✅ Exitosas: {stats['exitosas']}/{stats['total']}")
    logger.info(f"  ❌ Fallidas: {stats['fallidas']}/{stats['total']}")
    
    if stats["exitosas"] > 0:
        logger.info(f"\n📁 Archivos generados en: {output_dir}")
        logger.info("\n💡 PRÓXIMOS PASOS:")
        logger.info("  1. Configurar FastAPI para servir archivos .fgb")
        logger.info("  2. Actualizar frontend para usar FlatGeobuf")
        logger.info("  3. Verificar que HTTP Range Requests funcione")
    
    logger.info("\n✨ Exportación completada")
    
    return 0 if stats["fallidas"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
