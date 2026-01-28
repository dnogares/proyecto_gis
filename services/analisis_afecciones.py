"""
Módulo de Análisis de Afecciones

Analiza afecciones de una parcela con capas de protección ambiental y urbanística.
Usa PostGIS para máximo rendimiento en cálculos espaciales.
"""

import geopandas as gpd
from shapely import wkt
from shapely.geometry import shape, mapping
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class AnalizadorAfecciones:
    """
    Analiza afecciones ambientales y urbanísticas de parcelas
    """
    
    def __init__(self, data_manager):
        """
        Inicializa analizador de afecciones
        
        Args:
            data_manager: Instancia de DataSourceManager
        """
        self.data_manager = data_manager
        
        # Configuración de capas de afecciones
        self.capas_afecciones = {
            'rednatura': {
                'nombre': 'Red Natura 2000',
                'nivel': 'CRÍTICO',
                'descripcion': 'Espacios protegidos Red Natura',
                'restricciones': 'Requiere evaluación ambiental'
            },
            'espaciosnaturales': {
                'nombre': 'Espacios Naturales Protegidos',
                'nivel': 'ALTO',
                'descripcion': 'Espacios naturales de alto valor',
                'restricciones': 'Protección especial'
            },
            'viaspocuarias': {
                'nombre': 'Vías Pecuarias',
                'nivel': 'MEDIO',
                'descripcion': 'Vías pecuarias públicas',
                'restricciones': 'No edificables, dominio público'
            },
            'zonasinundables': {
                'nombre': 'Zonas Inundables',
                'nivel': 'ALTO',
                'descripcion': 'Zonas con riesgo de inundación',
                'restricciones': 'Restricciones constructivas'
            },
            'masasagua': {
                'nombre': 'Masas de Agua',
                'nivel': 'MEDIO',
                'descripcion': 'Cursos de agua y cauces',
                'restricciones': 'Zona de servidumbre'
            }
        }
    
    def analizar_parcela(
        self,
        geometria_parcela: str,
        referencia_catastral: Optional[str] = None
    ) -> Dict:
        """
        Analiza todas las afecciones de una parcela
        
        Args:
            geometria_parcela: WKT de la geometría de la parcela
            referencia_catastral: Referencia catastral opcional
            
        Returns:
            Diccionario con resultado del análisis completo
        """
        logger.info(f"🔍 Analizando afecciones para parcela {referencia_catastral or 'sin ref'}")
        
        try:
            # Convertir WKT a geometría
            geom_parcela = wkt.loads(geometria_parcela)
            
            # Crear GeoDataFrame de la parcela
            gdf_parcela = gpd.GeoDataFrame(
                {'geometry': [geom_parcela]},
                crs='EPSG:4326'
            )
            
            # Calcular área de la parcela
            # Reproyectar a UTM para cálculo preciso de área
            gdf_parcela_utm = gdf_parcela.to_crs('EPSG:25830')  # UTM 30N para España
            area_parcela_m2 = gdf_parcela_utm.geometry.area.sum()
            
            # Analizar cada capa de afecciones
            afecciones_encontradas = []
            tiene_afecciones = False
            
            for capa_id, capa_info in self.capas_afecciones.items():
                logger.info(f"  → Analizando {capa_info['nombre']}...")
                
                afeccion = self._analizar_capa_afeccion(
                    gdf_parcela,
                    capa_id,
                    capa_info
                )
                
                if afeccion['afecta']:
                    afecciones_encontradas.append(afeccion)
                    tiene_afecciones = True
                    logger.info(f"    ✓ AFECCIÓN: {afeccion['area_afectada_m2']:.2f} m²")
            
            # Calcular nivel de afección global
            nivel_afeccion_global = self._calcular_nivel_global(afecciones_encontradas)
            
            # Generar recomendaciones
            recomendaciones = self._generar_recomendaciones(
                afecciones_encontradas,
                area_parcela_m2
            )
            
            resultado = {
                'referencia_catastral': referencia_catastral,
                'area_total_m2': round(area_parcela_m2, 2),
                'tiene_afecciones': tiene_afecciones,
                'num_afecciones': len(afecciones_encontradas),
                'nivel_afeccion_global': nivel_afeccion_global,
                'afecciones': afecciones_encontradas,
                'recomendaciones': recomendaciones,
                'geometria_wkt': geometria_parcela
            }
            
            logger.info(f"✅ Análisis completado: {len(afecciones_encontradas)} afecciones")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de afecciones: {e}")
            raise
    
    def _analizar_capa_afeccion(
        self,
        gdf_parcela: gpd.GeoDataFrame,
        capa_id: str,
        capa_info: Dict
    ) -> Dict:
        """
        Analiza afección de una capa específica
        
        Args:
            gdf_parcela: GeoDataFrame de la parcela
            capa_id: ID de la capa a analizar
            capa_info: Información de la capa
            
        Returns:
            Diccionario con resultado del análisis
        """
        try:
            # Obtener bbox de la parcela
            bounds = gdf_parcela.total_bounds
            bbox = tuple(bounds)
            
            # Cargar capa de afecciones (prioriza PostGIS)
            gdf_capa = self.data_manager.obtener_capa(
                capa_id,
                bbox=bbox,
                formato_preferido='postgis'
            )
            
            if gdf_capa is None or gdf_capa.empty:
                return {
                    'afecta': False,
                    'capa': capa_id,
                    'nombre': capa_info['nombre'],
                    'nivel': capa_info['nivel']
                }
            
            # Asegurar mismo CRS
            if gdf_capa.crs != gdf_parcela.crs:
                gdf_capa = gdf_capa.to_crs(gdf_parcela.crs)
            
            # Calcular intersección
            interseccion = gpd.overlay(
                gdf_parcela,
                gdf_capa,
                how='intersection'
            )
            
            if interseccion.empty:
                return {
                    'afecta': False,
                    'capa': capa_id,
                    'nombre': capa_info['nombre'],
                    'nivel': capa_info['nivel']
                }
            
            # Calcular área afectada en metros cuadrados
            interseccion_utm = interseccion.to_crs('EPSG:25830')
            area_afectada_m2 = interseccion_utm.geometry.area.sum()
            
            # Calcular porcentaje
            area_parcela_m2 = gdf_parcela.to_crs('EPSG:25830').geometry.area.sum()
            porcentaje_afectado = (area_afectada_m2 / area_parcela_m2) * 100
            
            # Extraer atributos relevantes
            atributos = []
            for idx, row in interseccion.iterrows():
                attrs = {}
                # Seleccionar solo campos relevantes
                for col in interseccion.columns:
                    if col != 'geometry' and row[col] is not None:
                        attrs[col] = str(row[col])[:100]  # Limitar longitud
                
                if attrs:
                    atributos.append(attrs)
            
            return {
                'afecta': True,
                'capa': capa_id,
                'nombre': capa_info['nombre'],
                'nivel': capa_info['nivel'],
                'descripcion': capa_info['descripcion'],
                'restricciones': capa_info['restricciones'],
                'area_afectada_m2': round(area_afectada_m2, 2),
                'porcentaje_afectado': round(porcentaje_afectado, 2),
                'num_elementos': len(interseccion),
                'atributos': atributos[:5]  # Limitar a 5 elementos
            }
            
        except Exception as e:
            logger.error(f"Error analizando capa {capa_id}: {e}")
            return {
                'afecta': False,
                'capa': capa_id,
                'nombre': capa_info['nombre'],
                'nivel': capa_info['nivel'],
                'error': str(e)
            }
    
    def _calcular_nivel_global(self, afecciones: List[Dict]) -> str:
        """
        Calcula nivel de afección global basado en afecciones encontradas
        
        Args:
            afecciones: Lista de afecciones encontradas
            
        Returns:
            Nivel global: NINGUNO, BAJO, MEDIO, ALTO, CRÍTICO
        """
        if not afecciones:
            return 'NINGUNO'
        
        # Si hay alguna afección CRÍTICA
        if any(a['nivel'] == 'CRÍTICO' for a in afecciones):
            return 'CRÍTICO'
        
        # Si hay alguna afección ALTA
        if any(a['nivel'] == 'ALTO' for a in afecciones):
            return 'ALTO'
        
        # Si hay más de 2 afecciones MEDIO
        afecciones_medio = [a for a in afecciones if a['nivel'] == 'MEDIO']
        if len(afecciones_medio) >= 2:
            return 'ALTO'
        
        # Si hay alguna afección MEDIO
        if afecciones_medio:
            return 'MEDIO'
        
        return 'BAJO'
    
    def _generar_recomendaciones(
        self,
        afecciones: List[Dict],
        area_parcela_m2: float
    ) -> List[str]:
        """
        Genera recomendaciones basadas en las afecciones encontradas
        
        Args:
            afecciones: Lista de afecciones
            area_parcela_m2: Área de la parcela en m²
            
        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []
        
        if not afecciones:
            recomendaciones.append(
                "✅ No se detectaron afecciones ambientales o urbanísticas significativas"
            )
            recomendaciones.append(
                "ℹ️ Se recomienda verificar planeamiento urbanístico municipal"
            )
            return recomendaciones
        
        # Recomendaciones por tipo de afección
        for afeccion in afecciones:
            nivel = afeccion['nivel']
            nombre = afeccion['nombre']
            porcentaje = afeccion.get('porcentaje_afectado', 0)
            
            if nivel == 'CRÍTICO':
                recomendaciones.append(
                    f"⚠️ CRÍTICO - {nombre}: Afecta {porcentaje:.1f}% de la parcela. "
                    f"Requiere evaluación ambiental detallada."
                )
            
            elif nivel == 'ALTO':
                recomendaciones.append(
                    f"⚠️ ALTO - {nombre}: Afecta {porcentaje:.1f}% de la parcela. "
                    f"{afeccion.get('restricciones', 'Consultar normativa')}"
                )
            
            elif nivel == 'MEDIO':
                recomendaciones.append(
                    f"⚠️ MEDIO - {nombre}: Afecta {porcentaje:.1f}% de la parcela. "
                    f"{afeccion.get('restricciones', 'Verificar restricciones')}"
                )
        
        # Recomendaciones generales
        if len(afecciones) >= 3:
            recomendaciones.append(
                "📋 Se recomienda estudio técnico detallado debido a múltiples afecciones"
            )
        
        recomendaciones.append(
            "📞 Consultar con técnico competente antes de cualquier actuación"
        )
        
        return recomendaciones


class AnalizadorCatastro:
    """
    Analiza datos catastrales de parcelas
    """
    
    def __init__(self, catastro_service=None):
        """
        Inicializa analizador catastral
        
        Args:
            catastro_service: Servicio de conexión con Catastro (opcional)
        """
        self.catastro_service = catastro_service
    
    def obtener_datos_parcela(self, referencia_catastral: str) -> Dict:
        """
        Obtiene datos catastrales de una parcela
        
        Args:
            referencia_catastral: Referencia catastral de la parcela
            
        Returns:
            Diccionario con datos catastrales
        """
        logger.info(f"🔍 Consultando catastro: {referencia_catastral}")
        
        try:
            # TODO: Implementar conexión con API de Catastro
            # Por ahora, retornar datos de ejemplo
            
            return {
                'referencia_catastral': referencia_catastral,
                'direccion': 'Ejemplo de dirección',
                'municipio': 'Almería',
                'provincia': 'Almería',
                'uso_principal': 'Residencial',
                'superficie_construida': 150.0,
                'superficie_parcela': 500.0,
                'ano_construccion': 2010,
                'datos_disponibles': False,
                'mensaje': 'Integración con Catastro pendiente - datos de ejemplo'
            }
            
        except Exception as e:
            logger.error(f"Error consultando catastro: {e}")
            return {
                'referencia_catastral': referencia_catastral,
                'error': str(e),
                'datos_disponibles': False
            }


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def generar_informe_afecciones(resultado_analisis: Dict) -> str:
    """
    Genera informe en texto de las afecciones
    
    Args:
        resultado_analisis: Resultado del análisis de afecciones
        
    Returns:
        Informe en texto plano
    """
    informe = []
    informe.append("=" * 70)
    informe.append("INFORME DE AFECCIONES AMBIENTALES Y URBANÍSTICAS")
    informe.append("=" * 70)
    informe.append("")
    
    # Datos básicos
    if resultado_analisis.get('referencia_catastral'):
        informe.append(f"Referencia Catastral: {resultado_analisis['referencia_catastral']}")
    
    informe.append(f"Área de la parcela: {resultado_analisis['area_total_m2']:,.2f} m²")
    informe.append(f"Nivel de afección: {resultado_analisis['nivel_afeccion_global']}")
    informe.append("")
    
    # Afecciones encontradas
    if resultado_analisis['tiene_afecciones']:
        informe.append(f"AFECCIONES ENCONTRADAS ({resultado_analisis['num_afecciones']}):")
        informe.append("-" * 70)
        
        for i, afeccion in enumerate(resultado_analisis['afecciones'], 1):
            informe.append(f"\n{i}. {afeccion['nombre']} - Nivel {afeccion['nivel']}")
            informe.append(f"   Área afectada: {afeccion['area_afectada_m2']:,.2f} m² "
                         f"({afeccion['porcentaje_afectado']:.2f}%)")
            informe.append(f"   Descripción: {afeccion['descripcion']}")
            informe.append(f"   Restricciones: {afeccion['restricciones']}")
    else:
        informe.append("✅ NO SE ENCONTRARON AFECCIONES")
    
    # Recomendaciones
    informe.append("\n" + "=" * 70)
    informe.append("RECOMENDACIONES:")
    informe.append("-" * 70)
    
    for rec in resultado_analisis['recomendaciones']:
        informe.append(f"• {rec}")
    
    informe.append("\n" + "=" * 70)
    
    return "\n".join(informe)
