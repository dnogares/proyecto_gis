"""
FastAPI Backend con soporte híbrido PostGIS + FlatGeobuf

Arquitectura:
- Frontend: Carga FlatGeobuf directamente (HTTP Range, streaming)
- Backend: Usa PostGIS para análisis (índices GIST, SQL)
- Servir: Archivos .fgb estáticos con soporte HTTP Range
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from typing import Optional, List, Dict
import logging

from services.data_source_manager import DataSourceManager
from services.analisis_afecciones import AnalizadorAfecciones, AnalizadorCatastro, generar_informe_afecciones
from services.catastro_service import CatastroCompleteService

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="GIS Analysis API",
    description="API para análisis geoespacial con soporte FlatGeobuf + PostGIS",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración PostGIS
# Configuración de PostGIS
# Usar variables de entorno en producción
import os
from dotenv import load_dotenv

load_dotenv()

POSTGIS_CONFIG = {
    "host": os.getenv("POSTGIS_HOST", "postgis"),
    "database": os.getenv("POSTGIS_DATABASE", "GIS"),
    "user": os.getenv("POSTGIS_USER", "manuel"),
    "password": os.getenv("POSTGIS_PASSWORD", "Aa123456"),
    "port": int(os.getenv("POSTGIS_PORT", "5432")),
    "client_encoding": "utf8",
    "options": "-c client_encoding=UTF8"
}

# Inicializar Data Manager
try:
    data_manager = DataSourceManager(
        postgis_config=POSTGIS_CONFIG,
        gpkg_dir="capas/gpkg",
        fgb_dir="capas/fgb"
    )
    logger.info("✅ Data Manager inicializado")
    
    # Inicializar analizadores
    analizador_afecciones = AnalizadorAfecciones(data_manager)
    analizador_catastro = AnalizadorCatastro()
    logger.info("✅ Analizadores inicializados")
    
    # Inicializar servicio COMPLETO de Catastro
    catastro_service = CatastroCompleteService(
        output_dir="descargas_catastro",
        data_manager=data_manager,
        cache_enabled=True
    )
    logger.info("✅ Servicio completo de Catastro inicializado")
    
except Exception as e:
    logger.error(f"❌ Error inicializando Data Manager: {e}")
    data_manager = None
    analizador_afecciones = None
    analizador_catastro = None
    catastro_service = None



# =======================================================================
# ENDPOINTS PARA FLATGEOBUF
# ============================================================================

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/capas/fgb")
async def listar_capas_fgb():
    """
    Lista todas las capas FlatGeobuf disponibles con metadatos.
    
    Útil para que el frontend sepa qué capas puede cargar directamente.
    
    Returns:
        JSON con lista de capas y sus metadatos
    """
    if not data_manager:
        raise HTTPException(503, "Data Manager no disponible")
    
    fgb_dir = Path(data_manager.fgb_dir)
    
    if not fgb_dir.exists():
        return {"capas": [], "total": 0}
    
    capas = []
    
    for fgb_file in sorted(fgb_dir.glob("*.fgb")):
        try:
            # Obtener metadatos sin cargar todo el archivo
            import fiona
            
            with fiona.open(fgb_file) as src:
                bounds = src.bounds
                crs = src.crs
                count = len(src)
                schema = src.schema
            
            capas.append({
                "nombre": fgb_file.stem,
                "archivo": fgb_file.name,
                "url": f"/capas/fgb/{fgb_file.name}",
                "features": count,
                "bbox": list(bounds),
                "crs": str(crs),
                "tipo_geometria": schema.get('geometry', 'Unknown'),
                "campos": list(schema.get('properties', {}).keys()),
                "size_mb": round(fgb_file.stat().st_size / (1024 * 1024), 2)
            })
            
        except Exception as e:
            logger.warning(f"Error leyendo metadatos de {fgb_file.name}: {e}")
            # Info básica si falla
            capas.append({
                "nombre": fgb_file.stem,
                "archivo": fgb_file.name,
                "url": f"/capas/fgb/{fgb_file.name}",
                "size_mb": round(fgb_file.stat().st_size / (1024 * 1024), 2)
            })
    
    return {
        "capas": capas,
        "total": len(capas),
        "directorio": str(fgb_dir)
    }


@app.get("/api/v1/capas/{nombre_capa}/fgb-info")
async def info_capa_fgb(nombre_capa: str):
    """
    Retorna información detallada de una capa FlatGeobuf específica.
    
    Args:
        nombre_capa: Nombre de la capa (sin extensión)
        
    Returns:
        JSON con metadatos completos de la capa
    """
    if not data_manager:
        raise HTTPException(503, "Data Manager no disponible")
    
    fgb_path = data_manager.fgb_dir / f"{nombre_capa}.fgb"
    
    if not fgb_path.exists():
        raise HTTPException(404, f"Capa FGB '{nombre_capa}' no encontrada")
    
    try:
        import fiona
        
        with fiona.open(fgb_path) as src:
            info = {
                "nombre": nombre_capa,
                "url": f"/capas/fgb/{nombre_capa}.fgb",
                "features": len(src),
                "bbox": list(src.bounds),
                "crs": str(src.crs),
                "schema": dict(src.schema),
                "campos": list(src.schema['properties'].keys()),
                "tipo_geometria": src.schema['geometry'],
                "size_mb": round(fgb_path.stat().st_size / (1024 * 1024), 2)
            }
            
            # Ejemplo de features (primeros 3)
            features_sample = []
            for i, feature in enumerate(src):
                if i >= 3:
                    break
                features_sample.append({
                    "properties": feature['properties'],
                    "geometry_type": feature['geometry']['type']
                })
            
            info["ejemplos"] = features_sample
            
            return info
            
    except Exception as e:
        raise HTTPException(500, f"Error leyendo capa: {str(e)}")


@app.get("/api/v1/capas/disponibles")
async def listar_todas_capas():
    """
    Lista todas las capas disponibles en todas las fuentes.
    
    Returns:
        JSON con capas por fuente (FlatGeobuf, PostGIS, GPKG)
    """
    if not data_manager:
        raise HTTPException(503, "Data Manager no disponible")
    
    capas = data_manager.listar_capas_disponibles()
    
    return {
        "fuentes": capas,
        "total_fgb": len(capas.get("fgb", [])),
        "total_gpkg": len(capas.get("gpkg", [])),
        "total_postgis": len(capas.get("postgis", [])),
        "recomendacion": "Usa FlatGeobuf para visualización web (más rápido)"
    }


# ============================================================================
# ENDPOINTS PARA ANÁLISIS (Backend usa PostGIS)
# ============================================================================

from pydantic import BaseModel


class AnalisisRequest(BaseModel):
    """Request para análisis de afecciones"""
    nombre_capa: str
    bbox: Optional[List[float]] = None  # [minx, miny, maxx, maxy]
    geometria_wkt: Optional[str] = None


@app.post("/api/v1/analisis/obtener-capa")
async def obtener_capa_para_analisis(request: AnalisisRequest):
    """
    Obtiene una capa para análisis backend.
    
    IMPORTANTE: Este endpoint usa PostGIS (más rápido para análisis)
    El frontend debería usar FlatGeobuf directamente.
    
    Args:
        request: Nombre de capa y filtros opcionales
        
    Returns:
        GeoJSON de la capa
    """
    if not data_manager:
        raise HTTPException(503, "Data Manager no disponible")
    
    # Convertir bbox si existe
    bbox_tuple = None
    if request.bbox and len(request.bbox) == 4:
        bbox_tuple = tuple(request.bbox)
    
    # Obtener capa (prioriza PostGIS para análisis)
    gdf = data_manager.obtener_capa(
        request.nombre_capa,
        bbox=bbox_tuple,
        formato_preferido="postgis" if data_manager.postgis_available else "auto"
    )
    
    if gdf is None or gdf.empty:
        raise HTTPException(404, f"Capa '{request.nombre_capa}' no encontrada")
    
    # Retornar como GeoJSON
    return JSONResponse(
        content=gdf.to_json(),
        media_type="application/geo+json"
    )


@app.post("/api/v1/analisis/interseccion")
async def calcular_interseccion(request: Dict):
    """
    Calcula intersección entre geometría y capas.
    
    Ejemplo de uso del backend para análisis complejos.
    """
    if not data_manager:
        raise HTTPException(503, "Data Manager no disponible")
    
    # Aquí iría la lógica de intersección usando PostGIS
    # Ver implementación completa en el proyecto original
    
    return {
        "message": "Endpoint de ejemplo - implementar lógica de intersección",
        "nota": "Este análisis usa PostGIS para máxima velocidad"
    }


# ============================================================================
# ENDPOINTS DE ANÁLISIS DE AFECCIONES
# ============================================================================

class AfeccionesRequest(BaseModel):
    """Request para análisis de afecciones"""
    geometria_wkt: str
    referencia_catastral: Optional[str] = None


@app.post("/api/v1/analisis/afecciones")
async def analizar_afecciones(request: AfeccionesRequest):
    """
    Analiza afecciones ambientales y urbanísticas de una parcela.
    
    Este endpoint realiza un análisis completo de:
    - Red Natura 2000
    - Espacios Naturales Protegidos
    - Vías Pecuarias
    - Zonas Inundables
    - Masas de Agua
    
    Args:
        request: Geometría WKT de la parcela y ref. catastral opcional
        
    Returns:
        Análisis completo de afecciones con recomendaciones
    """
    if not analizador_afecciones:
        raise HTTPException(503, "Analizador de afecciones no disponible")
    
    try:
        logger.info(f"📊 Iniciando análisis de afecciones...")
        
        # Realizar análisis
        resultado = analizador_afecciones.analizar_parcela(
            geometria_parcela=request.geometria_wkt,
            referencia_catastral=request.referencia_catastral
        )
        
        logger.info(f"✅ Análisis completado: {resultado['num_afecciones']} afecciones")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de afecciones: {e}")
        raise HTTPException(500, f"Error en análisis: {str(e)}")


@app.post("/api/v1/analisis/afecciones/informe")
async def generar_informe(request: AfeccionesRequest):
    """
    Genera informe en texto plano de afecciones.
    
    Args:
        request: Geometría WKT de la parcela y ref. catastral opcional
        
    Returns:
        Informe en texto plano
    """
    if not analizador_afecciones:
        raise HTTPException(503, "Analizador de afecciones no disponible")
    
    try:
        # Realizar análisis
        resultado = analizador_afecciones.analizar_parcela(
            geometria_parcela=request.geometria_wkt,
            referencia_catastral=request.referencia_catastral
        )
        
        # Generar informe
        informe = generar_informe_afecciones(resultado)
        
        return {
            "informe": informe,
            "resultado": resultado
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando informe: {e}")
        raise HTTPException(500, f"Error generando informe: {str(e)}")


# ============================================================================
# ENDPOINTS DE CATASTRO
# ============================================================================

@app.get("/api/v1/catastro/{referencia_catastral}")
async def consultar_catastro(referencia_catastral: str):
    """
    Consulta datos catastrales de una parcela.
    
    Args:
        referencia_catastral: Referencia catastral de la parcela
        
    Returns:
        Datos catastrales de la parcela
    """
    if not analizador_catastro:
        raise HTTPException(503, "Analizador de catastro no disponible")
    
    try:
        datos = analizador_catastro.obtener_datos_parcela(referencia_catastral)
        return datos
        
    except Exception as e:
        logger.error(f"❌ Error consultando catastro: {e}")
        raise HTTPException(500, f"Error consultando catastro: {str(e)}")


class AnalisisCompletoRequest(BaseModel):
    """Request para análisis completo (catastro + afecciones)"""
    referencia_catastral: str
    geometria_wkt: str


@app.post("/api/v1/analisis/completo")
async def analisis_completo(request: AnalisisCompletoRequest):
    """
    Análisis completo: catastro + afecciones.
    
    Combina datos catastrales con análisis de afecciones ambientales
    para obtener un informe completo de la parcela.
    
    Args:
        request: Referencia catastral y geometría WKT
        
    Returns:
        Análisis completo con datos catastrales y afecciones
    """
    if not analizador_afecciones or not analizador_catastro:
        raise HTTPException(503, "Analizadores no disponibles")
    
    try:
        logger.info(f"📊 Análisis completo para {request.referencia_catastral}")
        
        # Obtener datos catastrales
        datos_catastro = analizador_catastro.obtener_datos_parcela(
            request.referencia_catastral
        )
        
        # Analizar afecciones
        resultado_afecciones = analizador_afecciones.analizar_parcela(
            geometria_parcela=request.geometria_wkt,
            referencia_catastral=request.referencia_catastral
        )
        
        # Combinar resultados
        return {
            "referencia_catastral": request.referencia_catastral,
            "datos_catastro": datos_catastro,
            "analisis_afecciones": resultado_afecciones,
            "informe": generar_informe_afecciones(resultado_afecciones)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en análisis completo: {e}")
        raise HTTPException(500, f"Error en análisis completo: {str(e)}")


# ============================================================================
# ENDPOINTS DE UTILIDAD PARA ANÁLISIS
# ============================================================================

@app.post("/api/v1/geometria/validar")
async def validar_geometria(geometria_wkt: str = None):
    """
    Valida una geometría WKT.
    
    Args:
        geometria_wkt: Geometría en formato WKT
        
    Returns:
        Validación y estadísticas de la geometría
    """
    if not geometria_wkt:
        raise HTTPException(400, "geometria_wkt es requerido")
    
    try:
        from shapely import wkt
        import geopandas as gpd
        
        # Parsear WKT
        geom = wkt.loads(geometria_wkt)
        
        # Validar
        es_valida = geom.is_valid
        
        # Calcular estadísticas
        gdf = gpd.GeoDataFrame({'geometry': [geom]}, crs='EPSG:4326')
        gdf_utm = gdf.to_crs('EPSG:25830')
        
        area_m2 = gdf_utm.geometry.area.sum()
        perimetro_m = gdf_utm.geometry.length.sum()
        bounds = geom.bounds
        
        return {
            "valida": es_valida,
            "tipo_geometria": geom.geom_type,
            "area_m2": round(area_m2, 2),
            "perimetro_m": round(perimetro_m, 2),
            "bbox": {
                "minx": bounds[0],
                "miny": bounds[1],
                "maxx": bounds[2],
                "maxy": bounds[3]
            },
            "centroide": {
                "lon": geom.centroid.x,
                "lat": geom.centroid.y
            }
        }
        
    except Exception as e:
        raise HTTPException(400, f"Error validando geometría: {str(e)}")



# ============================================================================
# ENDPOINTS DE CATASTRO COMPLETO - INTEGRADO
# ============================================================================

class CatastroValidarRequest(BaseModel):
    """Request para validar referencia"""
    referencia: str


class CatastroLoteRequest(BaseModel):
    """Request para procesar lote"""
    referencias: List[str]
    capas_analizar: Optional[List[str]] = None


class CatastroAfeccionesRequest(BaseModel):
    """Request para análisis de afecciones"""
    referencia: str
    capas_analizar: Optional[List[str]] = None


@app.post("/api/v1/catastro/validar")
async def validar_referencia_catastral(request: CatastroValidarRequest):
    """
    Valida una referencia catastral.
    
    Comprueba:
    - Formato correcto (16-Jorge)
    - Existencia en Catastro (17-Jorge)
    
    Args:
        request: Referencia a validar
        
    Returns:
        Resultado de validación
    """
    if not catastro_service:
        raise HTTPException(503, "Servicio de Catastro no disponible")
    
    try:
        resultado = catastro_service.validar_referencia(request.referencia)
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error validando referencia: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@app.post("/api/v1/catastro/validar-lote")
async def validar_lote_referencias(referencias: List[str]):
    """
    Valida un lote de referencias catastrales.
    
    Args:
        referencias: Lista de referencias
        
    Returns:
        Estadísticas de validación (válidas, inválidas, duplicadas)
    """
    if not catastro_service:
        raise HTTPException(503, "Servicio de Catastro no disponible")
    
    try:
        resultado = catastro_service.validar_lote(referencias)
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error validando lote: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/api/v1/catastro/datos/{referencia}")
async def obtener_datos_catastro(referencia: str):
    """
    Obtiene datos completos de una parcela catastral.
    
    Incluye:
    - Coordenadas (WGS84 + UTM)
    - Superficie de parcela
    - Superficie construida
    - Uso principal
    - Año construcción
    - Dirección
    - Provincia/Municipio
    
    Args:
        referencia: Referencia catastral
        
    Returns:
        Datos completos de la parcela
    """
    if not catastro_service:
        raise HTTPException(503, "Servicio de Catastro no disponible")
    
    try:
        datos = catastro_service.obtener_datos_parcela(referencia)
        return datos
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/api/v1/catastro/geometria/{referencia}")
async def obtener_geometria_catastro(
    referencia: str,
    formatos: str = "geojson,kml"
):
    """
    Obtiene geometría de una parcela en múltiples formatos.
    
    Formatos disponibles:
    - geojson: GeoJSON estándar
    - kml: Google Earth
    - gml: Catastro oficial
    - dxf: AutoCAD
    - xlsx: Excel con vértices
    - txt: Texto con vértices
    - png: Imagen del mapa
    
    Args:
        referencia: Referencia catastral
        formatos: Formatos separados por comas
        
    Returns:
        Geometría en formatos solicitados
    """
    if not catastro_service:
        raise HTTPException(503, "Servicio de Catastro no disponible")
    
    try:
        lista_formatos = [f.strip() for f in formatos.split(',')]
        resultado = catastro_service.obtener_geometria(referencia, lista_formatos)
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo geometría: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@app.post("/api/v1/catastro/afecciones")
async def analizar_afecciones_catastro(request: CatastroAfeccionesRequest):
    """
    Analiza afecciones de una parcela catastral.
    
    Calcula intersección con capas:
    - Red Natura 2000
    - Vías Pecuarias
    - Montes Públicos
    - Espacios Naturales Protegidos
    - Zonas Inundables
    - Masas de Agua
    
    Devuelve:
    - % de afección por capa
    - Área afectada (m²)
    - Mapa con afecciones dibujadas
    
    Args:
        request: Referencia y capas a analizar
        
    Returns:
        Análisis completo de afecciones
    """
    if not catastro_service:
        raise HTTPException(503, "Servicio de Catastro no disponible")
    
    try:
        resultado = catastro_service.analizar_afecciones(
            ref=request.referencia,
            capas_analizar=request.capas_analizar
        )
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error analizando afecciones: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/api/v1/catastro/urbanismo/{referencia}")
async def consultar_urbanismo_catastro(referencia: str):
    """
    Consulta urbanística de una parcela.
    
    Obtiene:
    - Clasificación de suelo (% urbano, no urbanizable, etc.)
    - Calificación urbanística
    - Planeamiento vigente
    - Ficha urbanística (si disponible)
    
    Args:
        referencia: Referencia catastral
        
    Returns:
        Información urbanística
    """
    if not catastro_service:
        raise HTTPException(503, "Servicio de Catastro no disponible")
    
    try:
        resultado = catastro_service.consultar_urbanismo(referencia)
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error consultando urbanismo: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@app.post("/api/v1/catastro/procesar-lote")
async def procesar_lote_catastro(request: CatastroLoteRequest):
    """
    Procesa un lote de referencias catastrales.
    
    Genera:
    - Validación de todas las RC
    - Datos de cada parcela
    - Geometrías en todos los formatos
    - Análisis de afecciones
    - Mapa del conjunto
    - Excel con resumen (coordenadas, superficies)
    - ZIP con toda la documentación
    
    Args:
        request: Lista de referencias y opciones
        
    Returns:
        Ruta del ZIP y estadísticas
    """
    if not catastro_service:
        raise HTTPException(503, "Servicio de Catastro no disponible")
    
    try:
        logger.info(f"📦 Procesando lote: {len(request.referencias)} referencias")
        
        resultado = catastro_service.procesar_lote(
            referencias=request.referencias,
            capas_analizar=request.capas_analizar
        )
        
        logger.info(f"✅ Lote procesado: {resultado.get('exitosas', 0)}/{len(request.referencias)}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error procesando lote: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/api/v1/catastro/descargar/{lote_id}")
async def descargar_lote_catastro(lote_id: str):
    """
    Descarga ZIP de un lote procesado.
    
    Args:
        lote_id: ID del lote
        
    Returns:
        Archivo ZIP
    """
    try:
        zip_path = Path(f"descargas_catastro/{lote_id}.zip")
        
        if not zip_path.exists():
            raise HTTPException(404, "Lote no encontrado")
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{lote_id}.zip"
        )
        
    except Exception as e:
        logger.error(f"❌ Error descargando lote: {e}")
        raise HTTPException(500, f"Error: {str(e)}")



# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/capas", StaticFiles(directory="capas"), name="capas")

@app.get("/")
async def read_index():
    return FileResponse('templates/index.html')

@app.get("/catastro.html")
async def read_catastro():
    return FileResponse('templates/catastro.html')

@app.get("/analisis.html")
async def read_analisis():
    return FileResponse('templates/analisis.html')

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar"""
    logger.info("=" * 70)
    logger.info("🚀 GIS API v2.0 - FlatGeobuf + PostGIS")
    logger.info("=" * 70)
    
    if data_manager:
        capas = data_manager.listar_capas_disponibles()
        logger.info(f"📊 Capas FlatGeobuf disponibles: {len(capas.get('fgb', []))}")
        logger.info(f"📊 Capas PostGIS disponibles: {len(capas.get('postgis', []))}")
        logger.info(f"📊 Capas GPKG disponibles: {len(capas.get('gpkg', []))}")
    
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al apagar"""
    if data_manager:
        data_manager.cerrar()
    logger.info("👋 Servidor detenido")


if __name__ == "__main__":
    import os
    import sys
    import logging
    import multiprocessing

    # Configuración desde variables de entorno
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "80"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    
    # Determinar número de workers
    MAX_WORKERS = 4
    WORKERS = int(os.getenv("WORKERS", str(min(MAX_WORKERS, max(2, multiprocessing.cpu_count() or 2)))))
    
    try:
        if DEBUG:
            # Modo desarrollo: Uvicorn con reload
            logger.info("🔧 Modo DESARROLLO: Uvicorn con reload")
            import uvicorn
            uvicorn.run(
                "main:app",
                host=HOST,
                port=PORT,
                reload=True,
                log_level=LOG_LEVEL
            )
        else:
            # Modo producción: intentar Gunicorn, fallback a Uvicorn
            try:
                logger.info(f"🚀 Modo PRODUCCIÓN: usando Gunicorn con {WORKERS} workers")
                
                # Ejecutar Gunicorn
                cmd = [
                    "gunicorn",
                    "-k", "uvicorn.workers.UvicornWorker",
                    "-w", str(WORKERS),
                    "-b", f"{HOST}:{PORT}",
                    "--timeout", "120",
                    "--graceful-timeout", "30",
                    "--log-level", LOG_LEVEL,
                    "--access-logfile", "-",
                    "--error-logfile", "-",
                    "main:app"
                ]
                
                os.execvp("gunicorn", cmd)
                
            except FileNotFoundError:
                # Gunicorn no disponible, usar Uvicorn
                logger.warning("⚠️ Gunicorn no encontrado, usando Uvicorn con workers")
                import uvicorn
                uvicorn.run(
                    "main:app",
                    host=HOST,
                    port=PORT,
                    workers=WORKERS,
                    log_level=LOG_LEVEL
                )
    
    except Exception as e:
        logging.exception(f"❌ Error arrancando el servidor: {e}")
        sys.exit(1)

