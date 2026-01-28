/**
 * GIS Viewer v2.0 - Con soporte FlatGeobuf
 * 
 * Características:
 * - Carga FlatGeobuf directamente desde navegador (HTTP Range)
 * - Streaming de features (no espera descarga completa)
 * - Actualización dinámica al mover mapa (solo carga visible)
 * - Fallback a GeoJSON API si FGB no disponible
 */

class GISViewer {
    constructor(mapId = 'map') {
        this.mapId = mapId;
        this.map = null;
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
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Inicializando GIS Viewer v2.0...');
        
        this.initMap();
        await this.cargarCapasDisponibles();
        this.initLayerControls();
        
        this.showNotification('✅ Visor inicializado correctamente', 'success');
    }
    
    /**
     * Inicializar mapa base Leaflet
     */
    initMap() {
        // Crear mapa centrado en Almería
        this.map = L.map(this.mapId, {
            center: [36.8381, -2.4597],
            zoom: 10,
            zoomControl: true
        });
        
        // Capas base
        const osm = L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }
        );
        
        const satellite = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            {
                attribution: 'Esri',
                maxZoom: 19
            }
        );
        
        const topo = L.tileLayer(
            'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            {
                attribution: 'Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap',
                maxZoom: 17
            }
        );
        
        // Añadir OSM por defecto
        osm.addTo(this.map);
        
        // Control de capas base
        L.control.layers({
            'OpenStreetMap': osm,
            'Satélite': satellite,
            'Topográfico': topo
        }, null, {
            position: 'topright'
        }).addTo(this.map);
        
        // Escala
        L.control.scale({
            position: 'bottomleft',
            imperial: false
        }).addTo(this.map);
        
        console.log('✅ Mapa inicializado');
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
                console.warn('⚠️  No hay capas FGB, usando fallback GeoJSON');
                this.showNotification('⚠️ No hay capas FlatGeobuf. Usando modo fallback.', 'warning');
            }
            
        } catch (error) {
            console.warn('⚠️  Error cargando capas FGB:', error);
            this.fgbCapas = [];
        }
    }
    
    /**
     * Inicializar controles de capas
     */
    initLayerControls() {
        const layerList = document.getElementById('layer-list');
        
        if (!layerList) {
            console.error('❌ Elemento #layer-list no encontrado');
            return;
        }
        
        // Capas por defecto
        const capasDefecto = [
            'rednatura',
            'viaspocuarias',
            'espaciosnaturales',
            'masasagua',
            'zonasinundables'
        ];
        
        capasDefecto.forEach(nombre => {
            const div = document.createElement('div');
            div.className = 'layer-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `layer-${nombre}`;
            checkbox.addEventListener('change', (e) => {
                this.toggleLayer(nombre, e.target.checked);
            });
            
            const color = this.colors[nombre] || '#666666';
            const colorBox = document.createElement('span');
            colorBox.className = 'layer-color';
            colorBox.style.backgroundColor = color;
            
            const label = document.createElement('label');
            label.htmlFor = `layer-${nombre}`;
            label.appendChild(colorBox);
            label.appendChild(document.createTextNode(this.layerNames[nombre] || nombre));
            
            div.appendChild(checkbox);
            div.appendChild(label);
            layerList.appendChild(div);
        });
        
        console.log('✅ Controles de capas inicializados');
    }
    
    /**
     * Toggle capa on/off
     */
    async toggleLayer(nombre, visible) {
        if (visible) {
            await this.loadLayer(nombre);
        } else {
            this.removeLayer(nombre);
        }
    }
    
    /**
     * Cargar capa (intenta FlatGeobuf primero, fallback a GeoJSON)
     */
    async loadLayer(nombre) {
        if (this.capasCargadas.has(nombre)) {
            console.log(`ℹ️  Capa ${nombre} ya está cargada`);
            return;
        }
        
        this.showLoading(`Cargando ${this.layerNames[nombre]}...`);
        
        try {
            // Verificar si existe FGB
            const fgbInfo = this.fgbCapas.find(c => c.nombre === nombre);
            
            if (fgbInfo && typeof flatgeobuf !== 'undefined') {
                // Cargar desde FlatGeobuf (RÁPIDO)
                await this.loadFromFlatGeobuf(nombre, fgbInfo);
            } else {
                // Fallback a GeoJSON API
                await this.loadFromGeoJSON(nombre);
            }
            
            this.capasCargadas.add(nombre);
            
        } catch (error) {
            console.error(`❌ Error cargando ${nombre}:`, error);
            this.showNotification(`❌ Error cargando ${this.layerNames[nombre]}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Cargar capa desde FlatGeobuf con streaming
     */
    async loadFromFlatGeobuf(nombre, info) {
        const url = info.url;
        const color = this.colors[nombre] || '#666666';
        
        console.log(`📥 Cargando ${nombre} desde FlatGeobuf (${info.size_mb} MB)...`);
        
        // Obtener bounds actuales del mapa
        const bounds = this.map.getBounds();
        const bbox = {
            minX: bounds.getWest(),
            minY: bounds.getSouth(),
            maxX: bounds.getEast(),
            maxY: bounds.getNorth()
        };
        
        // Crear layer group para esta capa
        const layerGroup = L.layerGroup().addTo(this.map);
        this.layers[nombre] = layerGroup;
        
        let featureCount = 0;
        const startTime = Date.now();
        
        try {
            // Streaming de features desde FlatGeobuf
            const iter = flatgeobuf.deserialize(url, bbox);
            
            for await (let feature of iter) {
                // Añadir feature al mapa
                const geoJsonLayer = L.geoJSON(feature, {
                    style: {
                        color: color,
                        weight: 2,
                        opacity: 0.8,
                        fillOpacity: 0.2
                    },
                    onEachFeature: (f, layer) => {
                        this.bindPopup(f, layer, nombre);
                    }
                });
                
                geoJsonLayer.addTo(layerGroup);
                
                featureCount++;
                
                // Limitar features para evitar sobrecargar el navegador
                if (featureCount >= 1000) {
                    console.warn(`⚠️  Límite de 1000 features alcanzado para ${nombre}`);
                    break;
                }
            }
            
            const loadTime = ((Date.now() - startTime) / 1000).toFixed(2);
            
            console.log(
                `✅ ${nombre}: ${featureCount} features en ${loadTime}s desde FlatGeobuf`
            );
            
            this.showNotification(
                `✅ ${this.layerNames[nombre]}: ${featureCount} elementos (${loadTime}s)`,
                'success'
            );
            
            // Zoom a la capa si es la primera
            if (featureCount > 0 && this.capasCargadas.size === 0) {
                this.map.fitBounds(layerGroup.getBounds(), { padding: [50, 50] });
            }
            
        } catch (error) {
            console.warn(`⚠️  Error con FlatGeobuf, usando fallback:`, error);
            // Intentar fallback a GeoJSON
            layerGroup.clearLayers();
            this.map.removeLayer(layerGroup);
            delete this.layers[nombre];
            await this.loadFromGeoJSON(nombre);
        }
    }
    
    /**
     * Cargar capa desde API GeoJSON (fallback)
     */
    async loadFromGeoJSON(nombre) {
        const color = this.colors[nombre] || '#666666';
        
        console.log(`📥 Cargando ${nombre} desde GeoJSON API...`);
        
        const startTime = Date.now();
        
        try {
            const response = await fetch(`/api/v1/analisis/obtener-capa`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    nombre_capa: nombre,
                    bbox: null
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const geojsonText = await response.text();
            const geojson = JSON.parse(geojsonText);
            
            // Crear layer
            const layer = L.geoJSON(geojson, {
                style: {
                    color: color,
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.2
                },
                onEachFeature: (f, layer) => {
                    this.bindPopup(f, layer, nombre);
                }
            }).addTo(this.map);
            
            this.layers[nombre] = layer;
            
            const loadTime = ((Date.now() - startTime) / 1000).toFixed(2);
            const featureCount = layer.getLayers().length;
            
            console.log(
                `✅ ${nombre}: ${featureCount} features desde API en ${loadTime}s`
            );
            
            this.showNotification(
                `✅ ${this.layerNames[nombre]}: ${featureCount} elementos (${loadTime}s, API)`,
                'success'
            );
            
            // Zoom a la capa si es la primera
            if (featureCount > 0 && this.capasCargadas.size === 0) {
                this.map.fitBounds(layer.getBounds(), { padding: [50, 50] });
            }
            
        } catch (error) {
            console.error(`❌ Error con API:`, error);
            throw error;
        }
    }
    
    /**
     * Remover capa del mapa
     */
    removeLayer(nombre) {
        const layer = this.layers[nombre];
        if (layer) {
            this.map.removeLayer(layer);
            delete this.layers[nombre];
            this.capasCargadas.delete(nombre);
            console.log(`🗑️  Capa ${nombre} removida`);
        }
    }
    
    /**
     * Bind popup a feature
     */
    bindPopup(feature, layer, layerName) {
        const props = feature.properties || {};
        
        let content = `<div style="max-width: 250px;">`;
        content += `<h4 style="margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">${this.layerNames[layerName]}</h4>`;
        
        // Mostrar primeras 5 propiedades
        const entries = Object.entries(props).slice(0, 5);
        
        if (entries.length > 0) {
            content += '<table style="width: 100%; font-size: 12px; border-collapse: collapse;">';
            
            entries.forEach(([key, value]) => {
                content += `
                    <tr>
                        <td style="padding: 3px 5px; font-weight: 600; border-bottom: 1px solid #eee;">${key}:</td>
                        <td style="padding: 3px 5px; border-bottom: 1px solid #eee;">${value || 'N/A'}</td>
                    </tr>
                `;
            });
            
            content += '</table>';
        }
        
        if (Object.keys(props).length > 5) {
            content += `<p style="margin: 8px 0 0 0; font-size: 11px; color: #666; font-style: italic;">
                ...y ${Object.keys(props).length - 5} campos más
            </p>`;
        }
        
        content += '</div>';
        
        layer.bindPopup(content);
    }
    
    /**
     * Mostrar loading
     */
    showLoading(message) {
        const loading = document.getElementById('loading');
        const loadingText = document.getElementById('loading-text');
        
        if (loading && loadingText) {
            loadingText.textContent = message;
            loading.style.display = 'block';
        }
    }
    
    /**
     * Ocultar loading
     */
    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }
    
    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        
        if (notification) {
            notification.textContent = message;
            notification.style.display = 'block';
            
            // Colores según tipo
            if (type === 'success') {
                notification.style.background = '#4CAF50';
                notification.style.color = 'white';
            } else if (type === 'error') {
                notification.style.background = '#F44336';
                notification.style.color = 'white';
            } else if (type === 'warning') {
                notification.style.background = '#FF9800';
                notification.style.color = 'white';
            } else {
                notification.style.background = 'white';
                notification.style.color = 'black';
            }
            
            // Auto-ocultar después de 3 segundos
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando GIS Viewer v2.0 con FlatGeobuf...');
    
    // Verificar que flatgeobuf esté cargado
    if (typeof flatgeobuf === 'undefined') {
        console.error('❌ FlatGeobuf library no cargada!');
        console.error('Añadir: <script src="https://unpkg.com/flatgeobuf@3.27.2/dist/flatgeobuf-geojson.min.js"></script>');
        alert('⚠️ FlatGeobuf no cargado. El visor funcionará en modo fallback (más lento).');
    } else {
        console.log('✅ FlatGeobuf cargado - Streaming HTTP Range disponible');
    }
    
    // Verificar Leaflet
    if (typeof L === 'undefined') {
        console.error('❌ Leaflet no cargado!');
        alert('❌ Error: Leaflet no cargado. El visor no funcionará.');
        return;
    } else {
        console.log('✅ Leaflet cargado');
    }
    
    // Crear visor
    window.gisViewer = new GISViewer('map');
    
    console.log('✅ GIS Viewer inicializado correctamente');
    console.log('💡 Activa capas desde el panel de la izquierda');
});
