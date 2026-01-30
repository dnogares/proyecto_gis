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
        if (!document.getElementById(this.mapId)) {
            console.warn(`⚠️ Contenedor de mapa #${this.mapId} no encontrado`);
            return;
        }

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
        if (!this.map) return;

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

        this.map.on(L.Draw.Event.CREATED, (e) => {
            this.drawnItems.clearLayers();
            const layer = e.layer;
            this.drawnItems.addLayer(layer);
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
        } catch (error) {
            console.error('❌ Error cargando capas FGB:', error);
            this.fgbCapas = [];
        }
    }

    /**
     * Inicializar controles de capas
     */
    initLayerControls() {
        // Soporte para múltiples IDs de contenedores usados en diferentes plantillas
        const containerIds = ['layer-list', 'capasList', 'capasContainer'];
        let layerList = null;

        for (const id of containerIds) {
            layerList = document.getElementById(id);
            if (layerList) break;
        }

        if (!layerList) {
            console.debug('ℹ️ No se encontró contenedor para la lista de capas');
            return;
        }

        layerList.innerHTML = '';
        if (this.fgbCapas.length === 0) {
            layerList.innerHTML = '<p style="color: #666; font-size: 12px; padding: 10px;">No hay capas disponibles</p>';
            return;
        }

        this.fgbCapas.forEach(capa => {
            const btn = document.createElement('button');
            btn.className = 'btn-capa';
            btn.innerHTML = `<span>📁</span> ${capa.nombre}`;
            btn.style.cssText = `display: block; width: 100%; margin: 5px 0; padding: 8px 12px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; cursor: pointer; font-size: 12px; text-align: left;`;
            btn.onclick = () => this.cargarCapaIndividual(capa.nombre, capa.url);
            layerList.appendChild(btn);
        });
    }

    /**
     * Alternar visibilidad de una capa
     */
    async toggleLayer(layerId, visible) {
        if (visible) {
            await this.loadLayer(layerId);
        } else {
            this.removeLayer(layerId);
        }
    }

    /**
     * Cargar una capa por su ID o nombre
     */
    async loadLayer(layerId) {
        if (this.layers[layerId] && this.map.hasLayer(this.layers[layerId])) return;

        const capa = this.fgbCapas.find(c => c.nombre.toLowerCase().includes(layerId.toLowerCase()));
        const url = capa ? capa.url : `/capas/fgb/${layerId}.fgb`;
        const nombre = capa ? capa.nombre : layerId;

        return await this.cargarCapaIndividual(nombre, url, layerId);
    }

    /**
     * Remover una capa del mapa
     */
    removeLayer(layerId) {
        if (this.layers[layerId]) {
            this.map.removeLayer(this.layers[layerId]);
            delete this.layers[layerId];
            this.showNotification(`🗑️ Capa ${layerId} removida`, 'info');
        }
    }

    /**
     * Cargar capa individual con FlatGeobuf
     */
    async cargarCapaIndividual(nombre, url, layerId = null) {
        if (!this.map) return;
        if (typeof flatgeobuf === 'undefined') {
            this.showNotification('❌ Error: Librería FlatGeobuf no cargada', 'error');
            return;
        }
        const id = layerId || nombre;
        console.log(`🔄 Descargando FGB: ${nombre} desde ${url}`);
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error("Error en la descarga");

            const loading = document.getElementById('loading');
            if (loading) loading.classList.add('active');

            const iter = flatgeobuf.deserialize(response.body);
            const fgLayer = L.geoJSON(null, {
                style: { color: this.getColorForLayer(nombre), weight: 2, fillOpacity: 0.3 },
                onEachFeature: (feature, layer) => {
                    let popup = `<b>Capa:</b> ${nombre}`;
                    if (feature.properties) {
                        popup += '<br><hr>';
                        Object.entries(feature.properties).slice(0, 10).forEach(([k, v]) => {
                            popup += `<br><b>${k}:</b> ${v}`;
                        });
                    }
                    layer.bindPopup(popup);
                }
            }).addTo(this.map);

            let count = 0;
            for await (let feature of iter) {
                fgLayer.addData(feature);
                count++;
            }
            
            this.layers[id] = fgLayer;
            if (count > 0) this.map.fitBounds(fgLayer.getBounds());
            if (loading) loading.classList.remove('active');
            this.showNotification(`✅ ${nombre}: ${count} elementos`, 'success');
            return fgLayer;
        } catch (error) {
            console.error("❌ Error FGB:", error);
            if (loading) loading.classList.remove('active');
            this.showNotification(`❌ Error cargando ${nombre}`, 'error');
        }
    }

    getColorForLayer(nombre) {
        const colors = { 'rednatura': '#2E7D32', 'vias': '#F57C00', 'espacios': '#1976D2', 'agua': '#0288D1', 'inund': '#F44336' };
        for (const [key, color] of Object.entries(colors)) { if (nombre.toLowerCase().includes(key)) return color; }
        return '#666666';
    }

    async cargarReferencia(ref) {
        if (!ref || !this.map) return;
        try {
            const response = await fetch(`/api/v1/referencia/${encodeURIComponent(ref)}/geojson`);
            if (!response.ok) throw new Error(`Referencia ${ref} no encontrada`);
            const geojson = await response.json();
            const layer = L.geoJSON(geojson, {
                style: { color: '#e74c3c', weight: 3, fillOpacity: 0.3 },
                onEachFeature: (f, l) => l.bindPopup(`<b>Ref:</b> ${ref}`)
            }).addTo(this.map);
            this.layers[`ref_${ref}`] = layer;
            this.map.fitBounds(layer.getBounds());
            this.showNotification(`✅ Referencia ${ref} cargada`, 'success');
        } catch (error) {
            this.showNotification(`❌ Error: ${error.message}`, 'error');
        }
    }

    limpiarMapa() {
        if (!this.map) return;
        Object.keys(this.layers).forEach(id => this.map.removeLayer(this.layers[id]));
        this.layers = {};
        if (this.drawnItems) this.drawnItems.clearLayers();
        this.showNotification('🗑️ Mapa limpiado', 'info');
    }

    showNotification(message, type = 'info') {
        let n = document.getElementById('notification');
        if (!n) {
            n = document.createElement('div');
            n.id = 'notification';
            n.style.cssText = `position: fixed; top: 20px; right: 20px; padding: 12px 20px; border-radius: 4px; z-index: 10000; color: white; display: none;`;
            document.body.appendChild(n);
        }
        n.textContent = message;
        n.style.background = { success: '#4CAF50', error: '#F44336', warning: '#FF9800', info: '#2196F3' }[type] || '#2196F3';
        n.style.display = 'block';
        setTimeout(() => n.style.display = 'none', 3000);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // Evitar inicialización doble si ya existe gisViewer
    if (document.getElementById('map') && !window.gisViewer) {
        window.gisViewer = new GISViewer('map');
        await window.gisViewer.init();
    }
});
