"""
Data Source Manager con soporte híbrido PostGIS + FlatGeobuf + GPKG

Estrategia:
- Frontend: Usa FlatGeobuf directamente (HTTP Range, streaming)
- Backend: Usa PostGIS para análisis (índices GIST, consultas SQL)
- Fallback: GPKG para compatibilidad
"""

import geopandas as gpd
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    Gestor centralizado de fuentes de datos geoespaciales.
    
    Soporta múltiples fuentes con priorización automática:
    1. PostGIS (análisis backend, más rápido)
    2. FlatGeobuf (visualización frontend, streaming)
    3. GeoPackage (fallback, compatibilidad)
    """
    
    def __init__(
        self,
        postgis_config: Optional[Dict] = None,
        gpkg_dir: str = "capas/gpkg",
        fgb_dir: str = "capas/fgb",
        shp_dir: str = "capas/shp"
    ):
        """
        Inicializa el gestor de fuentes de datos
        
        Args:
            postgis_config: Configuración de PostGIS (host, database, user, password)
            gpkg_dir: Directorio con archivos GeoPackage
            fgb_dir: Directorio con archivos FlatGeobuf
            shp_dir: Directorio con Shapefiles
        """
        self.gpkg_dir = Path(gpkg_dir)
        self.fgb_dir = Path(fgb_dir)
        self.shp_dir = Path(shp_dir)
        
        self.postgis = None
        self.postgis_available = False
        self.postgis_config = postgis_config
        
        # Crear directorios si no existen
        self.fgb_dir.mkdir(parents=True, exist_ok=True)
        self.gpkg_dir.mkdir(parents=True, exist_ok=True)
        self.shp_dir.mkdir(parents=True, exist_ok=True)
        
        # Intentar conectar a PostGIS
        if postgis_config:
            self._init_postgis(postgis_config)
        
        logger.info("✅ DataSourceManager inicializado")
        logger.info(f"  📁 FlatGeobuf: {self.fgb_dir}")
        logger.info(f"  📁 GeoPackage: {self.gpkg_dir}")
        logger.info(f"  🗄️  PostGIS: {'✅ Disponible' if self.postgis_available else '❌ No disponible'}")
    
    def _init_postgis(self, config: Dict):
        """Inicializar conexión PostGIS"""
        try:
            from services.postgis_service import PostGISService
            
            self.postgis = PostGISService(
                host=config.get("host", "localhost"),
                database=config.get("database", "GIS"),
                user=config.get("user"),
                password=config.get("password"),
                port=config.get("port", 5432)
            )
            
            # Verificar conexión
            with self.postgis.get_connection() as conn:
                pass
            
            self.postgis_available = True
            logger.info("✅ Conexión PostGIS establecida")
            
        except Exception as e:
            logger.warning(f"⚠️  PostGIS no disponible: {e}")
            self.postgis_available = False
    
    def obtener_capa(
        self,
        nombre_capa: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        formato_preferido: str = "auto"
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Obtiene una capa desde la mejor fuente disponible.
        
        Args:
            nombre_capa: Nombre de la capa
            bbox: Bounding box opcional (minx, miny, maxx, maxy) en EPSG:4326
            formato_preferido: "auto", "postgis", "fgb", "gpkg"
                - "auto": Selecciona automáticamente la mejor fuente
                - "postgis": Fuerza uso de PostGIS (análisis)
                - "fgb": Fuerza uso de FlatGeobuf (visualización)
                - "gpkg": Fuerza uso de GeoPackage (compatibilidad)
        
        Returns:
            GeoDataFrame con la capa o None si no se encuentra
        """
        logger.info(f"🔍 Buscando capa: {nombre_capa} (formato: {formato_preferido})")
        
        # Estrategia según formato preferido
        if formato_preferido == "postgis":
            return self._obtener_desde_postgis(nombre_capa, bbox)
        
        elif formato_preferido == "fgb":
            return self._obtener_desde_fgb(nombre_capa, bbox)
        
        elif formato_preferido == "gpkg":
            return self._obtener_desde_gpkg(nombre_capa)
        
        # Auto: Priorizar según caso de uso
        # 1. PostGIS (si está disponible y no hay bbox específico = análisis)
        if self.postgis_available and bbox is None:
            try:
                gdf = self._obtener_desde_postgis(nombre_capa, bbox)
                if gdf is not None and not gdf.empty:
                    return gdf
            except Exception as e:
                logger.warning(f"  ⚠️  Error con PostGIS: {e}")
        
        # 2. FlatGeobuf (mejor para bbox específicos = visualización)
        try:
            gdf = self._obtener_desde_fgb(nombre_capa, bbox)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.warning(f"  ⚠️  Error con FlatGeobuf: {e}")
        
        # 3. PostGIS (segundo intento si FGB falló)
        if self.postgis_available:
            try:
                gdf = self._obtener_desde_postgis(nombre_capa, bbox)
                if gdf is not None and not gdf.empty:
                    return gdf
            except Exception as e:
                logger.warning(f"  ⚠️  Error con PostGIS: {e}")
        
        # 4. Shapefile (Nuevo fallback)
        try:
            gdf = self._obtener_desde_shp(nombre_capa, bbox)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.warning(f"  ⚠️  Error con Shapefile: {e}")

        # 5. Fallback a GPKG
        return self._obtener_desde_gpkg(nombre_capa)
    
    def _obtener_desde_shp(
        self,
        nombre_capa: str,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Obtiene capa desde archivos Shapefile (.shp).
        """
        # Variaciones posibles
        posibles_nombres = [
            f"{nombre_capa}.shp",
            f"{nombre_capa.lower()}.shp",
            f"{nombre_capa.upper()}.shp"
        ]
        
        for nombre_archivo in posibles_nombres:
            shp_path = self.shp_dir / nombre_archivo
            
            if shp_path.exists():
                try:
                    # GeoPandas lee SHP de forma nativa
                    if bbox:
                        gdf = gpd.read_file(shp_path, bbox=bbox)
                    else:
                        gdf = gpd.read_file(shp_path)
                    
                    # Asegurar EPSG:4326
                    if gdf.crs and gdf.crs.to_epsg() != 4326:
                        gdf = gdf.to_crs("EPSG:4326")
                        
                    logger.info(
                        f"  ✅ {nombre_capa} desde Shapefile "
                        f"({len(gdf):,} features)"
                    )
                    return gdf
                    
                except Exception as e:
                    logger.warning(f"  ⚠️  Error leyendo SHP {shp_path.name}: {e}")
                    continue
                    
        return None

    def _obtener_desde_fgb(
        self,
        nombre_capa: str,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Obtiene capa desde FlatGeobuf con soporte para bbox.
        
        Ventajas de FlatGeobuf:
        - Lectura con bbox sin cargar todo el archivo
        - Índice R-tree integrado
        - Perfecto para visualización web
        """
        # Variaciones posibles del nombre
        posibles_nombres = [
            f"{nombre_capa}.fgb",
            f"{nombre_capa.lower()}.fgb",
            f"{nombre_capa.replace('_', '').lower()}.fgb",
            f"{nombre_capa.replace('_', '-').lower()}.fgb"
        ]
        
        for nombre_archivo in posibles_nombres:
            fgb_path = self.fgb_dir / nombre_archivo
            
            if fgb_path.exists():
                try:
                    # FlatGeobuf soporta bbox nativo (súper eficiente)
                    if bbox:
                        # GeoPandas 0.12+ soporta bbox directamente
                        # Usamos pyogrio si está disponible por velocidad
                        try:
                            gdf = gpd.read_file(
                                fgb_path,
                                bbox=bbox,
                                engine="pyogrio"
                            )
                        except:
                            gdf = gpd.read_file(fgb_path, bbox=bbox)
                    else:
                        try:
                            gdf = gpd.read_file(fgb_path, engine="pyogrio")
                        except:
                            gdf = gpd.read_file(fgb_path)
                    
                    logger.info(
                        f"  ✅ {nombre_capa} desde FlatGeobuf "
                        f"({len(gdf):,} features)"
                    )
                    return gdf
                    
                except Exception as e:
                    logger.warning(f"  ⚠️  Error leyendo {fgb_path.name}: {e}")
                    continue
        
        logger.debug(f"  ❌ {nombre_capa} no encontrado en FlatGeobuf")
        return None
    
    def _obtener_desde_postgis(
        self,
        nombre_capa: str,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Obtiene capa desde PostGIS con filtro espacial opcional.
        
        Ventajas de PostGIS:
        - Índices GIST para consultas espaciales rápidas
        - Soporte completo de SQL
        - Mejor para análisis complejos
        """
        if not self.postgis_available:
            return None
        
        try:
            # Mapeo de nombres a tablas PostGIS
            tabla_map = {
                "rednatura": "biodiversidad:RedNatura",
                "viaspocuarias": "biodiversidad:VP_ViasPecuarias",
                "espaciosnaturales": "biodiversidad:EspaciosNaturalesProtegidos",
                "masasagua": "hidrologia:MasasAgua",
                "zonasinundables": "hidrologia:ZonasInundables",
                "montes": "biodiversidad:MontesPublicos"
            }
            
            tabla = tabla_map.get(nombre_capa.lower())
            if not tabla:
                # Intento directo si el nombre coincide con la tabla
                tabla = nombre_capa
            
            # Construir query con filtro espacial si hay bbox
            if bbox:
                minx, miny, maxx, maxy = bbox
                # Crear geometría del bbox en EPSG:4326
                bbox_wkt = f"POLYGON(({minx} {miny},{maxx} {miny},{maxx} {maxy},{minx} {maxy},{minx} {miny}))"
                
                # Intentamos detectar el esquema public o biodiversidad
                query = f"""
                    SELECT *
                    FROM "{tabla}"
                    WHERE geom && ST_Transform(ST_GeomFromText('{bbox_wkt}', 4326), 25830)
                """
            else:
                query = f'SELECT * FROM "{tabla}"'
            
            # Leer con PostGIS
            with self.postgis.get_connection() as conn:
                gdf = gpd.read_postgis(query, conn, geom_col='geom')
            
            # Asegurar que está en EPSG:4326 para web
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs("EPSG:4326")
            
            logger.info(
                f"  ✅ {nombre_capa} desde PostGIS "
                f"({len(gdf):,} features)"
            )
            return gdf
            
        except Exception as e:
            logger.warning(f"  ⚠️  Error leyendo {nombre_capa} desde PostGIS: {e}")
            return None
    
    def _obtener_desde_gpkg(
        self,
        nombre_capa: str
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Obtiene capa desde GeoPackage (fallback).
        
        Usado cuando PostGIS y FlatGeobuf no están disponibles.
        """
        posibles_nombres = [
            f"{nombre_capa}.gpkg",
            f"{nombre_capa.lower()}.gpkg"
        ]
        
        for nombre_archivo in posibles_nombres:
            gpkg_path = self.gpkg_dir / nombre_archivo
            
            if gpkg_path.exists():
                try:
                    gdf = gpd.read_file(gpkg_path)
                    
                    # Asegurar EPSG:4326
                    if gdf.crs and gdf.crs.to_epsg() != 4326:
                        gdf = gdf.to_crs("EPSG:4326")
                    
                    logger.info(
                        f"  ✅ {nombre_capa} desde GPKG "
                        f"({len(gdf):,} features)"
                    )
                    return gdf
                    
                except Exception as e:
                    logger.warning(f"  ⚠️  Error leyendo {gpkg_path.name}: {e}")
                    continue
        
        logger.warning(f"  ❌ {nombre_capa} no encontrado en ninguna fuente")
        return None
    
    def obtener_url_fgb(self, nombre_capa: str) -> Optional[str]:
        """
        Retorna URL pública del archivo FGB para acceso directo desde frontend.
        
        Args:
            nombre_capa: Nombre de la capa
            
        Returns:
            URL del archivo FGB o None si no existe
        """
        fgb_path = self.fgb_dir / f"{nombre_capa.lower()}.fgb"
        
        if fgb_path.exists():
            return f"/capas/fgb/{nombre_capa.lower()}.fgb"
        
        return None
    
    def listar_capas_disponibles(self) -> Dict[str, List[str]]:
        """
        Lista todas las capas disponibles por fuente.
        
        Returns:
            Diccionario con listas de capas por fuente
        """
        capas = {
            "fgb": [],
            "gpkg": [],
            "shp": [],
            "postgis": []
        }
        
        # FlatGeobuf
        if self.fgb_dir.exists():
            capas["fgb"] = [
                f.stem for f in self.fgb_dir.glob("*.fgb")
            ]
        
        # GeoPackage
        if self.gpkg_dir.exists():
            capas["gpkg"] = [
                f.stem for f in self.gpkg_dir.glob("*.gpkg")
            ]
            
        # Shapefile
        if self.shp_dir.exists():
            capas["shp"] = [
                f.stem for f in self.shp_dir.glob("*.shp")
            ]
        
        # PostGIS
        if self.postgis_available:
            try:
                # Aquí podrías consultar las tablas disponibles
                capas["postgis"] = [
                    "rednatura", "viaspocuarias", "espaciosnaturales",
                    "masasagua", "zonasinundables", "montes"
                ]
            except:
                pass
        
        return capas
    
    def cerrar(self):
        """Cierra conexiones abiertas"""
        if self.postgis:
            try:
                self.postgis.cerrar()
                logger.info("✅ Conexiones PostGIS cerradas")
            except:
                pass
