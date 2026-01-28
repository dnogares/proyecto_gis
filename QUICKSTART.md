# 🚀 QUICKSTART - GIS API v2.0

Guía de inicio rápido para poner en marcha el sistema en **5 minutos**.

## ⚡ Inicio Rápido (5 minutos)

### 1. Instalar dependencias del sistema

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip gdal-bin libgdal-dev

# macOS
brew install python@3.10 gdal

# Verificar
python3 --version
gdalinfo --version
```

### 2. Instalar dependencias Python

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Instalar paquetes
pip install -r requirements.txt
```

### 3. Verificar instalación

```bash
python scripts/verify_system.py
```

**Salida esperada:**
```
✅ GeoPandas: 0.14.2
✅ PyOGRIO: 0.7.2
✅ GDAL: 3.6.2
✅ FlatGeobuf driver disponible
```

### 4. Preparar datos (escoge una opción)

#### Opción A: Desde PostGIS (si tienes)

```bash
# Configurar credenciales en scripts/export_postgis_to_fgb.py
python scripts/export_postgis_to_fgb.py
```

#### Opción B: Convertir GPKG/Shapefile existentes

```bash
# Copiar tus archivos a:
# - capas/gpkg/*.gpkg
# - capas/shp/*.shp

# Convertir
python scripts/convert_to_fgb.py
```

#### Opción C: Usar ogr2ogr manualmente

```bash
ogr2ogr -f FlatGeobuf capas/fgb/miscapas.fgb tu_archivo.gpkg
```

#### Opción D: Descargar datos de ejemplo

```bash
# Ejemplo: Red Natura de MITECO
wget https://www.miteco.gob.es/es/cartografia-y-sig/ide/descargas/biodiversidad/red-natura-2000.zip
unzip red-natura-2000.zip -d temp/
ogr2ogr -f FlatGeobuf capas/fgb/rednatura.fgb temp/RedNatura2000.shp
```

### 5. Iniciar servidor

```bash
python main.py
```

**Salida esperada:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     ✅ Data Manager inicializado
INFO:     📊 Capas FlatGeobuf disponibles: 5
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6. Abrir navegador

```
http://localhost:8000
```

¡Listo! El visor debería mostrar el mapa con controles de capas.

---

## 📋 Checklist Pre-vuelo

Antes de iniciar, verifica:

- [ ] Python 3.10+ instalado
- [ ] GDAL instalado y funcionando
- [ ] Dependencias Python instaladas (`pip list | grep geopandas`)
- [ ] Al menos 1 archivo .fgb en `capas/fgb/`
- [ ] Puerto 8000 disponible
- [ ] Navegador moderno (Chrome/Firefox/Edge)

---

## 🔧 Solución de Problemas Comunes

### Error: "ModuleNotFoundError: No module named 'geopandas'"

```bash
pip install -r requirements.txt
```

### Error: "GDAL not found"

```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev

# macOS
brew install gdal

# Verificar
python -c "from osgeo import gdal; print(gdal.__version__)"
```

### Error: "No se pueden cargar capas en el frontend"

1. Verificar que hay archivos .fgb:
   ```bash
   ls -lh capas/fgb/*.fgb
   ```

2. Verificar endpoint API:
   ```bash
   curl http://localhost:8000/api/v1/capas/fgb
   ```

3. Abrir consola del navegador (F12) y buscar errores

### Error: "flatgeobuf is not defined" en navegador

Verificar que el script está cargado en `templates/index.html`:
```html
<script src="https://unpkg.com/flatgeobuf@3.27.2/dist/flatgeobuf-geojson.min.js"></script>
```

### FlatGeobuf muy lento

1. Verificar que HTTP Range está habilitado:
   ```bash
   curl -I http://localhost:8000/capas/fgb/tuarchivo.fgb | grep Accept-Ranges
   # Debe mostrar: Accept-Ranges: bytes
   ```

2. Simplificar geometrías si son muy complejas:
   ```bash
   ogr2ogr -f FlatGeobuf -simplify 0.0001 \
       capas/fgb/simple.fgb \
       capas/fgb/complejo.fgb
   ```

---

## 🎯 Próximos Pasos

Una vez funcionando:

### Configurar PostGIS (opcional)

```bash
# Instalar PostgreSQL + PostGIS
sudo apt-get install postgresql postgresql-contrib postgis

# Crear base de datos
sudo -u postgres psql -c "CREATE DATABASE GIS;"
sudo -u postgres psql -d GIS -c "CREATE EXTENSION postgis;"

# Importar capas
shp2pgsql -I -s 25830 capas/shp/miscapas.shp public.miscapas | \
    psql -h localhost -U manuel -d GIS
```

### Personalizar capas

Editar `static/js/viewer.js` para añadir tus capas:

```javascript
const capasDefecto = [
    'rednatura',
    'viaspocuarias',
    'tu_capa_custom'  // Añadir aquí
];

this.colors = {
    rednatura: '#2E7D32',
    viaspocuarias: '#F57C00',
    tu_capa_custom: '#FF0000'  // Añadir aquí
};
```

### Añadir análisis personalizado

Crear endpoint en `main.py`:

```python
@app.post("/api/v1/analisis/mi-analisis")
async def mi_analisis(request: Dict):
    # Tu lógica aquí
    gdf = data_manager.obtener_capa(
        "rednatura",
        formato_preferido="postgis"  # Usa PostGIS para análisis
    )
    
    # Hacer cálculos...
    resultado = gdf.area.sum()
    
    return {"area_total": resultado}
```

### Deploy en producción

```bash
# Usar gunicorn + uvicorn workers
pip install gunicorn

gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

---

## 📞 Obtener Ayuda

### Scripts útiles

```bash
# Ver info de archivos FGB
python -c "
import fiona
with fiona.open('capas/fgb/tuarchivo.fgb') as src:
    print(f'Features: {len(src)}')
    print(f'CRS: {src.crs}')
    print(f'Bounds: {src.bounds}')
"

# Listar drivers GDAL disponibles
python -c "
from osgeo import gdal
for i in range(gdal.GetDriverCount()):
    print(gdal.GetDriver(i).ShortName)
" | grep -i geo
```

### Logs

Ver logs detallados:

```bash
# Iniciar con debug
python main.py --log-level debug

# Ver solo errores
python main.py 2>&1 | grep ERROR
```

### Documentación adicional

- **README.md**: Documentación completa
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **FlatGeobuf**: https://flatgeobuf.org/
- **GeoPandas**: https://geopandas.org/

---

## ✅ Verificación Final

Para verificar que todo funciona:

```bash
# 1. Sistema
python scripts/verify_system.py

# 2. API
curl http://localhost:8000/health

# 3. Capas FGB
curl http://localhost:8000/api/v1/capas/fgb

# 4. Frontend
# Abrir http://localhost:8000 y activar una capa
```

Si todos los checks pasan: **¡Estás listo! 🎉**

---

**¿Problemas?** Abre un issue en GitHub o revisa los logs en detalle.

**¿Funciona perfecto?** ¡Disfruta de 20x más velocidad con FlatGeobuf! 🚀
