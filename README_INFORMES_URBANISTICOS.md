# Integración de Informes Urbanísticos

Este módulo añade la capacidad de generar informes urbanísticos automáticos al Proyecto GIS, integrando datos de Catastro, INSPIRE y diversos servicios de afecciones territoriales.

## 🚀 Instalación

1. Copia los archivos a tu proyecto:
   - `urbanismo.py` -> Raíz del proyecto
   - `urbanismo_config.json` -> `config/`
   - `informes_urbanisticos.html` -> `templates/`

2. Instala las dependencias necesarias:
   ```bash
   pip install requests
   ```

## 🛠️ Uso del Módulo Python

```python
from urbanismo import InformeUrbanistico

# Inicializar
generador = InformeUrbanistico('config/urbanismo_config.json')

# Generar informe por RC
informe = generador.generar_informe_completo(ref_catastral='1234567VK1234N0001AB')

# Exportar resultados
generador.generar_informe_pdf(informe, 'informe.pdf')
generador.generar_informe_kml(informe, 'parcela.kml')
```

## 🖥️ Interfaz Web

La nueva sección `informes_urbanisticos.html` ofrece:
- Búsqueda por Referencia Catastral o Dirección.
- Selección de tipo de informe (Básico, Completo, Viabilidad, Cédula).
- Barra de progreso animada.
- Visualización de resultados y descarga de documentos.

## 📊 Afecciones Soportadas

El sistema consulta automáticamente:
1. **Costas**: Deslinde y servidumbres.
2. **Carreteras**: Zonas de afección y servidumbre.
3. **Cauces**: Dominio Público Hidráulico y zonas de policía.
4. **Inundabilidad**: Zonas inundables para distintos periodos de retorno.
5. **Espacios Protegidos**: Red Natura 2000, Parques, etc.
6. **Patrimonio**: Entornos de protección BIC.
7. **Vías Pecuarias**.
8. **Montes Públicos**.
9. **Servidumbres Aeronáuticas**.
10. **Líneas Eléctricas y Gaseoductos**.

## 📝 Pruebas

Para ejecutar los tests automatizados:
```bash
python -m unittest tests/test_urbanismo.py
```
