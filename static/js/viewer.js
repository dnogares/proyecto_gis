/**
 * GIS Viewer v3.0 - Código Maestro Corregido
 * 
 * Características:
 * - Carga FlatGeobuf con flatgeobuf.deserialize(response.body) 
 * - Inicialización segura con DOMContentLoaded
 * - Manejo robusto de errores FGB
 * - Controles de dibujo integrados
 */

class GISViewer {
    constructor(mapId = 'map') {
        this.mapId = mapId;
        this.map = null;
        this.drawnItems = null;
        this.layers = {};
        this.colors = {
            rednatura: '#2E7D32',
            viaspocuarias: '#F57C00',
            espaciosnaturales: '#1976D2',
            masasagua: '#0288D1',
            zonasinundables: '#F44336'
        };

        this.layerNames = {
            rednatura: 'Red Natura 2000',
            viaspocuarias: 'Vías Pecuarias',
            espaciosnaturales: 'Espacios Naturales',
            masasagua: 'Masas de Agua',
            zonasinundables: 'Zonas Inundables'
        };

        // Estado de capas FGB disponibles
        this.fgbCapas = [];
        this.capasCargadas = new Set();
    }

    /**
     * Inicialización segura con DOMContentLoaded
     */
    async init() {
        console.log('🚀 Inicializando GIS Viewer v3.0...');

        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            await new Promise(resolve => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        }

        this.initMap();
        this.initDrawControls();
        await this.cargarCapasDisponibles();
        this.initLayerControls();

        this.showNotification('✅ Visor inicializado correctamente', 'success');
    }

    /**
     * Inicializar mapa base Leaflet
     */
    initMap() {
        // Crear mapa centrado en España
        this.map = L.map(this.mapId, {
            center: [40.4167, -3.7033],
            zoom: 6,
            zoomControl: true
        });

        // Capa base
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
            maxZoom: 19
        }).addTo(this.map);

        console.log('✅ Mapa inicializado');
    }

    /**
     * Inicializar controles de dibujo
     */
    initDrawControls() {
        // Configurar herramientas de dibujo
        this.drawnItems = new L.FeatureGroup();
        this.map.addLayer(this.drawnItems);

        const drawControl = new L.Control.Draw({
            edit: { featureGroup: this.drawnItems },
            draw: { 
                polygon: true, 
                polyline: false, 
                rectangle: true, 
                circle: false, 
                marker: false 
            }
        });
        this.map.addControl(drawControl);

        // SOLUCIÓN AL ERROR 'ON' de null: El evento se asigna DESPUÉS de crear el mapa
        this.map.on(L.Draw.Event.CREATED, (e) => {
            this.drawnItems.clearLayers(); // Limpiar dibujos previos
            const layer = e.layer;
            this.drawnItems.addLayer(layer);
            
            // Geometría lista para analizar
            const geometria = layer.toGeoJSON().geometry;
            console.log("📐 Geometría lista para analizar:", geometria);
        });

        console.log('✅ Controles de dibujo configurados');
    }

    /**
     * Cargar lista de capas FlatGeobuf disponibles desde API
     */
    async cargarCapasDisponibles() {
        try {
            const response = await fetch('/api/v1/capas/fgb');
            const data = await response.json();

            this.fgbCapas = data.capas || [];

            console.log(`📊 ${this.fgbCapas.length} capas FlatGeobuf disponibles`);

            if (this.fgbCapas.length === 0) {
                console.warn('⚠️  No hay capas FGB disponibles');
                this.showNotification('⚠️ No hay capas FlatGeobuf disponibles', 'warning');
            }

        } catch (error) {
            console.error('❌ Error cargando capas FGB:', error);
            this.fgbCapas = [];
        }
    }

    /**
     * Inicializar controles de capas
     */
    initLayerControls() {
        const layerList = document.getElementById('layer-list') || document.getElementById('capasList');

        if (!layerList) {
            console.warn('⚠️ Elemento de lista de capas no encontrado');
            return;
        }

        // Limpiar lista existente
        layerList.innerHTML = '';

        // Añadir botones para capas FGB disponibles
        this.fgbCapas.forEach(capa => {
            const btn = document.createElement('button');
            btn.className = 'btn-capa';
            btn.innerHTML = `<span>📁</span> ${capa.nombre}`;
            btn.style.cssText = `
                display: block;
                width: 100%;
                margin: 5px 0;
                padding: 8px 12px;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                text-align: left;
            `;
            
            btn.onclick = () => this.cargarCapaIndividual(capa.nombre, capa.url);
            btn.onmouseover = () => btn.style.background = '#e9ecef';
            btn.onmouseout = () => btn.style.background = '#f8f9fa';
            
            layerList.appendChild(btn);
        });

        console.log('✅ Controles de capas inicializados');
    }

    /**
     * Cargar capa individual con FlatGeobuf (Código Maestro)
     */
    async cargarCapaIndividual(nombre, url) {
        console.log(`🔄 Descargando binario FGB: ${nombre}`);
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error("Error en la descarga");

            // IMPORTANTE: flatgeobuf.deserialize espera el body de la respuesta
            const iter = flatgeobuf.deserialize(response.body);
            
            const fgLayer = L.geoJSON(null, {
                style: { 
                    color: this.getColorForLayer(nombre), 
                    weight: 2, 
                    fillOpacity: 0.3 
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`<b>Capa:</b> ${nombre}`);
                }
            }).addTo(this.map);

            // Leemos el stream binario
            let featureCount = 0;
            for await (let feature of iter) {
                fgLayer.addData(feature);
                featureCount++;
            }
            
            console.log(`✅ Capa ${nombre} renderizada con éxito (${featureCount} elementos)`);
            
            // Zoom a la capa
            if (featureCount > 0) {
                this.map.fitBounds(fgLayer.getBounds());
            }

            this.showNotification(`✅ ${nombre}: ${featureCount} elementos cargados`, 'success');

        } catch (error) {
            console.error("❌ Fallo crítico cargando FGB:", error);
            this.showNotification(`❌ Error cargando ${nombre}`, 'error');
        }
    }

    /**
     * Obtener color para capa
     */
    getColorForLayer(nombre) {
        const colors = {
            'rednatura': '#2E7D32',
            'vias': '#F57C00',
            'espacios': '#1976D2',
            'agua': '#0288D1',
            'inund': '#F44336',
            'monte': '#228B22',
            'cultural': '#9B59B6',
            'sismico': '#E74C3C',
            'desert': '#F39C12',
            'volcan': '#8B0000'
        };

        for (const [key, color] of Object.entries(colors)) {
            if (nombre.toLowerCase().includes(key)) return color;
        }

        return '#666666'; // Gris por defecto
    }

    /**
     * Cargar referencia catastral
     */
    async cargarReferencia(ref) {
        if (!ref) {
            this.showNotification('Por favor, introduce una referencia catastral', 'warning');
            return null;
        }
        
        try {
            const response = await fetch(`/api/v1/catastro/geometria/${encodeURIComponent(ref)}?formatos=geojson`);
            if (!response.ok) {
                throw new Error('Referencia no encontrada');
            }
            
            const data = await response.json();
            const geojson = data.geojson;
            
            if (!geojson) throw new Error('No se recibió geometría GeoJSON');

            const layer = L.geoJSON(geojson, {
                style: {
                    color: '#e74c3c',
                    weight: 3,
                    fillOpacity: 0.3
                }
            }).addTo(this.map);
            
            // Centrar mapa en la referencia
            const bounds = layer.getBounds();
            this.map.fitBounds(bounds);
            
            this.showNotification(`✅ Referencia ${ref} cargada`, 'success');
            return data;
            
        } catch (error) {
            console.error('Error cargando referencia:', error);
            this.showNotification('Error cargando referencia', 'error');
            return null;
        }
    }

    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Crear elemento de notificación si no existe
        let notification = document.getElementById('notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
                z-index: 10000;
                display: none;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            `;
            document.body.appendChild(notification);
        }

        notification.textContent = message;
        notification.style.display = 'block';

        // Colores según tipo
        const colors = {
            success: { bg: '#4CAF50', color: 'white' },
            error: { bg: '#F44336', color: 'white' },
            warning: { bg: '#FF9800', color: 'white' },
            info: { bg: '#2196F3', color: 'white' }
        };

        const style = colors[type] || colors.info;
        notification.style.background = style.bg;
        notification.style.color = style.color;

        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }
}

