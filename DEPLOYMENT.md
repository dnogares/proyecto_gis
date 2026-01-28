# 🚀 Deployment en EasyPanel

Guía completa para desplegar tu aplicación GIS en EasyPanel.

---

## 📋 Pre-requisitos

1. **Cuenta en EasyPanel**
2. **Repositorio en GitHub** con el código
3. **(Opcional) Servidor PostgreSQL/PostGIS**

---

## 🔧 Paso 1: Preparar el Repositorio

### 1.1 Verificar Archivos Necesarios

Tu repositorio debe contener:

```
✅ Dockerfile              # Configuración de Docker
✅ requirements.txt        # Dependencias de Python
✅ main.py                 # Aplicación principal
✅ .dockerignore          # Archivos a excluir
✅ docker-compose.yml     # Para testing local
✅ start.sh               # Script de inicio (opcional)
```

### 1.2 Commit y Push

```bash
git add .
git commit -m "Add Docker configuration for EasyPanel"
git push origin main
```

---

## 🌐 Paso 2: Crear Servicio en EasyPanel

### 2.1 Nuevo Servicio

1. Login en EasyPanel
2. Click en **"Create Service"** o **"+"**
3. Seleccionar **"App"**
4. Seleccionar **"GitHub"**

### 2.2 Conectar GitHub

1. Autorizar EasyPanel en GitHub
2. Seleccionar tu repositorio: `tu-usuario/proyecto_gis`
3. Branch: `main`

### 2.3 Configuración Básica

| Campo | Valor |
|-------|-------|
| **Service Name** | `gis-api` o `webgis` |
| **Port** | `8000` |
| **Health Check Path** | `/health` |
| **Build Command** | (vacío - usa Dockerfile) |
| **Start Command** | (vacío - usa Dockerfile) |

---

## 🔐 Paso 3: Variables de Entorno

### 3.1 Variables Obligatorias (Si usas PostGIS externo)

En EasyPanel → Tu servicio → Settings → Environment Variables:

```env
POSTGIS_HOST=tu-servidor.com
POSTGIS_DATABASE=GIS
POSTGIS_USER=tu_usuario
POSTGIS_PASSWORD=tu_password
POSTGIS_PORT=5432
```

### 3.2 Variables Opcionales

```env
DEBUG=false
LOG_LEVEL=info
WORKERS=4
```

### 3.3 Sin PostGIS

Si **NO** tienes PostgreSQL, déjalo así:
- El sistema funciona perfectamente con solo FlatGeobuf
- No necesitas configurar variables de PostGIS

---

## 💾 Paso 4: Volúmenes Persistentes (Recomendado)

Para que tus datos persistan entre deployments:

### 4.1 Crear Volumen para Capas

En EasyPanel → Tu servicio → Volumes:

| Campo | Valor |
|-------|-------|
| **Mount Path** | `/app/capas` |
| **Size** | `5 GB` |

### 4.2 Crear Volumen para Descargas

| Campo | Valor |
|-------|-------|
| **Mount Path** | `/app/descargas_catastro` |
| **Size** | `10 GB` |

---

## 🌍 Paso 5: Configurar Dominio

### 5.1 Dominio de EasyPanel

EasyPanel te da un subdominio automático:
```
https://gis-api-xxxxx.easypanel.host
```

### 5.2 Dominio Personalizado (Opcional)

1. Ve a **Domains** en tu servicio
2. Click **"Add Domain"**
3. Introduce: `gis.tudominio.com`
4. Configura DNS:
   ```
   Tipo: CNAME
   Nombre: gis
   Valor: [proporcionado por EasyPanel]
   ```

5. **SSL automático** con Let's Encrypt

---

## 🚀 Paso 6: Deploy

1. Click en **"Deploy"**
2. Esperar build (3-5 minutos primera vez)
3. Verificar logs en tiempo real

### Logs Esperados:

```
✅ Conexión PostGIS exitosa (o warning si no está configurado)
✅ DataSourceManager inicializado
✅ Analizadores inicializados
✅ Servicio completo de Catastro inicializado
✅ Uvicorn running on http://0.0.0.0:8000
```

---

## ✅ Paso 7: Verificar Deployment

### 7.1 Health Check

```bash
curl https://tu-app.easypanel.host/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T...",
  "postgis": true,
  "capas_fgb": 0,
  "capas_postgis": 0
}
```

### 7.2 Abrir en Navegador

```
https://tu-app.easypanel.host/
```

Deberías ver el visor GIS.

### 7.3 Verificar API

```
https://tu-app.easypanel.host/docs
```

Documentación Swagger interactiva.

---

## 📊 Paso 8: Subir Capas FlatGeobuf

### 8.1 Vía SFTP (Si EasyPanel lo soporta)

```bash
sftp usuario@tu-servidor
cd /app/capas/fgb
put rednatura.fgb
put viaspocuarias.fgb
```

### 8.2 Vía API (Futuro)

Crear endpoint para subir capas vía HTTP.

### 8.3 Desde PostGIS (Si tienes)

1. Configurar conexión a tu PostGIS externo
2. Ejecutar desde dentro del contenedor:

```bash
# Entrar al contenedor
docker exec -it tu-contenedor bash

# Exportar capas
python scripts/export_postgis_to_fgb.py
```

---

## 🔄 Actualizaciones Automáticas

### Configurar Auto-Deploy

En EasyPanel → Tu servicio → Settings:

1. **Auto Deploy:** ON
2. **Branch:** main
3. **Trigger:** Push to main

Ahora cada `git push` desplegará automáticamente.

---

## 📈 Monitoreo

### Logs en Tiempo Real

```
EasyPanel → Tu servicio → Logs
```

### Métricas

```
EasyPanel → Tu servicio → Metrics
```

- CPU Usage
- Memory Usage
- Network I/O

---

## 🔧 Troubleshooting

### Error: failed to read dockerfile

**Causa:** Falta `Dockerfile` en el repo

**Solución:**
```bash
# Verificar que existe
ls -la Dockerfile

# Si no existe, descarga el ZIP actualizado
# que ya lo incluye
```

### Error: Module not found

**Causa:** Dependencia faltante en `requirements.txt`

**Solución:**
```bash
# Verificar requirements.txt
cat requirements.txt

# Añadir dependencia faltante
echo "nombre-paquete==version" >> requirements.txt
git commit -am "Add missing dependency"
git push
```

### Error: PostGIS connection failed

**Causa:** Variables de entorno incorrectas

**Solución:**
1. Verificar variables en EasyPanel
2. O deshabilitar PostGIS (funciona sin él)

### Build muy lento

**Causa:** Instalación de GDAL tarda ~2-3 min

**Solución:** Es normal la primera vez. Builds subsecuentes usan cache.

### Out of memory

**Causa:** Workers demasiados o RAM insuficiente

**Solución:**
```env
# Reducir workers
WORKERS=2
```

O aumentar RAM del servicio en EasyPanel.

---

## 🎯 Recursos Recomendados

| Usuarios Concurrentes | CPU | RAM | Disco |
|----------------------|-----|-----|-------|
| 1-10 | 0.5 | 1 GB | 10 GB |
| 10-50 | 1 | 2 GB | 20 GB |
| 50-100 | 2 | 4 GB | 50 GB |
| 100+ | 4+ | 8 GB+ | 100 GB+ |

---

## 🔒 Seguridad

### 1. Cambiar Password de PostGIS

```env
POSTGIS_PASSWORD=un_password_muy_seguro_aleatorio_12345
```

### 2. Configurar CORS

En `main.py`, línea ~38:

```python
origins = [
    "https://tu-dominio.com",
    "https://www.tu-dominio.com"
]
```

### 3. Habilitar HTTPS

EasyPanel lo hace automáticamente con Let's Encrypt.

### 4. Rate Limiting

Considerar añadir rate limiting para la API de Catastro.

---

## 📝 Checklist Final

Antes de ir a producción:

- [ ] Dockerfile commiteado
- [ ] Variables de entorno configuradas
- [ ] Volúmenes creados
- [ ] Health check funciona
- [ ] Dominio configurado
- [ ] SSL activo
- [ ] Logs sin errores
- [ ] Capas subidas
- [ ] API documentada
- [ ] Backups configurados

---

## 🎉 ¡Listo!

Tu sistema GIS está ahora desplegado en EasyPanel y accesible desde internet.

**URLs importantes:**
- **App:** `https://tu-app.easypanel.host/`
- **API Docs:** `https://tu-app.easypanel.host/docs`
- **Health:** `https://tu-app.easypanel.host/health`

**Dashboard EasyPanel:** `https://easypanel.io/dashboard`

---

## 📞 Soporte

- **EasyPanel Docs:** https://easypanel.io/docs
- **GitHub Issues:** Reportar problemas en tu repo
- **Logs:** Siempre revisar logs primero

---

**¡Tu GIS API está ahora en producción! 🚀**
