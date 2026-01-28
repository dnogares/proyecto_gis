# 📊 Guía de Análisis de Afecciones y Catastro

## 🎯 Descripción

El sistema de análisis de afecciones permite evaluar el impacto ambiental y urbanístico de parcelas,  identificando automáticamente afecciones con:

- 🌳 **Red Natura 2000** (nivel CRÍTICO)
- 🏞️ **Espacios Naturales Protegidos** (nivel ALTO)
- 🐄 **Vías Pecuarias** (nivel MEDIO)
- 💧 **Masas de Agua** (nivel MEDIO)
- 🌊 **Zonas Inundables** (nivel ALTO)

---

## 🚀 Inicio Rápido

### Opción 1: Interfaz Web

1. **Abrir interfaz de análisis:**
   ```
   http://localhost:8000/analisis.html
   ```

2. **Dibujar parcela en el mapa:**
   - Usar herramientas de dibujo (polígono/rectángulo)
   - O pegar geometría WKT manualmente

3. **Introducir referencia catastral** (opcional)

4. **Click en "Analizar Afecciones"**

5. **Ver resultados:**
   - Nivel de afección global
   - Lista de afecciones encontradas
   - Recomendaciones técnicas

### Opción 2: API REST

```bash
# Analizar afecciones de una parcela
curl -X POST http://localhost:8000/api/v1/analisis/afecciones \
  -H "Content-Type: application/json" \
  -d '{
    "geometria_wkt": "POLYGON((-2.45 36.84, -2.44 36.84, -2.44 36.83, -2.45 36.83, -2.45 36.84))",
    "referencia_catastral": "1234567AB1234D"
  }'
```

---

## 📚 Endpoints API

### 1. Análisis de Afecciones

**POST** `/api/v1/analisis/afecciones`

Analiza todas las afecciones ambientales y urbanísticas.

**Request:**
```json
{
  "geometria_wkt": "POLYGON((...)))",
  "referencia_catastral": "1234567AB1234D"  // opcional
}
```

**Response:**
```json
{
  "referencia_catastral": "1234567AB1234D",
  "area_total_m2": 5000.50,
  "tiene_afecciones": true,
  "num_afecciones": 2,
  "nivel_afeccion_global": "ALTO",
  "afecciones": [
    {
      "afecta": true,
      "capa": "rednatura",
      "nombre": "Red Natura 2000",
      "nivel": "CRÍTICO",
      "descripcion": "Espacios protegidos Red Natura",
      "restricciones": "Requiere evaluación ambiental",
      "area_afectada_m2": 1250.30,
      "porcentaje_afectado": 25.00,
      "num_elementos": 1,
      "atributos": [...]
    }
  ],
  "recomendaciones": [
    "⚠️ CRÍTICO - Red Natura 2000: Afecta 25.0% de la parcela...",
    "📋 Se recomienda estudio técnico detallado..."
  ]
}
```

### 2. Generar Informe

**POST** `/api/v1/analisis/afecciones/informe`

Genera informe en texto plano.

**Request:** Igual que análisis de afecciones

**Response:**
```json
{
  "informe": "======================================...",
  "resultado": { ... }
}
```

### 3. Consultar Catastro

**GET** `/api/v1/catastro/{referencia_catastral}`

Obtiene datos catastrales de una parcela.

**Response:**
```json
{
  "referencia_catastral": "1234567AB1234D",
  "direccion": "Calle Ejemplo, 1",
  "municipio": "Almería",
  "provincia": "Almería",
  "uso_principal": "Residencial",
  "superficie_construida": 150.0,
  "superficie_parcela": 500.0,
  "ano_construccion": 2010,
  "datos_disponibles": false,
  "mensaje": "Integración con Catastro pendiente"
}
```

### 4. Análisis Completo

**POST** `/api/v1/analisis/completo`

Combina datos catastrales + análisis de afecciones.

**Request:**
```json
{
  "referencia_catastral": "1234567AB1234D",
  "geometria_wkt": "POLYGON((...)))"
}
```

**Response:**
```json
{
  "referencia_catastral": "1234567AB1234D",
  "datos_catastro": { ... },
  "analisis_afecciones": { ... },
  "informe": "..."
}
```

### 5. Validar Geometría

**POST** `/api/v1/geometria/validar`

Valida una geometría WKT y retorna estadísticas.

**Request:**
```json
{
  "geometria_wkt": "POLYGON((...)))"
}
```

**Response:**
```json
{
  "valida": true,
  "tipo_geometria": "Polygon",
  "area_m2": 5000.50,
  "perimetro_m": 283.14,
  "bbox": {
    "minx": -2.45,
    "miny": 36.83,
    "maxx": -2.44,
    "maxy": 36.84
  },
  "centroide": {
    "lon": -2.445,
    "lat": 36.835
  }
}
```

---

## 🧪 Ejemplos de Uso

### Python

```python
import requests
import json

# Definir geometría de la parcela
geometria = "POLYGON((-2.45 36.84, -2.44 36.84, -2.44 36.83, -2.45 36.83, -2.45 36.84))"

# Analizar afecciones
response = requests.post(
    'http://localhost:8000/api/v1/analisis/afecciones',
    json={
        'geometria_wkt': geometria,
        'referencia_catastral': '1234567AB1234D'
    }
)

resultado = response.json()

# Mostrar resultados
print(f"Área: {resultado['area_total_m2']} m²")
print(f"Nivel: {resultado['nivel_afeccion_global']}")
print(f"Afecciones: {resultado['num_afecciones']}")

for afeccion in resultado['afecciones']:
    print(f"\n- {afeccion['nombre']}")
    print(f"  Nivel: {afeccion['nivel']}")
    print(f"  Área afectada: {afeccion['area_afectada_m2']} m²")
    print(f"  Porcentaje: {afeccion['porcentaje_afectado']}%")
```

### JavaScript

```javascript
async function analizarParcela(geometriaWKT, refCatastral) {
    const response = await fetch('/api/v1/analisis/afecciones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            geometria_wkt: geometriaWKT,
            referencia_catastral: refCatastral
        })
    });
    
    const resultado = await response.json();
    
    console.log(`Área: ${resultado.area_total_m2} m²`);
    console.log(`Nivel: ${resultado.nivel_afeccion_global}`);
    console.log(`Afecciones: ${resultado.num_afecciones}`);
    
    resultado.afecciones.forEach(afeccion => {
        console.log(`\n${afeccion.nombre} (${afeccion.nivel})`);
        console.log(`  Área: ${afeccion.area_afectada_m2} m²`);
        console.log(`  ${afeccion.restricciones}`);
    });
    
    return resultado;
}

// Uso
const wkt = "POLYGON((-2.45 36.84, -2.44 36.84, -2.44 36.83, -2.45 36.83, -2.45 36.84))";
analizarParcela(wkt, "1234567AB1234D");
```

---

## 🎨 Personalización

### Añadir Nueva Capa de Afecciones

Editar `services/analisis_afecciones.py`:

```python
self.capas_afecciones = {
    # ... capas existentes ...
    
    'mi_nueva_capa': {
        'nombre': 'Mi Nueva Capa',
        'nivel': 'ALTO',  # CRÍTICO, ALTO, MEDIO, BAJO
        'descripcion': 'Descripción de la capa',
        'restricciones': 'Restricciones aplicables'
    }
}
```

### Modificar Niveles de Afección

En `_calcular_nivel_global()`:

```python
def _calcular_nivel_global(self, afecciones: List[Dict]) -> str:
    # Personalizar lógica de cálculo
    if not afecciones:
        return 'NINGUNO'
    
    # Tu lógica personalizada aquí
    ...
```

### Personalizar Recomendaciones

En `_generar_recomendaciones()`:

```python
def _generar_recomendaciones(self, afecciones, area_parcela_m2):
    recomendaciones = []
    
    # Tu lógica de recomendaciones
    if area_parcela_m2 > 10000:
        recomendaciones.append("Parcela grande: considerar estudio de impacto")
    
    ...
```

---

## 📊 Niveles de Afección

| Nivel | Color | Significado | Acción Recomendada |
|-------|-------|-------------|-------------------|
| **CRÍTICO** | 🔴 Rojo | Afección muy grave | Evaluación ambiental obligatoria |
| **ALTO** | 🟠 Naranja | Afección grave | Estudio técnico detallado |
| **MEDIO** | 🟡 Amarillo | Afección moderada | Verificar restricciones |
| **BAJO** | 🟢 Verde | Afección leve | Revisión básica |
| **NINGUNO** | ⚪ Blanco | Sin afecciones | Proceder normalmente |

---

## 🔧 Troubleshooting

### Error: "Data Manager no disponible"

**Causa:** Backend no inicializado correctamente

**Solución:**
```bash
# Verificar que el servidor está corriendo
python main.py

# Verificar logs
# Debe mostrar: ✅ Analizadores inicializados
```

### Error: "Capa no encontrada"

**Causa:** Archivos FGB/GPKG no disponibles o PostGIS no conectado

**Solución:**
```bash
# Verificar archivos FGB
ls -lh capas/fgb/

# Verificar PostGIS
curl http://localhost:8000/health
```

### Resultados vacíos

**Causa:** No hay intersección entre parcela y capas

**Solución:**
- Verificar que la geometría WKT es correcta
- Verificar que las coordenadas están en EPSG:4326
- Probar con parcela más grande o en ubicación diferente

### Geometría WKT inválida

**Causa:** Formato WKT incorrecto

**Solución:**
```bash
# Validar geometría
curl -X POST http://localhost:8000/api/v1/geometria/validar \
  -H "Content-Type: application/json" \
  -d '{"geometria_wkt": "POLYGON((...)))"}'
```

---

## 📁 Estructura de Archivos

```
services/
├── analisis_afecciones.py     # 🔍 Motor de análisis
│   ├── AnalizadorAfecciones    # Clase principal
│   ├── AnalizadorCatastro      # Integración catastro
│   └── generar_informe_*       # Generación de informes

templates/
└── analisis.html               # 🎨 Interfaz web

main.py                          # 🌐 Endpoints API
```

---

## 🎯 Casos de Uso

### 1. Análisis Urbanístico

```python
# Analizar viabilidad de proyecto urbanístico
resultado = analizador.analizar_parcela(geometria_parcela)

if resultado['nivel_afeccion_global'] in ['CRÍTICO', 'ALTO']:
    print("⚠️ Proyecto NO VIABLE sin evaluación ambiental")
else:
    print("✅ Proyecto potencialmente viable")
```

### 2. Due Diligence Inmobiliaria

```python
# Análisis previo a compra de terreno
analisis = requests.post('/api/v1/analisis/completo', json={
    'referencia_catastral': ref,
    'geometria_wkt': wkt
})

# Evaluar riesgos
if analisis['tiene_afecciones']:
    print(f"Riesgos identificados: {analisis['num_afecciones']}")
```

### 3. Planificación de Infraestructuras

```python
# Evaluar trazado de carretera
for tramo in trazado:
    afecciones = analizador.analizar_parcela(tramo.geometria)
    tramos_problematicos.append(afecciones)
```

---

## ✅ Checklist de Producción

Antes de usar en producción:

- [ ] Datos FlatGeobuf actualizados
- [ ] PostGIS configurado y optimizado
- [ ] Índices GIST creados
- [ ] API de Catastro integrada (si aplica)
- [ ] Testing con casos reales
- [ ] Validación de resultados por técnico
- [ ] Documentación de responsabilidades legales

---

## ⚖️ Disclaimer Legal

Este sistema proporciona **análisis técnico automatizado** basado en datos geoespaciales disponibles.

**IMPORTANTE:**
- Los resultados son orientativos y requieren validación técnica
- NO sustituyen estudios técnicos oficiales
- NO constituyen informe pericial vinculante
- Se recomienda consultar con técnico competente
- Verificar normativa municipal vigente

---

## 📞 Soporte

- **Documentación API:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Logs:** Ver consola del servidor

---

**¡Sistema de análisis de afecciones listo para usar! 🚀**
