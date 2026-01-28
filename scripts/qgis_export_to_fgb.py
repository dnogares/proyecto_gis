"""
Script para QGIS Python Console
Exporta todas las capas del proyecto a FlatGeobuf

Uso:
1. Abrir QGIS
2. Abrir Python Console (Ctrl+Alt+P)
3. Copiar y pegar este script
4. Ejecutar
"""

from qgis.core import QgsVectorFileWriter, QgsProject, QgsCoordinateReferenceSystem
from pathlib import Path
import os

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Directorio de salida (relativo al proyecto QGIS o absoluto)
OUTPUT_DIR = Path("capas/fgb")

# CRS objetivo (EPSG:4326 para web)
TARGET_CRS = QgsCoordinateReferenceSystem("EPSG:4326")

# Opciones de exportación
ENCODING = "UTF-8"

# ============================================================================
# FUNCIONES
# ============================================================================

def exportar_capa_a_fgb(layer, output_path, target_crs):
    """
    Exporta una capa a FlatGeobuf
    
    Args:
        layer: QgsVectorLayer
        output_path: Path de salida
        target_crs: CRS objetivo
    
    Returns:
        Tuple (success: bool, message: str)
    """
    # Configurar opciones de exportación
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "FlatGeobuf"
    options.fileEncoding = ENCODING
    
    # Reproyectar si es necesario
    if layer.crs() != target_crs:
        options.ct = QgsCoordinateTransform(
            layer.crs(),
            target_crs,
            QgsProject.instance()
        )
    
    # Exportar
    error = QgsVectorFileWriter.writeAsVectorFormatV2(
        layer,
        str(output_path),
        QgsProject.instance().transformContext(),
        options
    )
    
    if error[0] == QgsVectorFileWriter.NoError:
        size_mb = output_path.stat().st_size / (1024 * 1024)
        return True, f"✅ {layer.name()} → {output_path.name} ({size_mb:.2f} MB)"
    else:
        return False, f"❌ Error: {layer.name()} - {error[1]}"


def main():
    """Función principal"""
    print("=" * 70)
    print("EXPORTACIÓN DE CAPAS A FLATGEOBUF")
    print("=" * 70)
    
    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de salida: {OUTPUT_DIR.absolute()}")
    
    # Obtener todas las capas vectoriales del proyecto
    layers = [
        layer for layer in QgsProject.instance().mapLayers().values()
        if layer.type() == QgsMapLayer.VectorLayer
    ]
    
    if not layers:
        print("⚠️  No hay capas vectoriales en el proyecto")
        return
    
    print(f"📊 {len(layers)} capas encontradas\n")
    
    # Exportar cada capa
    exitosas = 0
    fallidas = 0
    
    for layer in layers:
        # Nombre de archivo de salida
        nombre_limpio = layer.name().lower()
        nombre_limpio = nombre_limpio.replace(" ", "_")
        nombre_limpio = ''.join(c for c in nombre_limpio if c.isalnum() or c == '_')
        
        output_path = OUTPUT_DIR / f"{nombre_limpio}.fgb"
        
        print(f"📥 Exportando: {layer.name()} ({layer.featureCount()} features)...")
        
        # Exportar
        success, message = exportar_capa_a_fgb(layer, output_path, TARGET_CRS)
        print(f"   {message}")
        
        if success:
            exitosas += 1
        else:
            fallidas += 1
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN:")
    print(f"  ✅ Exitosas: {exitosas}/{len(layers)}")
    print(f"  ❌ Fallidas: {fallidas}/{len(layers)}")
    print("=" * 70)
    
    if exitosas > 0:
        print(f"\n✨ Archivos FlatGeobuf generados en:")
        print(f"   {OUTPUT_DIR.absolute()}")
        print("\n💡 PRÓXIMOS PASOS:")
        print("  1. Copiar archivos .fgb a tu proyecto web")
        print("  2. Configurar FastAPI para servir /capas/fgb")
        print("  3. Actualizar frontend para usar FlatGeobuf")
        print("  4. ¡Disfrutar de 20x más velocidad! 🚀")


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    # Verificar que estamos en QGIS
    try:
        from qgis.core import QgsMapLayer, QgsCoordinateTransform
        main()
    except ImportError:
        print("❌ Este script debe ejecutarse desde QGIS Python Console")
        print("   1. Abrir QGIS")
        print("   2. Plugins → Python Console (Ctrl+Alt+P)")
        print("   3. Copiar y pegar este script")
