# Copilot Instructions for GIS API v2.0

## 🎯 Project Overview

**GIS Geospatial Analysis API** - Hybrid FastAPI backend with FlatGeobuf frontend visualization and PostGIS analysis engine. Key innovation: **HTTP Range streaming for 20x faster spatial data loading** compared to traditional formats.

## 🏗️ Architecture Essentials

### Three-Tier Data Strategy
```
Frontend (Browser) → FlatGeobuf (HTTP Range streaming, Leaflet)
Backend (FastAPI) → PostGIS (spatial queries, indices, analysis)
Fallback → GeoPackage/Shapefile (compatibility)
```

**Why this matters:** FlatGeobuf with HTTP Range requests only downloads visible features (e.g., 800 KB of 45 MB file), enabling 0.1s first-feature load vs 2.3s for full GPKG download.

### Core Components
- **[main.py](main.py)** - FastAPI endpoints for layer listing, analysis, static file serving with Range headers
- **[services/data_source_manager.py](services/data_source_manager.py)** - Intelligent source routing (prioritizes PostGIS for backend, FlatGeobuf for frontend)
- **[services/postgis_service.py](services/postgis_service.py)** - PostGIS connection, spatial queries with GIST indices, geometry validation
- **[services/catastro_service.py](services/catastro_service.py)** - Spanish cadastral data fetching, geometry validation, bulk processing
- **[services/analisis_afecciones.py](services/analisis_afecciones.py)** - Environmental impact analysis (spatial intersections, area calculations)
- **[static/js/viewer.js](static/js/viewer.js)** - Leaflet viewer with FlatGeobuf streaming via `flatgeobuf.deserialize()` + HTTP Range requests
- **[templates/](templates/)** - HTML interfaces (main viewer, catastral analysis, environmental analysis)

## 🔌 Critical Patterns & Integration Points

### Data Source Selection Logic
```python
# From data_source_manager.py - requests should check availability in order:
1. PostGIS (if connected) → Best for backend analysis
2. FlatGeobuf file → Best for frontend visualization  
3. GeoPackage → Fallback for compatibility
4. Return None if all unavailable
```

When adding new analysis features: **always call `DataSourceManager.obtener_capa()`** rather than loading files directly. This ensures PostGIS optimizations (spatial indices) are used automatically.

### HTTP Range Request Handling
FlatGeobuf viewer requires `Content-Range` headers. In `main.py`, static file serving:
```python
# Check request.headers.get("range") for partial content requests
# Return FileResponse with status_code=206 and proper Content-Range header
```
This is non-negotiable for performance. Test with browser DevTools "Throttling" to verify Range requests are used.

### Environment Configuration
All connections use `.env` variables (loaded via `python-dotenv`):
```
POSTGIS_HOST, POSTGIS_DATABASE, POSTGIS_USER, POSTGIS_PASSWORD, POSTGIS_PORT
```
**Never hardcode credentials.** Docker containers use environment variables; local development uses `.env` files (see [README.md](README.md) for setup).

## 🛠️ Development Workflows

### Running Locally
```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Start (without PostGIS - optional)
python main.py
# Opens http://localhost:8000

# 3. Verification
python scripts/verify_system.py  # Checks dependencies, FGB files, PostGIS connectivity
```

### Adding New Spatial Layer
1. Place `.fgb` file in `capas/fgb/` (for frontend) and/or `.gpkg`/`.shp` in respective dirs
2. Register in PostGIS: `python scripts/export_postgis_to_fgb.py` (if data lives in DB)
3. Update [main.py](main.py) layer listing endpoint to include new layer name
4. Test via `/api/layers` endpoint

### Adding Analysis Feature
1. Extend `AnalizadorAfecciones` or create new analyzer class in `services/analisis_afecciones.py`
2. Query spatial data via `DataSourceManager.obtener_capa()` with bbox
3. Use `PostGISService` for complex spatial operations (intersections, buffers)
4. Add FastAPI endpoint in `main.py` that calls analyzer
5. Frontend: Add handler in `viewer.js` to POST drawn features to new endpoint

### Docker Deployment
```bash
# Local testing
docker-compose up

# Production (EasyPanel - see DEPLOYMENT.md)
# - Dockerfile builds Python image with GDAL + dependencies
# - Uses gunicorn via start_gunicorn.sh for production
# - Environment variables injected by platform
```

## 📦 Dependencies & System Requirements

**Critical system dependencies** (not pip-installable):
- `gdal-bin` / `libgdal-dev` (geospatial operations) - **must be installed OS-level**
- PostgreSQL + PostGIS (optional, for backend analysis)
- Python 3.10+

**Key Python packages:**
- `fastapi`, `uvicorn` - HTTP server
- `geopandas`, `pyogrio` - Spatial data I/O (pyogrio faster than fiona for FGB)
- `psycopg2-binary`, `geoalchemy2` - PostGIS connection
- `shapely`, `pyproj` - Geometry operations
- `requests` - HTTP fetching (Catastro API calls)
- `Pillow`, `reportlab` - Image/PDF generation

See [requirements.txt](requirements.txt) for pinned versions and notes on GDAL installation.

## 🚀 Troubleshooting Patterns

**FlatGeobuf not loading in browser:**
- Check DevTools Network tab - verify HTTP Range requests (`206 Partial Content`)
- If GET returns 200, Range request support is disabled (check `main.py` static file handler)
- Fallback to PostGIS via `/api/geojson/{layer}` endpoint

**PostGIS connection fails:**
- `DataSourceManager` logs warning and disables PostGIS - backend continues with GPKG/FGB
- Verify `.env` credentials and `POSTGIS_HOST` reachability
- Check DB exists: `psql -U user -d GIS -c "SELECT PostGIS_version();"`

**GDAL import errors:**
- Reinstall: `pip install --upgrade pyogrio` (not fiona - slower)
- If still fails, system GDAL missing - see README.md installation section

## 📝 Code Style & Conventions

- **Logging:** Use `logging.getLogger(__name__)` not print statements
- **Type hints:** Use Python 3.10+ syntax (e.g., `str | None` not `Optional[str]`)
- **Spatial CRS:** All external APIs use EPSG:4326 (WGS84); reproject internally if needed
- **Error handling:** Catch specific exceptions; return JSON errors with status codes >= 400
- **Async:** Use `async def` for I/O-heavy endpoints; sync for compute-heavy (spatial operations)

## 📚 Essential File References

- **Architecture details:** [README.md](README.md) (benchmarks, diagrams)
- **Setup guide:** [QUICKSTART.md](QUICKSTART.md)
- **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md) (EasyPanel, Docker)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Full implementation notes:** [IMPLEMENTATION.md](IMPLEMENTATION.md)

---

**Last Updated:** January 2026 | **Version:** GIS API v2.0
