# AI Agent Instructions for GIS API v2.0 - FlatGeobuf + PostGIS

## Project Overview

**GIS API v2.0** is a geospatial analysis platform using a **hybrid architecture**:
- **Frontend**: FlatGeobuf format for streaming visualization (HTTP Range requests, 20x faster than GeoPackage)
- **Backend**: FastAPI + PostGIS for complex spatial analysis with GIST indexes
- **Secondary storage**: GeoPackage/Shapefile fallback formats

This is a production-grade system handling cadastral analysis, environmental impact assessment, and flood risk analysis.

---

## Architecture Deep Dive

### Data Flow Architecture

```
Client Browser
  ↓ (HTTP Range Request)
  → FlatGeobuf File (from /capas/fgb/)
  → Streams only visible bbox (0.1s load)
  
Parallel Analysis API
  ↓ (SQL spatial queries)
  → PostGIS Database (GIST indexed)
  → Complex intersections, buffers, calculations
  ↓ (Fallback)
  → GeoPackage files (if PostGIS unavailable)
```

### Key Design Decisions

1. **FlatGeobuf over GPKG/Shapefile**: Enables HTTP Range requests (load only visible bbox). Benchmark: 0.1s vs 2.3s first feature.
2. **PostGIS for Analysis**: Spatial indexes (GIST) and SQL make server-side calculations 10x faster than client-side.
3. **DataSourceManager Pattern**: Abstracts all data sources (PostGIS/FlatGeobuf/GPKG) behind unified interface with automatic fallback.
4. **Lazy Layer Loading**: Layers are only loaded when first accessed (configuration in `capas/fgb/`, not hardcoded).

---

## Critical File Map

| File | Purpose | When to Edit |
|------|---------|--------------|
| [main.py](main.py) | FastAPI server, all endpoints, request/response models | Adding API routes, analyzing workflows |
| [services/data_source_manager.py](services/data_source_manager.py) | Unified data access layer (PostGIS/FlatGeobuf/GPKG) | Adding data sources, fixing fallback logic |
| [services/postgis_service.py](services/postgis_service.py) | PostGIS connection and spatial SQL queries | Performance tuning, adding GIS operations |
| [services/analisis_afecciones.py](services/analisis_afecciones.py) | Environmental impact analysis (intersection calculations) | Adding new impact layers, changing analysis rules |
| [services/catastro_service.py](services/catastro_service.py) | Cadastral data: fetch, parse, geometry conversion | Extending cadastral features, API changes |
| [scripts/convert_to_fgb.py](scripts/convert_to_fgb.py) | Batch conversion tool (GPKG/SHP → FlatGeobuf) | Adding new input formats, optimization |
| [scripts/verify_system.py](scripts/verify_system.py) | Dependency verification (GDAL, PostGIS, FlatGeobuf driver) | Adding dependency checks |
| [requirements.txt](requirements.txt) | Python dependencies (frozen versions) | Adding packages (but check GDAL compatibility first) |

---

## Common Development Patterns

### Pattern 1: Adding a New Spatial Analysis Layer

```python
# In services/analisis_afecciones.py, add to self.capas_afecciones dict:
'nuevacapa': {
    'nombre': 'Display Name',
    'nivel': 'CRÍTICO|ALTO|MEDIO',  # Impact level
    'descripcion': 'What is this?',
    'restricciones': 'Legal constraints'
}

# Then in main.py POST /api/v1/analisis/afecciones, it auto-detects and analyzes
```

**Why this pattern?** The `AnalizadorAfecciones` uses a configuration dict to dynamically query any layer in PostGIS. Adding a layer requires NO code changes to analysis logic.

### Pattern 2: Retrieving Data with Automatic Fallback

```python
# In any service, DON'T use PostGIS directly:
gdf = data_manager.obtener_capa(
    'rednatura',
    bbox=(minx, miny, maxx, maxy),
    formato_preferido='postgis'  # Will fallback to FlatGeobuf if unavailable
)

# DataSourceManager returns GeoDataFrame regardless of source
# This is CRITICAL for deployment resilience
```

### Pattern 3: Spatial Analysis with PostGIS

```python
# In postgis_service.py, all analysis uses SQL:
SELECT ST_Intersection(a.geom, b.geom) as inteseccion
       ST_Area(ST_Intersection(a.geom, b.geom)) as area_intersectada
FROM capas.rednatura a, capas.zonas_inundables b
WHERE ST_Intersects(a.geom, b.geom);

# GIST indexes auto-speed up ST_Intersects
# Never do geometry operations in Python loop - use batch SQL
```

---

## API Contract & Workflows

### Workflow 1: Frontend Visualization

1. Client requests `GET /api/v1/capas/fgb` → lists all FlatGeobuf files
2. Client directly loads from `/capas/fgb/rednatura.fgb` with HTTP Range
3. Browser uses FlatGeobufLibrary to stream features by bbox
4. **No Python involved** (this is the speed advantage)

### Workflow 2: Backend Analysis (Cadastral Impact Assessment)

1. Client POSTs geometry to `POST /api/v1/analisis/afecciones`
   - Sends WKT geometry + optional reference ID
2. `AnalizadorAfecciones.analizar_parcela()` executes for each configured layer:
   - `data_manager.obtener_capa()` loads layer (PostGIS if available)
   - `PostGISService.calcular_intersecciones()` computes % overlap for each impact type
3. Returns structured JSON with impact level, area percentages, legal restrictions
4. Optional: `generar_informe_afecciones()` creates PDF report

### Workflow 3: Cadastral Data Retrieval

1. Client POSTs cadastral reference to `POST /api/v1/catastro/...`
2. `CatastroCompleteService` fetches from official Spanish cadastral API
3. Parses XML response, extracts geometry (WKT), downloads GML/GeoJSON
4. Converts to multiple formats (DXF, XLSX, PNG)
5. Returns JSON with parcela data + downloadable URLs

---

## Configuration & Deployment

### Environment Variables (from main.py)

```python
POSTGIS_HOST = os.getenv("POSTGIS_HOST", "postgis")      # Docker service name
POSTGIS_DATABASE = os.getenv("POSTGIS_DATABASE", "GIS")
POSTGIS_USER = os.getenv("POSTGIS_USER", "manuel")
POSTGIS_PASSWORD = os.getenv("POSTGIS_PASSWORD", "...")  # Change in production!
POSTGIS_PORT = os.getenv("POSTGIS_PORT", "5432")
CACHE_BUST = os.getenv("CACHE_BUST", "0")                # For frontend JS updates
```

### Docker Deployment

- `docker-compose.yml`: Defines `gis-app` + `postgis` services
- **Important**: `gis-app` depends on `postgis` network; both share `gis-network`
- Gunicorn config: 4 workers, port 80, auto-restart
- Mounted volumes: `/capas/` (layer files), `/descargas_catastro/` (downloads)

### Data Directory Structure

```
capas/
  fgb/          ← FlatGeobuf files (HTTP Range served)
  gpkg/         ← GeoPackage fallback format
  shp/          ← Shapefile fallback format
```

**Naming convention**: Layer names = filename without extension (e.g., `rednatura.fgb` → layer `"rednatura"`)

---

## Performance & Optimization

### Do's
- ✅ Use PostGIS SQL for spatial calculations (10x faster than Python)
- ✅ Cache FlatGeobuf files in HTTP headers (HTTP Range is stateless)
- ✅ Load layers lazily only when requested
- ✅ Use GIST indexes on geometry columns in PostGIS
- ✅ Batch analysis: send one geometry, get all layer intersections

### Don'ts
- ❌ Load entire GPKG files in memory for visualization (use FlatGeobuf instead)
- ❌ Loop over features in Python for spatial math (use PostGIS SQL)
- ❌ Make separate DB query per layer (batch with UNION/JOIN)
- ❌ Assume PostGIS available (implement fallback to GeoPackage)

---

## Testing & Verification

**Always run after changes:**

```bash
# 1. Verify system dependencies
python scripts/verify_system.py
# Checks: GDAL, FlatGeobuf driver, GIST support, layer file integrity

# 2. Run FastAPI server
python main.py
# Automatically initializes DataSourceManager + PostGIS connection

# 3. Test key endpoints (from QUICKSTART.md)
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/capas/disponibles
```

**Common issues & solutions in [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**:
- `ImportError: No module named 'osgeo'` → Install system GDAL
- PostGIS connection timeout → Check docker-compose networking
- FlatGeobuf load slow → Missing HTTP Range support or large bbox

---

## Important Project-Specific Conventions

1. **WKT Geometries**: All geometry exchange uses WKT format (not GeoJSON), enables PostGIS direct processing
2. **EPSG:4326**: All stored/returned data in WGS84 (lat/long) for web compatibility
3. **Async FastAPI**: All endpoints are `async def`, use `await` for I/O-heavy operations
4. **Layer Metadata Dict**: Impact layers defined as configuration dict (not database), enables dynamic querying
5. **HTTP Range Protocol**: FlatGeobuf **requires** server support for Range header; static file mount handles this automatically

---

## When to Consult Each Document

- **README.md**: Architecture overview, benchmarks, feature comparison
- **QUICKSTART.md**: Step-by-step setup, common problems
- **IMPLEMENTATION.md**: Implementation checklist, file inventory
- **DEPLOYMENT.md**: Production setup, Docker, reverse proxy config
- **INTEGRACION_COMPLETA.md**: Full integration test suite examples
- **ANALISIS.md**: Detailed impact analysis layer specifications
- **CATASTRO.md**: Cadastral API details, reference format validation

---

## AI Agent Quick Wins

**To become productive immediately:**

1. Read [main.py](main.py#L104-L150) endpoints section (defines all API routes)
2. Check [DataSourceManager.__init__](services/data_source_manager.py#L19-L65) to understand data source priority
3. Review [AnalizadorAfecciones.capas_afecciones](services/analisis_afecciones.py#L34) dict to understand available impact layers
4. Run `python scripts/verify_system.py` to validate environment

Most bugs involve: data source fallback logic, missing PostGIS indexes, or GDAL driver issues. Check error logs first.

