"""
Servicio para interactuar con PostGIS

Proporciona conexión y operaciones básicas con PostgreSQL + PostGIS
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class PostGISService:
    """
    Servicio para operaciones con PostGIS
    
    Maneja conexiones, consultas y operaciones espaciales
    """
    
    def __init__(
        self,
        host: str = "192.168.1.138",
        database: str = "GIS",
        user: str = "manuel",
        password: str = "Aa123456",
        port: int = 5432
    ):
        """
        Inicializa servicio PostGIS
        
        Args:
            host: Host de PostgreSQL
            database: Nombre de la base de datos
            user: Usuario de PostgreSQL
            password: Contraseña
            port: Puerto (default: 5432)
        """
        self.config = {
            "host": host,
            "database": database,
            "user": user,
            "password": password,
            "port": port
        }
        
        self.connection = None
        
        # Verificar conexión inicial
        self._test_connection()
    
    def _test_connection(self):
        """Verificar que la conexión funciona"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT PostGIS_version();")
                    version = cur.fetchone()[0]
                    logger.info(f"✅ Conexión PostGIS exitosa: {version}")
        except Exception as e:
            logger.warning(f"⚠️  PostGIS no disponible: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para conexión PostgreSQL
        
        Uso:
            with service.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT ...")
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            # Fuerza UTF-8 en cada conexión
            conn.set_client_encoding('UTF8')
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error en conexión PostGIS: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False
    ) -> Optional[List[Dict]]:
        """
        Ejecutar query y retornar resultados
        
        Args:
            query: Query SQL
            params: Parámetros para la query
            fetch_one: Si True, retorna solo el primer resultado
            
        Returns:
            Lista de diccionarios con resultados o None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    
                    if fetch_one:
                        return dict(cur.fetchone()) if cur.rowcount > 0 else None
                    else:
                        return [dict(row) for row in cur.fetchall()]
        
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            return None
    
    def listar_tablas_espaciales(self) -> List[Dict[str, str]]:
        """
        Lista todas las tablas con geometrías en la base de datos
        
        Returns:
            Lista de diccionarios con info de tablas
        """
        query = """
            SELECT 
                f_table_schema as schema,
                f_table_name as tabla,
                f_geometry_column as columna_geom,
                type as tipo_geometria,
                srid,
                coord_dimension as dimensiones
            FROM geometry_columns
            ORDER BY f_table_schema, f_table_name;
        """
        
        return self.execute_query(query) or []
    
    def obtener_bbox_tabla(
        self,
        schema: str,
        tabla: str,
        columna_geom: str = "geom"
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Obtiene el bounding box de una tabla
        
        Args:
            schema: Esquema de la tabla
            tabla: Nombre de la tabla
            columna_geom: Nombre de la columna de geometría
            
        Returns:
            Tupla (minx, miny, maxx, maxy) en el CRS de la tabla
        """
        query = f"""
            SELECT 
                ST_XMin(extent) as minx,
                ST_YMin(extent) as miny,
                ST_XMax(extent) as maxx,
                ST_YMax(extent) as maxy
            FROM (
                SELECT ST_Extent({columna_geom}) as extent
                FROM {schema}."{tabla}"
            ) as subquery;
        """
        
        result = self.execute_query(query, fetch_one=True)
        
        if result:
            return (
                result['minx'],
                result['miny'],
                result['maxx'],
                result['maxy']
            )
        
        return None
    
    def contar_features(
        self,
        schema: str,
        tabla: str
    ) -> int:
        """
        Cuenta el número de features en una tabla
        
        Args:
            schema: Esquema de la tabla
            tabla: Nombre de la tabla
            
        Returns:
            Número de features
        """
        query = f'SELECT COUNT(*) as count FROM {schema}."{tabla}";'
        
        result = self.execute_query(query, fetch_one=True)
        
        return result['count'] if result else 0
    
    def verificar_indice_espacial(
        self,
        schema: str,
        tabla: str,
        columna_geom: str = "geom"
    ) -> bool:
        """
        Verifica si existe índice espacial GIST en una columna
        
        Args:
            schema: Esquema de la tabla
            tabla: Nombre de la tabla
            columna_geom: Nombre de la columna de geometría
            
        Returns:
            True si existe índice GIST
        """
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = %s
                AND tablename = %s
                AND indexdef LIKE %s
            ) as tiene_indice;
        """
        
        result = self.execute_query(
            query,
            (schema, tabla, f'%USING gist%{columna_geom}%'),
            fetch_one=True
        )
        
        return result['tiene_indice'] if result else False
    
    def crear_indice_espacial(
        self,
        schema: str,
        tabla: str,
        columna_geom: str = "geom"
    ) -> bool:
        """
        Crea índice espacial GIST en una columna
        
        Args:
            schema: Esquema de la tabla
            tabla: Nombre de la tabla
            columna_geom: Nombre de la columna de geometría
            
        Returns:
            True si se creó el índice exitosamente
        """
        # Verificar si ya existe
        if self.verificar_indice_espacial(schema, tabla, columna_geom):
            logger.info(f"✅ Índice ya existe en {schema}.{tabla}.{columna_geom}")
            return True
        
        try:
            nombre_indice = f"{tabla}_{columna_geom}_idx"
            query = f"""
                CREATE INDEX {nombre_indice}
                ON {schema}."{tabla}"
                USING GIST ({columna_geom});
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
            
            logger.info(f"✅ Índice creado: {nombre_indice}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando índice: {e}")
            return False
    
    def obtener_info_tabla(
        self,
        schema: str,
        tabla: str
    ) -> Optional[Dict]:
        """
        Obtiene información completa de una tabla espacial
        
        Args:
            schema: Esquema de la tabla
            tabla: Nombre de la tabla
            
        Returns:
            Diccionario con info de la tabla
        """
        # Info básica
        query_info = """
            SELECT 
                f_geometry_column as columna_geom,
                type as tipo_geometria,
                srid,
                coord_dimension as dimensiones
            FROM geometry_columns
            WHERE f_table_schema = %s
            AND f_table_name = %s;
        """
        
        info = self.execute_query(query_info, (schema, tabla), fetch_one=True)
        
        if not info:
            return None
        
        # Añadir estadísticas
        info['num_features'] = self.contar_features(schema, tabla)
        info['bbox'] = self.obtener_bbox_tabla(schema, tabla, info['columna_geom'])
        info['tiene_indice'] = self.verificar_indice_espacial(
            schema,
            tabla,
            info['columna_geom']
        )
        
        return info
    
    def cerrar(self):
        """Cerrar conexión si está abierta"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Conexión PostGIS cerrada")


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def crear_indices_todas_tablas(service: PostGISService) -> Dict[str, int]:
    """
    Crea índices GIST en todas las tablas espaciales que no lo tengan
    
    Args:
        service: Instancia de PostGISService
        
    Returns:
        Diccionario con estadísticas
    """
    logger.info("🔍 Verificando índices espaciales...")
    
    tablas = service.listar_tablas_espaciales()
    stats = {"creados": 0, "existentes": 0, "errores": 0}
    
    for tabla in tablas:
        schema = tabla['schema']
        nombre = tabla['tabla']
        columna = tabla['columna_geom']
        
        if service.verificar_indice_espacial(schema, nombre, columna):
            stats["existentes"] += 1
        else:
            if service.crear_indice_espacial(schema, nombre, columna):
                stats["creados"] += 1
            else:
                stats["errores"] += 1
    
    logger.info(f"📊 Índices creados: {stats['creados']}")
    logger.info(f"📊 Índices existentes: {stats['existentes']}")
    logger.info(f"📊 Errores: {stats['errores']}")
    
    return stats


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Crear servicio
    service = PostGISService(
        host="localhost",
        database="GIS",
        user="manuel",
        password="Aa123456"
    )
    
    # Listar tablas
    print("\n📊 TABLAS ESPACIALES:")
    print("-" * 70)
    
    tablas = service.listar_tablas_espaciales()
    for tabla in tablas:
        print(f"  • {tabla['schema']}.{tabla['tabla']}")
        print(f"    - Geometría: {tabla['tipo_geometria']} (SRID: {tabla['srid']})")
    
    # Info de una tabla específica
    print("\n📋 INFO DETALLADA - Red Natura:")
    print("-" * 70)
    
    info = service.obtener_info_tabla("public", "biodiversidad:RedNatura")
    if info:
        print(f"  Features: {info['num_features']:,}")
        print(f"  Tipo: {info['tipo_geometria']}")
        print(f"  SRID: {info['srid']}")
        print(f"  Índice GIST: {'✅ Sí' if info['tiene_indice'] else '❌ No'}")
        if info['bbox']:
            print(f"  BBox: {info['bbox']}")
    
    # Crear índices faltantes
    print("\n🔧 VERIFICANDO ÍNDICES:")
    print("-" * 70)
    
    stats = crear_indices_todas_tablas(service)
    
    service.cerrar()
    
    print("\n✅ Completado")
