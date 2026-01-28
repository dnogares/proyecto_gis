#!/usr/bin/env python3
"""
Script de verificación y pruebas del sistema FlatGeobuf + PostGIS

Verifica que todos los componentes estén funcionando correctamente
"""

import sys
from pathlib import Path
import logging
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemVerifier:
    """Verificador del sistema GIS"""
    
    def __init__(self):
        self.results = {
            "python_packages": {},
            "postgis": {},
            "files": {},
            "fgb_files": []
        }
    
    def verificar_paquetes_python(self) -> bool:
        """Verifica que los paquetes Python necesarios estén instalados"""
        logger.info("\n📦 VERIFICANDO PAQUETES PYTHON")
        logger.info("=" * 70)
        
        packages = {
            "geopandas": "GeoPandas",
            "pyogrio": "PyOGRIO (motor FlatGeobuf)",
            "shapely": "Shapely",
            "fiona": "Fiona",
            "psycopg2": "psycopg2 (PostgreSQL)",
            "fastapi": "FastAPI",
            "uvicorn": "Uvicorn"
        }
        
        all_ok = True
        
        for package, name in packages.items():
            try:
                module = __import__(package)
                version = getattr(module, "__version__", "desconocida")
                logger.info(f"  ✅ {name}: {version}")
                self.results["python_packages"][package] = {
                    "installed": True,
                    "version": version
                }
            except ImportError as e:
                logger.error(f"  ❌ {name}: NO INSTALADO")
                self.results["python_packages"][package] = {
                    "installed": False,
                    "error": str(e)
                }
                all_ok = False
        
        return all_ok
    
    def verificar_gdal(self) -> bool:
        """Verifica que GDAL esté instalado"""
        logger.info("\n🗺️  VERIFICANDO GDAL")
        logger.info("=" * 70)
        
        try:
            from osgeo import gdal
            version = gdal.__version__
            logger.info(f"  ✅ GDAL: {version}")
            
            # Verificar soporte FlatGeobuf
            drivers = []
            for i in range(gdal.GetDriverCount()):
                driver = gdal.GetDriver(i)
                drivers.append(driver.ShortName)
            
            if "FlatGeobuf" in drivers:
                logger.info("  ✅ FlatGeobuf driver disponible")
                return True
            else:
                logger.error("  ❌ FlatGeobuf driver NO disponible")
                return False
                
        except ImportError:
            logger.error("  ❌ GDAL NO instalado")
            logger.error("     Ubuntu/Debian: sudo apt-get install gdal-bin libgdal-dev")
            logger.error("     macOS: brew install gdal")
            return False
    
    def verificar_postgis(self) -> bool:
        """Verifica conexión a PostGIS"""
        logger.info("\n🗄️  VERIFICANDO POSTGIS")
        logger.info("=" * 70)
        
        try:
            from services.postgis_service import PostGISService
            
            # Intentar conexión
            service = PostGISService(
                host="localhost",
                database="GIS",
                user="manuel",
                password="Aa123456"
            )
            
            # Verificar versión PostGIS
            with service.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT PostGIS_version();")
                    version = cur.fetchone()[0]
                    logger.info(f"  ✅ PostGIS: {version}")
                    
                    # Listar tablas espaciales
                    cur.execute("""
                        SELECT COUNT(*)
                        FROM geometry_columns;
                    """)
                    num_tablas = cur.fetchone()[0]
                    logger.info(f"  ✅ Tablas espaciales: {num_tablas}")
            
            service.cerrar()
            
            self.results["postgis"] = {
                "available": True,
                "version": version,
                "tables": num_tablas
            }
            
            return True
            
        except Exception as e:
            logger.warning(f"  ⚠️  PostGIS no disponible: {e}")
            logger.info("     (Opcional - el sistema funciona sin PostGIS)")
            
            self.results["postgis"] = {
                "available": False,
                "error": str(e)
            }
            
            return False
    
    def verificar_estructura_directorios(self) -> bool:
        """Verifica que existan los directorios necesarios"""
        logger.info("\n📁 VERIFICANDO ESTRUCTURA DE DIRECTORIOS")
        logger.info("=" * 70)
        
        directorios = {
            "capas": "Directorio principal de capas",
            "capas/fgb": "FlatGeobuf files",
            "capas/gpkg": "GeoPackage files",
            "static": "Archivos estáticos",
            "static/js": "JavaScript files",
            "templates": "HTML templates",
            "services": "Servicios Python",
            "scripts": "Scripts de utilidad"
        }
        
        all_ok = True
        
        for dir_path, descripcion in directorios.items():
            path = Path(dir_path)
            exists = path.exists()
            
            if exists:
                logger.info(f"  ✅ {dir_path}: OK")
            else:
                logger.warning(f"  ⚠️  {dir_path}: NO EXISTE")
                all_ok = False
            
            self.results["files"][dir_path] = {
                "exists": exists,
                "description": descripcion
            }
        
        return all_ok
    
    def verificar_archivos_fgb(self) -> List[Dict]:
        """Lista y verifica archivos FlatGeobuf"""
        logger.info("\n🗂️  VERIFICANDO ARCHIVOS FLATGEOBUF")
        logger.info("=" * 70)
        
        fgb_dir = Path("capas/fgb")
        
        if not fgb_dir.exists():
            logger.warning("  ⚠️  Directorio capas/fgb no existe")
            return []
        
        fgb_files = list(fgb_dir.glob("*.fgb"))
        
        if not fgb_files:
            logger.warning("  ⚠️  No hay archivos .fgb")
            logger.info("\n     💡 Para crear archivos FlatGeobuf:")
            logger.info("        python scripts/export_postgis_to_fgb.py")
            logger.info("        python scripts/convert_to_fgb.py")
            return []
        
        logger.info(f"  📊 {len(fgb_files)} archivos encontrados:\n")
        
        try:
            import fiona
            
            for fgb_file in sorted(fgb_files):
                try:
                    with fiona.open(fgb_file) as src:
                        size_mb = fgb_file.stat().st_size / (1024 * 1024)
                        count = len(src)
                        
                        logger.info(
                            f"  ✅ {fgb_file.name}\n"
                            f"     - Tamaño: {size_mb:.2f} MB\n"
                            f"     - Features: {count:,}\n"
                            f"     - CRS: {src.crs}\n"
                        )
                        
                        self.results["fgb_files"].append({
                            "name": fgb_file.name,
                            "size_mb": round(size_mb, 2),
                            "features": count,
                            "crs": str(src.crs)
                        })
                        
                except Exception as e:
                    logger.error(f"  ❌ Error leyendo {fgb_file.name}: {e}")
        
        except ImportError:
            logger.warning("  ⚠️  Fiona no disponible, no se pueden leer metadatos")
            
            # Info básica sin metadatos
            for fgb_file in sorted(fgb_files):
                size_mb = fgb_file.stat().st_size / (1024 * 1024)
                logger.info(f"  • {fgb_file.name} ({size_mb:.2f} MB)")
        
        return fgb_files
    
    def verificar_archivos_principales(self) -> bool:
        """Verifica que existan los archivos principales del proyecto"""
        logger.info("\n📄 VERIFICANDO ARCHIVOS PRINCIPALES")
        logger.info("=" * 70)
        
        archivos = {
            "main.py": "FastAPI backend",
            "requirements.txt": "Dependencias Python",
            "services/data_source_manager.py": "Gestor de fuentes de datos",
            "static/js/viewer.js": "Visor JavaScript",
            "templates/index.html": "HTML principal",
            "scripts/export_postgis_to_fgb.py": "Script exportación PostGIS",
            "scripts/convert_to_fgb.py": "Script conversión GPKG/SHP"
        }
        
        all_ok = True
        
        for archivo, descripcion in archivos.items():
            path = Path(archivo)
            exists = path.exists()
            
            if exists:
                size = path.stat().st_size
                logger.info(f"  ✅ {archivo} ({size:,} bytes)")
            else:
                logger.error(f"  ❌ {archivo} NO ENCONTRADO")
                all_ok = False
        
        return all_ok
    
    def generar_reporte(self) -> Dict:
        """Genera reporte final de verificación"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 REPORTE FINAL")
        logger.info("=" * 70)
        
        # Resumen de paquetes Python
        packages_ok = sum(
            1 for p in self.results["python_packages"].values()
            if p.get("installed", False)
        )
        packages_total = len(self.results["python_packages"])
        
        logger.info(f"\n📦 Paquetes Python: {packages_ok}/{packages_total} instalados")
        
        # PostGIS
        postgis_status = "✅ Disponible" if self.results["postgis"].get("available") else "⚠️  No disponible"
        logger.info(f"🗄️  PostGIS: {postgis_status}")
        
        # Archivos FGB
        num_fgb = len(self.results["fgb_files"])
        logger.info(f"🗂️  Archivos FlatGeobuf: {num_fgb}")
        
        # Recomendaciones
        logger.info("\n💡 RECOMENDACIONES:")
        
        if packages_ok < packages_total:
            logger.info("  • Instalar paquetes faltantes: pip install -r requirements.txt")
        
        if not self.results["postgis"].get("available"):
            logger.info("  • PostGIS opcional pero recomendado para análisis")
            logger.info("    Instalar: sudo apt-get install postgresql postgis")
        
        if num_fgb == 0:
            logger.info("  • Crear archivos FlatGeobuf:")
            logger.info("    python scripts/export_postgis_to_fgb.py")
            logger.info("    python scripts/convert_to_fgb.py")
        
        # Estado general
        all_ok = (
            packages_ok == packages_total and
            num_fgb > 0
        )
        
        if all_ok:
            logger.info("\n✅ ¡SISTEMA LISTO!")
            logger.info("   Iniciar servidor: python main.py")
            logger.info("   Abrir navegador: http://localhost:8000")
        else:
            logger.info("\n⚠️  SISTEMA REQUIERE CONFIGURACIÓN")
            logger.info("   Ver recomendaciones arriba")
        
        logger.info("\n" + "=" * 70)
        
        return self.results


def main():
    """Función principal"""
    logger.info("🔍 VERIFICACIÓN DEL SISTEMA GIS")
    logger.info("=" * 70)
    
    verifier = SystemVerifier()
    
    # Ejecutar verificaciones
    verifier.verificar_paquetes_python()
    verifier.verificar_gdal()
    verifier.verificar_postgis()
    verifier.verificar_estructura_directorios()
    verifier.verificar_archivos_fgb()
    verifier.verificar_archivos_principales()
    
    # Generar reporte
    results = verifier.generar_reporte()
    
    # Retornar código de salida
    packages_ok = sum(
        1 for p in results["python_packages"].values()
        if p.get("installed", False)
    )
    packages_total = len(results["python_packages"])
    
    return 0 if packages_ok == packages_total else 1


if __name__ == "__main__":
    sys.exit(main())
