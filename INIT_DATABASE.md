# 🗄️ Inicialización de Base de Datos - GIS API v2.0

Guía paso a paso para crear y configurar la base de datos PostGIS en desarrollo, Docker o EasyPanel.

---

## 📋 Contenido

1. [Requisitos](#requisitos)
2. [Inicialización Local (Linux/macOS)](#inicialización-local-linuxmacos)
3. [Inicialización en Windows](#inicialización-en-windows)
4. [Inicialización en Docker](#inicialización-en-docker)
5. [Inicialización en EasyPanel](#inicialización-en-easypanel)
6. [Verificar la Instalación](#verificar-la-instalación)
7. [Troubleshooting](#troubleshooting)

---

## ✅ Requisitos

- **PostgreSQL 12+** instalado
- **PostGIS 3.0+** habilitado
- **psql** disponible en el PATH
- Usuario `postgres` o equivalente con permisos de superusuario
- Acceso a línea de comandos/terminal

---

## 🔧 Inicialización Local (Linux/macOS)

### Paso 1: Verificar PostgreSQL

```bash
# Verificar que PostgreSQL está corriendo
psql --version

# Conectar a PostgreSQL (si pide contraseña, úsala)
psql -U postgres -h localhost -d postgres
```

Si ves un error de conexión, inicia PostgreSQL:

```bash
# macOS
brew services start postgresql

# Ubuntu/Debian
sudo systemctl start postgresql
```

### Paso 2: Ejecutar Script de Inicialización

```bash
# Activar virtualenv (si usas)
source venv/bin/activate

# Ejecutar script bash
bash scripts/init_db.sh

# O con parámetros específicos
bash scripts/init_db.sh -h localhost -p 5432 -u postgres
```

### Paso 3: Configurar .env

Copia `.env.example` a `.env` y actualiza:

```bash
cp .env.example .env

# Editar .env
POSTGIS_HOST=localhost
POSTGIS_PORT=5432
POSTGIS_DATABASE=GIS
POSTGIS_USER=manuel
POSTGIS_PASSWORD=<tu_contraseña>  # Ajusta si el script estableció una
```

---

## 🪟 Inicialización en Windows

### Paso 1: Verificar PostgreSQL

```cmd
# Verificar instalación
psql --version

# Probar conexión (abre una terminal cmd o PowerShell)
psql -U postgres -h localhost -d postgres
```

Si no funciona, asegúrate de que PostgreSQL está en el PATH:
- Panel de Control → Sistema → Variables de entorno
- Añade `C:\Program Files\PostgreSQL\15\bin` (o tu versión) al PATH

### Paso 2: Ejecutar Script Batch

```cmd
# Abre cmd como Administrador y navega al directorio del proyecto
cd C:\ruta\a\proyecto_gis

# Ejecutar script
scripts\init_db.bat

# O con parámetros
scripts\init_db.bat -host localhost -port 5432 -user postgres
```

### Paso 3: Configurar .env

Edita `.env` (copia de `.env.example`):

```env
POSTGIS_HOST=localhost
POSTGIS_PORT=5432
POSTGIS_DATABASE=GIS
POSTGIS_USER=manuel
POSTGIS_PASSWORD=<tu_contraseña>
```

---

## 🐳 Inicialización en Docker

Si usas `docker-compose.yml`:

### Paso 1: Verificar docker-compose.yml

Asegúrate de que incluya el servicio `postgis`:

```yaml
services:
  postgis:
    image: postgis/postgis:15-3.3
    container_name: gis-postgis
    environment:
      POSTGRES_DB: GIS
      POSTGRES_USER: manuel
      POSTGRES_PASSWORD: Aa123456
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - gis-network

  gis-app:
    build: .
    container_name: gis-platform
    depends_on:
      - postgis
    environment:
      POSTGIS_HOST=postgis
      POSTGIS_PORT=5432
      POSTGIS_DATABASE=GIS
      POSTGIS_USER=manuel
      POSTGIS_PASSWORD=Aa123456
    networks:
      - gis-network

volumes:
  postgres_data:

networks:
  gis-network:
    driver: bridge
```

### Paso 2: Levantar Servicios

```bash
# Construir y levantar
docker-compose up -d

# Ver logs
docker-compose logs postgis

# Esperar a que PostGIS inicie (5-10 segundos)
sleep 10

# Ejecutar el script de inicialización DENTRO del contenedor
docker exec -it gis-postgis psql -U postgres -f /path/to/init_db.sql
```

**Alternativa**: Montar el script SQL como volumen en `docker-compose.yml`:

```yaml
postgis:
  volumes:
    - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
```

Esto ejecutará el script automáticamente al iniciar el contenedor.

### Paso 3: Verificar desde la App

```bash
# Ver logs de la app
docker-compose logs gis-app

# Deberías ver:
# ✅ Data Manager inicializado
# ✅ PostGIS disponible
```

---

## 🎯 Inicialización en EasyPanel

EasyPanel es una plataforma de deployments. Aquí está el flujo recomendado:

### Opción A: Script Manual en Terminal SSH/UI

1. **SSH al servidor**:
   ```bash
   ssh usuario@tu-servidor.easypanel.io
   cd /app/proyecto_gis
   ```

2. **Ejecutar script bash**:
   ```bash
   # Asegurar permisos
   chmod +x scripts/init_db.sh
   
   # Ejecutar (ajusta PGHOST si PostGIS está en otro host)
   PGHOST=localhost PGPORT=5432 PGUSER=postgres bash scripts/init_db.sh
   ```

3. **Configurar variables de entorno en EasyPanel**:
   - Ir a Settings → Environment Variables
   - Añadir:
     ```
     POSTGIS_HOST=localhost (o IP/hostname del servidor PostGIS)
     POSTGIS_PORT=5432
     POSTGIS_DATABASE=GIS
     POSTGIS_USER=manuel
     POSTGIS_PASSWORD=Aa123456
     CATASTRO_OUTPUT_DIR=/app/descargas_catastro
     ```

4. **Redeploy de la aplicación**:
   - Ir a Deployments
   - Click "Deploy" o "Redeploy"

### Opción B: Usar Docker Compose en EasyPanel

Si EasyPanel soporta docker-compose:

1. **Crea un archivo `docker-compose.prod.yml`**:
   ```yaml
   version: '3.8'
   services:
     postgis:
       image: postgis/postgis:15-3.3
       environment:
         POSTGRES_DB: GIS
         POSTGRES_USER: manuel
         POSTGRES_PASSWORD: ${POSTGIS_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/01-init.sql
       networks:
         - gis-network

     gis-app:
       build: .
       depends_on:
         - postgis
       environment:
         POSTGIS_HOST=postgis
         POSTGIS_DATABASE=${POSTGIS_DATABASE}
         POSTGIS_USER=${POSTGIS_USER}
         POSTGIS_PASSWORD=${POSTGIS_PASSWORD}
         CATASTRO_OUTPUT_DIR=/app/descargas_catastro
       ports:
         - "8000:8000"
       networks:
         - gis-network

   volumes:
     postgres_data:
   networks:
     gis-network:
   ```

2. **Configura en EasyPanel**:
   - Environment variables en EasyPanel UI
   - Docker compose como deployment method

### Opción C: SQL Manual en pgAdmin (si EasyPanel lo soporta)

1. Accede a pgAdmin (si está disponible en EasyPanel)
2. Conecta al servidor PostGIS
3. Abre Query Tool
4. Copia/pega el contenido de `scripts/init_db.sql`
5. Ejecuta

---

## ✓ Verificar la Instalación

### Desde la Línea de Comandos

```bash
# Conectar a la base de datos
psql -h localhost -p 5432 -U manuel -d GIS

# Una vez conectado, ejecuta:
SELECT
    'Database' as componente,
    current_database() as valor
UNION ALL
SELECT
    'PostGIS Version',
    postgis_version()
UNION ALL
SELECT
    'Tables in capas',
    COUNT(*)::text
FROM information_schema.tables
WHERE table_schema = 'capas';
```

**Resultado esperado:**
```
 componente   |       valor
--------------+-------------------
 Database     | GIS
 PostGIS Vers | PostGIS 3.3.2
 Tables       | 12
```

### Desde Python

```python
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="GIS",
    user="manuel",
    password="tu_contraseña"
)

cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT COUNT(*) as tables FROM information_schema.tables WHERE table_schema='capas'")
result = cur.fetchone()
print(f"✓ Tablas creadas: {result['tables']}")

cur.execute("SELECT COUNT(*) as indices FROM pg_indexes WHERE schemaname='capas'")
result = cur.fetchone()
print(f"✓ Índices GIST: {result['indices']}")

conn.close()
```

### Desde FastAPI

Una vez que la API está corriendo, visita:

```
http://localhost:8000/api/v1/capas/disponibles
```

Deberías ver un JSON con las capas disponibles (aunque estén vacías de datos):

```json
{
  "capas": [
    {"nombre": "rednatura", "tipo": "postgis", "features": 0},
    {"nombre": "zonasinundables", "tipo": "postgis", "features": 0},
    ...
  ]
}
```

---

## 🐛 Troubleshooting

### Error: "Connection refused"

```
psql: error: FATAL: could not connect to server: Connection refused
```

**Solución:**
- Verifica que PostgreSQL está corriendo
- macOS: `brew services start postgresql`
- Ubuntu: `sudo systemctl start postgresql`
- Windows: Abre Services y verifica que "PostgreSQL" está iniciado

---

### Error: "role 'postgres' does not exist"

**Solución:**
```bash
# Crea el rol postgres
createuser -s -i -d -r -l -w postgres
```

---

### Error: "PostGIS extension not available"

```
ERROR: extension postgis is not installed
```

**Solución:**
- PostGIS no está instalado correctamente
- Ubuntu: `sudo apt-get install postgresql-postgis`
- macOS: `brew install postgis`
- Windows: Usa PostgreSQL Stack Builder para instalar PostGIS

---

### Error: "could not open relation with OID..."

**Solución:**
```bash
# Reinicia el servidor
psql -U postgres -d postgres -c "REINDEX DATABASE GIS;"
```

---

### Puerto 5432 en uso

```
psql: error: could not connect to server: ... Address already in use
```

**Solución:**
```bash
# Encuentra el proceso
lsof -i :5432

# Mata el proceso (macOS/Linux)
kill -9 <PID>

# O cambia el puerto en .env
POSTGIS_PORT=5433
```

---

## 📝 Próximos Pasos

Una vez que la BD está creada y funcionando:

1. **Cargar datos** desde FlatGeobuf/GeoPackage:
   ```bash
   python scripts/export_postgis_to_fgb.py
   # O convierte archivos existentes
   python scripts/convert_to_fgb.py
   ```

2. **Verificar el sistema**:
   ```bash
   python scripts/verify_system.py
   ```

3. **Iniciar la API**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **Probar endpoints**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/capas/disponibles
   ```

---

## 📚 Referencias

- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [PostGIS Docs](https://postgis.net/docs/)
- [Docker PostgreSQL](https://hub.docker.com/_/postgres)
- [EasyPanel Docs](https://easypanel.io/docs)

