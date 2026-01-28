# 📄 Guía Completa del Sistema de Catastro

## 🎯 Descripción General

Sistema completo e integrado de descarga y procesamiento de documentación catastral con las siguientes capacidades:

### ✅ Funcionalidades Implementadas

1. **Descarga de GML** (Geometrías oficiales)
2. **Datos Alfanuméricos** (Superficies, usos, año construcción)
3. **Plano Catastral** (Imagen WMS del plano oficial)
4. **Ortofoto PNOA** (Imagen aérea de alta resolución)
5. **Composición Plano + Ortofoto** con mezcla visual
6. **Contornos Dibujados** en rojo sobre todas las imágenes
7. **PDF Oficial del Catastro**
8. **Archivo KML** para Google Earth
9. **Capas de Afecciones** (planeamiento, protecciones)
10. **Ortofotos de Contexto** (provincial, autonómico, nacional)
11. **Informe PDF Completo** con todas las imágenes
12. **Procesamiento por Lotes** con hasta 3 workers paralelos
13. **Resumen CSV** con coordenadas y superficies
14. **Cache HTTP** (1 hora) para mayor velocidad
15. **Validación de Referencias** Catastrales

---

## 🚀 Uso Rápido

### Interfaz Web

```
http://localhost:8000/catastro.html
```

#### Referencia Individual:
1. Introducir referencia catastral
2. Marcar opciones (afecciones, ZIP)
3. Click en "Descargar Documentación"
4. Descargar ZIP generado

#### Lote de Referencias:
1. Pegar lista de referencias (una por línea)
2. Click en "Descargar Lote"
3. Descargar ZIP de lote con resumen CSV

---

## 📚 API REST

### 1. Descargar Documentación Completa

**POST** `/api/v1/catastro/descargar`

```bash
curl -X POST http://localhost:8000/api/v1/catastro/descargar \
  -H "Content-Type: application/json" \
  -d '{
    "referencia": "30037A008002060000UZ",
    "descargar_afecciones": true,
    "crear_zip": true
  }'
```

**Response:**
```json
{
  "referencia": "30037A008002060000UZ",
  "exitosa": true,
  "coordenadas": {
    "lon": -2.4597,
    "lat": 36.8381,
    "srs": "EPSG:4326",
    "fuente": "JSON"
  },
  "parcela_gml": true,
  "edificio_gml": false,
  "plano_ortofoto": {
    "plano_catastro": true,
    "ortofoto_pnoa": true,
    "composicion": true
  },
  "pdf_oficial": true,
  "kml": true,
  "capas_afecciones": true,
  "ortofoto_provincial": true,
  "ortofoto_autonomico": true,
  "ortofoto_nacional": true,
  "contorno_superpuesto": true,
  "informe_pdf": true,
  "zip_generado": true,
  "zip_path": "descargas_catastro/30037A008002060000UZ_completo.zip"
}
```

### 2. Descargar Lote

**POST** `/api/v1/catastro/descargar-lote`

```bash
curl -X POST http://localhost:8000/api/v1/catastro/descargar-lote \
  -H "Content-Type: application/json" \
  -d '{
    "referencias": [
      "30037A008002060000UZ",
      "30037A008002070000UZ",
      "30037A008002080000UZ"
    ],
    "descargar_afecciones": true
  }'
```

**Response:**
```json
{
  "exitosa": true,
  "zip_path": "descargas_catastro/lote_20260128_1430_3_refs.zip",
  "zip_size_mb": 45.3,
  "total_referencias": 3,
  "mensaje": "Lote procesado correctamente. ZIP: lote_20260128_1430_3_refs.zip"
}
```

### 3. Obtener Coordenadas

**GET** `/api/v1/catastro/coordenadas/{referencia}`

```bash
curl http://localhost:8000/api/v1/catastro/coordenadas/30037A008002060000UZ
```

**Response:**
```json
{
  "referencia": "30037A008002060000UZ",
  "wgs84": {
    "lon": -2.4597,
    "lat": 36.8381,
    "srs": "EPSG:4326"
  },
  "utm": {
    "x": 549123.45,
    "y": 4078567.89,
    "huso": 30,
    "srs": "EPSG:25830"
  },
  "fuente": "JSON"
}
```

### 4. Descargar GML

**GET** `/api/v1/catastro/gml/{referencia}`

```bash
curl http://localhost:8000/api/v1/catastro/gml/30037A008002060000UZ \
  -o parcela.gml
```

### 5. Descargar PDF Oficial

**GET** `/api/v1/catastro/pdf/{referencia}`

```bash
curl http://localhost:8000/api/v1/catastro/pdf/30037A008002060000UZ \
  -o catastro.pdf
```

### 6. Validar Referencia

**GET** `/api/v1/catastro/validar/{referencia}`

```bash
curl http://localhost:8000/api/v1/catastro/validar/30037A008002060000UZ
```

**Response:**
```json
{
  "valida": true,
  "referencia_original": "30037A008002060000UZ",
  "referencia_limpia": "30037A008002060000UZ",
  "referencia_formateada": "3003 7A0 08002 0600 00UZ",
  "componentes": {
    "parcela": "3003 7A0",
    "hoja": "08",
    "subparcela": "00206",
    "control": "UZ"
  }
}
```

---

## 📁 Archivos Generados

Para cada referencia catastral se generan los siguientes archivos:

### Geometrías
- `{REF}_parcela.gml` - Geometría oficial de la parcela
- `{REF}_edificio.gml` - Geometría del edificio (si existe)
- `{REF}_parcela.kml` - Para Google Earth

### Datos
- `{REF}_datos.xml` - Datos alfanuméricos completos

### Imágenes
- `{REF}_plano_catastro.png` - Plano catastral
- `{REF}_plano_catastro_contorno.png` - Plano con contorno rojo
- `{REF}_ortofoto_pnoa.jpg` - Ortofoto PNOA
- `{REF}_ortofoto_pnoa_contorno.jpg` - Ortofoto con contorno
- `{REF}_plano_con_ortofoto.png` - Composición plano + ortofoto
- `{REF}_plano_con_ortofoto_contorno.png` - **Composición con contorno** ⭐

### Ortofotos de Contexto
- `{REF}_ortofoto_provincial.jpg` - Vista provincial con contorno
- `{REF}_ortofoto_autonomico.jpg` - Vista autonómica con contorno
- `{REF}_ortofoto_nacional.jpg` - Vista nacional con contorno

### Documentos
- `{REF}_consulta_oficial.pdf` - PDF oficial del Catastro
- `{REF}_informe.pdf` - Informe completo con todas las imágenes

### Afecciones (opcional)
- `{REF}_afeccion_catastro_parcelas.png`
- `{REF}_afeccion_planeamiento.png`
- `{REF}_afecciones_info.json`

### Comprimido
- `{REF}_completo.zip` - ZIP con todos los archivos

---

## 🎨 Composición de Imágenes

El sistema genera automáticamente una **composición visual** que combina:

1. **Ortofoto PNOA** (base, 65% opacidad)
2. **Plano Catastral** (overlay, 35% opacidad)
3. **Contorno de Parcela** (rojo sólido, dibujado sobre la composición)

### Resultado:
```
{REF}_plano_con_ortofoto_contorno.png
```

Esta imagen muestra:
- ✅ Imagen aérea de alta resolución
- ✅ Plano catastral superpuesto
- ✅ Contorno de la parcela dibujado en rojo
- ✅ Perfecto para presentaciones e informes

---

## 🔧 Configuración Avanzada

### Cambiar Directorio de Salida

```python
# En main.py
catastro_downloader = CatastroDownloader(
    output_dir="mi_directorio_custom",  # ← Cambiar aquí
    cache_hours=1,
    max_workers=3
)
```

### Ajustar Workers Paralelos

```python
catastro_downloader = CatastroDownloader(
    output_dir="descargas_catastro",
    cache_hours=1,
    max_workers=5  # ← Más workers = más rápido (pero más carga)
)
```

### Cambiar Tiempo de Cache

```python
catastro_downloader = CatastroDownloader(
    output_dir="descargas_catastro",
    cache_hours=24,  # ← 24 horas de cache
    max_workers=3
)
```

---

## 📊 Procesamiento por Lotes

### Estructura del ZIP de Lote

```
lote_20260128_1430_3_refs.zip
├── resumen_lote_20260128_1430.csv  ← Resumen con coordenadas y superficies
├── 30037A008002060000UZ/
│   ├── 30037A008002060000UZ_parcela.gml
│   ├── 30037A008002060000UZ_plano_con_ortofoto_contorno.png
│   ├── 30037A008002060000UZ_informe.pdf
│   └── ... (todos los archivos)
├── 30037A008002070000UZ/
│   └── ...
└── 30037A008002080000UZ/
    └── ...
```

### Resumen CSV

El archivo `resumen_lote_*.csv` contiene:

| Campo | Descripción |
|-------|-------------|
| Referencia | Referencia catastral |
| Estado | Correcto / Error |
| Latitud | Coordenadas WGS84 |
| Longitud | Coordenadas WGS84 |
| UTM_X | Coordenadas UTM |
| UTM_Y | Coordenadas UTM |
| Huso | Huso UTM |
| Superficie_Catastro_m2 | Superficie de la parcela |
| Superficie_Construida_m2 | Superficie construida |
| Año_Construccion | Año de construcción |
| Uso_Principal | Uso principal |

---

## 🐛 Troubleshooting

### Error: "Pillow no disponible"

```bash
pip install Pillow
```

Sin Pillow, no se generarán:
- Composiciones de imágenes
- Contornos dibujados
- Ortofotos de contexto

### Error: "ReportLab no disponible"

```bash
pip install reportlab
```

Sin ReportLab, no se generará:
- Informe PDF completo

### Error: "pyproj no disponible"

```bash
pip install pyproj
```

Sin pyproj, las coordenadas UTM serán aproximadas (no precisas).

### Cache demasiado agresivo

```bash
# Limpiar cache HTTP
rm -rf catastro_cache.sqlite

# O desactivar cache
# En catastro_service.py, línea ~30:
# cache_hours=0  # Sin cache
```

### Archivos muy grandes

Los ZIP pueden ser grandes (30-50 MB por referencia). Para reducir tamaño:

1. Desactivar afecciones: `descargar_afecciones=False`
2. Desactivar ortofotos de contexto (modificar código)
3. Reducir resolución de imágenes WMS

---

## ✨ Ejemplos de Uso

### Python

```python
import requests

# Descargar documentación completa
response = requests.post(
    'http://localhost:8000/api/v1/catastro/descargar',
    json={
        'referencia': '30037A008002060000UZ',
        'descargar_afecciones': True,
        'crear_zip': True
    }
)

resultado = response.json()

if resultado['exitosa']:
    print(f"✅ Descarga exitosa")
    print(f"ZIP: {resultado['zip_path']}")
    
    # Acceder al ZIP
    zip_url = f"http://localhost:8000/descargas/{resultado['zip_path'].split('/')[-1]}"
    print(f"Descargar: {zip_url}")
```

### JavaScript

```javascript
async function descargarCatastro(referencia) {
    const response = await fetch('/api/v1/catastro/descargar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            referencia: referencia,
            descargar_afecciones: true,
            crear_zip: true
        })
    });
    
    const data = await response.json();
    
    if (data.exitosa) {
        console.log('✅ Descarga completa');
        
        // Descargar ZIP
        const zipName = data.zip_path.split('/').pop();
        window.location.href = `/descargas/${zipName}`;
    }
}

// Uso
descargarCatastro('30037A008002060000UZ');
```

---

## 🎯 Casos de Uso

### 1. Due Diligence Inmobiliaria
Obtener toda la documentación oficial de una parcela para análisis previo a compra.

### 2. Proyectos Urbanísticos
Descargar geometrías y planos para proyectos de construcción.

### 3. Estudios Territoriales
Procesar lotes de referencias para análisis territorial.

### 4. Informes Técnicos
Generar informes profesionales con composiciones visuales.

### 5. Planificación
Obtener ortofotos de contexto para visualización de ubicación.

---

## 📞 Soporte

- **Documentación API:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Logs:** Ver consola del servidor

---

**🎉 Sistema de Catastro completamente integrado y funcional!**

Todas las funcionalidades del documento original están implementadas:
- ✅ GML de parcelas y edificios
- ✅ Datos alfanuméricos (XML)
- ✅ Composición plano + ortofoto
- ✅ Contornos dibujados en rojo
- ✅ PDFs oficiales
- ✅ Ortofotos de contexto
- ✅ Procesamiento por lotes
- ✅ Cache HTTP
- ✅ Resumen CSV
