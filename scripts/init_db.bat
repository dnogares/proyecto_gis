@echo off
REM ============================================================================
REM SCRIPT DE INICIALIZACIÓN - GIS API v2.0 (Windows)
REM Crea base de datos PostGIS desde cero
REM ============================================================================
REM
REM USO:
REM   init_db.bat
REM
REM O con parámetros:
REM   init_db.bat -host localhost -port 5432 -user postgres
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM Variables por defecto
set "PGHOST=localhost"
set "PGPORT=5432"
set "PGUSER=postgres"
set "PGPASSWORD="
set "DB_USER=manuel"
set "DB_NAME=GIS"
set "RESET_DB=false"

REM Parsear argumentos
:parse_args
if "%~1"=="" goto start_init
if "%~1"=="-host" (
    set "PGHOST=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="-port" (
    set "PGPORT=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="-user" (
    set "PGUSER=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="-password" (
    set "PGPASSWORD=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="-reset" (
    set "RESET_DB=true"
    shift
    goto parse_args
)
shift
goto parse_args

:start_init
cls
color 0A
echo.
echo =============================================================================
echo GIS API v2.0 - Database Initialization (Windows)
echo =============================================================================
echo.
echo Configuracion:
echo   Host: %PGHOST%
echo   Puerto: %PGPORT%
echo   Usuario: %PGUSER%
echo   Base de datos: %DB_NAME%
echo   Owner: %DB_USER%
echo.

REM Verificar si psql está disponible
echo [1/5] Verificando disponibilidad de PostgreSQL...
where psql > nul 2>&1
if errorlevel 1 (
    color 0C
    echo Error: psql no encontrado en PATH
    echo.
    echo Asegúrate de que PostgreSQL está instalado y psql está en el PATH
    echo Ejemplo: C:\Program Files\PostgreSQL\15\bin
    pause
    exit /b 1
)
echo [OK] PostgreSQL encontrado

REM Verificar conexión
echo.
echo [2/5] Probando conexión a PostgreSQL...
set "PGPASSWORD=%PGPASSWORD%"
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres -c "SELECT 1" > nul 2>&1
if errorlevel 1 (
    color 0C
    echo Error: No se puede conectar a PostgreSQL
    echo.
    echo Verifica:
    echo   - PostgreSQL está ejecutándose en %PGHOST%:%PGPORT%
    echo   - Usuario %PGUSER% existe
    echo   - Contraseña correcta (si es necesaria)
    pause
    exit /b 1
)
echo [OK] Conexión exitosa

REM Verificar PostGIS
echo.
echo [3/5] Verificando PostGIS...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;" > nul 2>&1
if errorlevel 1 (
    color 0C
    echo Error: PostGIS no disponible
    echo.
    echo Instala PostGIS:
    echo   Windows: Descarga desde postgresql.org - Stack Builder
    pause
    exit /b 1
)
echo [OK] PostGIS disponible

REM Crear usuario si no existe
echo.
echo [4/5] Verificando usuario %DB_USER%...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres ^
    -c "SELECT 1 FROM pg_user WHERE usename='%DB_USER%'" 2>nul | find "1" > nul 2>&1
if errorlevel 1 (
    echo   Creando usuario %DB_USER%...
    psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres ^
        -c "CREATE USER %DB_USER% WITH CREATEDB CREATEROLE;" > nul 2>&1
)
echo [OK] Usuario %DB_USER% verificado

REM Eliminar BD anterior si RESET_DB=true
if "%RESET_DB%"=="true" (
    echo.
    echo [5/5] Eliminando base de datos anterior...
    psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres ^
        -c "DROP DATABASE IF EXISTS %DB_NAME%;" > nul 2>&1
    echo [OK] Base de datos eliminada
)

REM Ejecutar script SQL
echo.
echo [5/5] Ejecutando script de inicialización...
if not exist "scripts\init_db.sql" (
    color 0C
    echo Error: scripts\init_db.sql no encontrado
    echo.
    echo Asegúrate de ejecutar este script desde la raíz del proyecto
    pause
    exit /b 1
)

psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres -f scripts\init_db.sql
if errorlevel 1 (
    color 0C
    echo Error ejecutando script SQL
    pause
    exit /b 1
)

echo.
color 0A
echo =============================================================================
echo INICIALIZACIÓN COMPLETADA
echo =============================================================================
echo.
echo Proximo paso: Configura .env con tus credenciales
echo.
echo Ejemplo:
echo   POSTGIS_HOST=%PGHOST%
echo   POSTGIS_PORT=%PGPORT%
echo   POSTGIS_DATABASE=%DB_NAME%
echo   POSTGIS_USER=%DB_USER%
echo   POSTGIS_PASSWORD=tu_contraseña
echo.
echo Luego inicia la API:
echo   python main.py
echo.
pause
endlocal
