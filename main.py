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
import os
import logging
import sys

from services.data_source_manager import DataSourceManager
from services.analisis_afecciones import AnalizadorAfecciones, AnalizadorCatastro, generar_informe_afecciones
from services.catastro_service import CatastroCompleteService

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variable de entorno para cache busting
CACHE_BUST = os.getenv("CACHE_BUST", "0")

# Inicializar FastAPI
app = FastAPI(
    title="GIS Analysis API",
    description="API para análisis geoespacial con soporte FlatGeobuf + PostGIS",
    version="3.0.0"
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
        gpkg_dir="/app/capas/gpkg",
        fgb_dir="/app/capas/fgb"
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
# ENDPOINTS DE CONTROL Y VERIFICACIÓN
# =======================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.0.0-Premium"}

@app.get("/api/v1/debug/sync-check")
async def sync_check():
    import datetime
    now = datetime.datetime.now()
    return {
        "status": "synchronized",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "cache_bust": CACHE_BUST,
        "serving_file": "index.html",
        "message": "💎 v3.0 PREMIUM ACTIVADO - Dashboard de Módulos",
        "routes": {
            "/": "Dashboard de Módulos (index.html)",
            "/visor.html": "Visor Catastral 3 Paneles",
            "/gis.html": "Visor GIS FlatGeobuf",
            "/catastro.html": "Módulo de Catastro",
            "/analisis.html": "Análisis de Afecciones"
        },
        "version": "v3.0.0-Premium-" + str(int(now.timestamp()))
    }

@app.get("/api/v1/force-update")
async def force_update():
    """Endpoint para forzar actualización y romper cachés"""
    import datetime
    now = datetime.datetime.now()
    return {
        "status": "force_update_triggered",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "cache_bust": CACHE_BUST,
        "message": "🔄 ACTUALIZACIÓN FORZADA - v3.0 Premium Activa",
        "version": "v3.0.0-Premium-" + str(int(now.timestamp()))
    }

# =======================================================================
# ENDPOINTS DE ANÁLISIS GEOGRÁFICO
# =======================================================================

@app.post("/api/v1/analisis/interseccion")
async def analisis_interseccion(request: Request):
    try:
        data = await request.json()
        geometria = data.get("geometria")
        capas = data.get("capas", ["montes", "urbanismo", "proteccion_ambiental"])
        
        logger.info(f"🔍 Analizando intersección con capas: {capas}")
        
        # Simulación de resultados
        afecciones_simuladas = [
            {
                "capa": "urbanismo",
                "nivel": "ALTO",
                "area_afectada_m2": 1250.50,
                "descripcion": "La parcela intersecta con zona urbana consolidada"
            }
        ] if geometria else []
        
        return {
            "status": "success",
            "afecciones": afecciones_simuladas,
            "timestamp": "2026-01-30T18:15:00"
        }
    except Exception as e:
        logger.error(f"❌ Error en análisis: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/v1/capas/fgb")
async def listar_capas_fgb():
    if not data_manager:
        raise HTTPException(503, "Data Manager no disponible")
    
    fgb_dir = Path(data_manager.fgb_dir)
    if not fgb_dir.exists():
        return {"capas": [], "total": 0}
    
    capas = []
    for fgb_file in sorted(fgb_dir.glob("*.fgb")):
        capas.append({
            "nombre": fgb_file.stem,
            "archivo": fgb_file.name,
            "url": f"/capas/fgb/{fgb_file.name}",
            "size_mb": round(fgb_file.stat().st_size / (1024 * 1024), 2)
        })
    
    return {"capas": capas, "total": len(capas)}

@app.get("/api/v1/capas/disponibles")
async def listar_todas_capas():
    if not data_manager:
        raise HTTPException(503, "Data Manager no disponible")
    return {"fuentes": data_manager.listar_capas_disponibles()}

@app.post("/api/v1/analisis/afecciones")
async def analizar_afecciones(request: Request):
    if not analizador_afecciones:
        raise HTTPException(503, "Analizador no disponible")
    data = await request.json()
    resultado = analizador_afecciones.analizar_parcela(
        geometria_parcela=data.get("geometria_wkt"),
        referencia_catastral=data.get("referencia_catastral")
    )
    return resultado

# =======================================================================
# ENDPOINTS DE CATASTRO
# =======================================================================

@app.get("/api/v1/catastro/{referencia}")
async def consultar_catastro(referencia: str):
    if not catastro_service:
        raise HTTPException(503, "Servicio no disponible")
    return catastro_service.obtener_datos_parcela(referencia)

@app.get("/api/v1/catastro/geometria/{referencia}")
async def obtener_geometria_catastro(referencia: str, formatos: str = "geojson,kml"):
    if not catastro_service:
        raise HTTPException(503, "Servicio no disponible")
    lista_formatos = [f.strip() for f in formatos.split(',')]
    return catastro_service.obtener_geometria(referencia, lista_formatos)

@app.post("/api/v1/catastro/procesar-lote")
async def procesar_lote_catastro(request: Request):
    if not catastro_service:
        raise HTTPException(503, "Servicio no disponible")
    data = await request.json()
    return catastro_service.procesar_lote(
        referencias=data.get("referencias", []),
        capas_analizar=data.get("capas_analizar")
    )

@app.get("/api/v1/catastro/descargar/{lote_id}")
async def descargar_lote_catastro(lote_id: str):
    zip_path = Path(f"descargas_catastro/{lote_id}.zip")
    if not zip_path.exists():
        raise HTTPException(404, "Lote no encontrado")
    return FileResponse(zip_path, media_type="application/zip", filename=f"{lote_id}.zip")

# =======================================================================
# SERVIR FRONTEND Y ESTÁTICOS
# =======================================================================

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.mount("/capas", StaticFiles(directory="/app/capas"), name="capas")

@app.get("/")
async def read_index():
    return FileResponse('templates/index.html')

@app.get("/visor.html")
async def read_visor():
    return FileResponse('templates/visor.html')

@app.get("/gis.html")
async def read_gis():
    return FileResponse('templates/gis.html')

@app.get("/catastro.html")
async def read_catastro():
    return FileResponse('templates/catastro.html')

@app.get("/analisis.html")
async def read_analisis():
    return FileResponse('templates/analisis.html')

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 GIS API v3.0 - Premium Dashboard Ready")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)
