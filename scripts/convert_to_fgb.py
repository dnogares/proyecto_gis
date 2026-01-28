#!/usr/bin/env python3
"""
Script para convertir GPKG/Shapefile a FlatGeobuf en batch

Convierte todos los archivos GPKG y SHP encontrados en los directorios
especificados a formato FlatGeobuf (.fgb)

Uso:
    python convert_to_fgb.py
    python convert_to_fgb.py --gpkg-dir capas/gpkg --shp-dir capas/shp
"""

import argparse
import sys
from pathlib import Path
import geopandas as gpd
import logging
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convertir_archivo(
    input_path: Path,
    output_dir: Path,
    force: bool = False
) -> bool:
    """
    Convierte un archivo a FlatGeobuf
    
    Args:
        input_path: Ruta del archivo de entrada (GPKG/SHP)
        output_dir: Directorio de salida
        force: Si True, sobreescribe archivos existentes
        
    Returns:
        True si la conversión fue exitosa
    """
    nombre_base = input_path.stem
    output_path = output_dir / f"{nombre_base}.fgb"
    
    # Verificar si ya existe
    if output_path.exists() and not force:
        logger.info(f"  ⏭️  {nombre_base}.fgb ya existe (usa --force para sobreescribir)")
        return True
    
    logger.info(f"📥 Convirtiendo {input_path.name}...")
    
    try:
        # Leer archivo
        logger.info(f"  → Leyendo {input_path.name}...")
        gdf = gpd.read_file(input_path)
        
        if gdf.empty:
            logger.warning(f"  ⚠️  Archivo vacío: {input_path.name}")
            return False
        
        logger.info(f"  → {len(gdf):,} features encontrados")
        
        # Validar geometrías
        invalid = ~gdf.geometry.is_valid
        if invalid.any():
            logger.warning(f"  ⚠️  {invalid.sum()} geometrías inválidas, reparando...")
            gdf.geometry = gdf.geometry.buffer(0)
        
        # Asegurar CRS
        if gdf.crs is None:
            logger.warning(f"  ⚠️  CRS no definido, asignando EPSG:25830")
            gdf.set_crs("EPSG:25830", inplace=True)
        
        # Convertir a EPSG:4326 para web
        if gdf.crs.to_epsg() != 4326:
            logger.info(f"  → Reproyectando de {gdf.crs} a EPSG:4326...")
            gdf = gdf.to_crs("EPSG:4326")
        
        # Exportar a FlatGeobuf
        logger.info(f"  → Exportando a {output_path.name}...")
        
        gdf.to_file(
            output_path,
            driver="FlatGeobuf",
            engine="pyogrio"  # Más rápido que fiona
        )
        
        # Estadísticas
        input_size = input_path.stat().st_size / (1024 * 1024)
        output_size = output_path.stat().st_size / (1024 * 1024)
        reduction = ((input_size - output_size) / input_size) * 100 if input_size > 0 else 0
        
        logger.info(
            f"  ✅ {output_path.name} creado\n"
            f"     Tamaño: {output_size:.2f} MB (era {input_size:.2f} MB, "
            f"{reduction:.1f}% reducción)\n"
            f"     Features: {len(gdf):,}"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Error convirtiendo {input_path.name}: {e}")
        return False


def convertir_directorio(
    input_dir: Path,
    output_dir: Path,
    extension: str,
    force: bool = False
) -> Dict[str, int]:
    """
    Convierte todos los archivos de un directorio
    
    Args:
        input_dir: Directorio de entrada
        output_dir: Directorio de salida
        extension: Extensión de archivos a buscar ('.gpkg' o '.shp')
        force: Si True, sobreescribe archivos existentes
        
    Returns:
        Diccionario con estadísticas
    """
    if not input_dir.exists():
        logger.warning(f"⚠️  Directorio no existe: {input_dir}")
        return {"exitosas": 0, "fallidas": 0, "saltadas": 0}
    
    # Buscar archivos
    archivos = list(input_dir.glob(f"*{extension}"))
    
    if not archivos:
        logger.info(f"ℹ️  No se encontraron archivos {extension} en {input_dir}")
        return {"exitosas": 0, "fallidas": 0, "saltadas": 0}
    
    logger.info(f"\n📂 Procesando {len(archivos)} archivos {extension}...")
    logger.info("-" * 70)
    
    stats = {"exitosas": 0, "fallidas": 0, "saltadas": 0}
    
    for archivo in sorted(archivos):
        if convertir_archivo(archivo, output_dir, force):
            stats["exitosas"] += 1
        else:
            stats["fallidas"] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Convertir GPKG/Shapefile a FlatGeobuf en batch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python convert_to_fgb.py
  python convert_to_fgb.py --gpkg-dir mi_directorio/gpkg
  python convert_to_fgb.py --force
        """
    )
    
    parser.add_argument(
        '--gpkg-dir',
        type=str,
        default='capas/gpkg',
        help='Directorio con archivos GPKG (default: capas/gpkg)'
    )
    
    parser.add_argument(
        '--shp-dir',
        type=str,
        default='capas/shp',
        help='Directorio con archivos Shapefile (default: capas/shp)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='capas/fgb',
        help='Directorio de salida (default: capas/fgb)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Sobreescribir archivos existentes'
    )
    
    args = parser.parse_args()
    
    # Convertir a Path
    gpkg_dir = Path(args.gpkg_dir)
    shp_dir = Path(args.shp_dir)
    output_dir = Path(args.output_dir)
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("CONVERSIÓN BATCH A FLATGEOBUF")
    logger.info("=" * 70)
    logger.info(f"📁 Directorio GPKG: {gpkg_dir}")
    logger.info(f"📁 Directorio Shapefile: {shp_dir}")
    logger.info(f"📁 Directorio salida: {output_dir}")
    logger.info(f"🔄 Modo: {'FORZAR' if args.force else 'NORMAL'}")
    
    # Convertir GPKG
    stats_gpkg = convertir_directorio(
        gpkg_dir,
        output_dir,
        '.gpkg',
        args.force
    )
    
    # Convertir Shapefile
    stats_shp = convertir_directorio(
        shp_dir,
        output_dir,
        '.shp',
        args.force
    )
    
    # Resumen total
    total_exitosas = stats_gpkg["exitosas"] + stats_shp["exitosas"]
    total_fallidas = stats_gpkg["fallidas"] + stats_shp["fallidas"]
    total = total_exitosas + total_fallidas
    
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN TOTAL:")
    logger.info(f"  ✅ Exitosas: {total_exitosas}/{total}")
    logger.info(f"  ❌ Fallidas: {total_fallidas}/{total}")
    logger.info("=" * 70)
    
    if total_exitosas > 0:
        logger.info(f"\n✨ Archivos FlatGeobuf generados en: {output_dir}")
        logger.info("\n💡 PRÓXIMOS PASOS:")
        logger.info("  1. Verificar archivos .fgb generados")
        logger.info("  2. Configurar FastAPI para servir /capas/fgb")
        logger.info("  3. Actualizar frontend para usar FlatGeobuf")
        logger.info("  4. ¡Disfrutar de 20x más velocidad! 🚀")
    
    return 0 if total_fallidas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
