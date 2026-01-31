#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para generación de informes urbanísticos
Obtiene información de clasificación, calificación y afecciones urbanísticas
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InformeUrbanistico:
    """Clase para generar informes urbanísticos completos"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el generador de informes urbanísticos
        
        Args:
            config_path: Ruta al archivo de configuración JSON
        """
        self.config = self._cargar_configuracion(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InformeUrbanistico/1.0',
            'Accept': 'application/json, application/xml'
        })
    
    def _cargar_configuracion(self, config_path: Optional[str]) -> Dict:
        """Carga la configuración desde archivo JSON"""
        config_default = {
            'urls': {
                'catastro': 'https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/',
                'inspire': 'https://inspire.catastro.es/inspire/wfs',
                'siu': 'https://services.arcgis.com/YWQjeT7gO1z78YVu/arcgis/rest/services/',
                'mapama': 'https://wms.mapama.gob.es/sig/Biodiversidad/'
            },
            'timeout': 30,
            'max_retries': 3
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
                config_default.update(custom_config)
        
        return config_default
    
    def generar_informe_completo(
        self, 
        ref_catastral: Optional[str] = None,
        provincia: Optional[str] = None,
        municipio: Optional[str] = None,
        via: Optional[str] = None,
        numero: Optional[str] = None
    ) -> Dict:
        """
        Genera un informe urbanístico completo
        
        Args:
            ref_catastral: Referencia catastral
            provincia: Nombre de la provincia
            municipio: Nombre del municipio
            via: Nombre de la vía
            numero: Número de la vía
            
        Returns:
            Diccionario con toda la información urbanística
        """
        logger.info(f"Generando informe para: {ref_catastral or (via + ' ' + numero)}")
        
        # Simulación de obtención de datos para el ejemplo
        # En una implementación real, aquí se llamarían a los servicios WFS/WMS
        
        resultado = {
            "estado": "completado",
            "fecha_generacion": datetime.now().isoformat(),
            "datos_catastrales": {
                "referencia": ref_catastral or "1234567VK1234N0001AB",
                "localizacion": f"{via or 'Calle Mayor'} {numero or '1'}, {municipio or 'Madrid'}",
                "superficie_suelo": 500,
                "uso_principal": "Residencial"
            },
            "urbanismo": {
                "clasificacion": "Suelo Urbano Consolidado",
                "calificacion": "Residencial Unifamiliar (R-1)",
                "edificabilidad": "0.6 m2t/m2s",
                "ocupacion_max": "40%",
                "altura_max": "7m (2 plantas)",
                "retranqueos": "3m a linderos"
            },
            "afecciones": [
                {"tipo": "Costas", "afectado": False},
                {"tipo": "Inundabilidad", "afectado": False},
                {"tipo": "Patrimonio", "afectado": True, "descripcion": "Entorno de protección BIC"},
                {"tipo": "Vías Pecuarias", "afectado": False}
            ]
        }
        
        return resultado

    def generar_informe_pdf(self, datos: Dict, output_path: str):
        """Simula la generación de un PDF"""
        logger.info(f"Generando PDF en {output_path}")
        with open(output_path, 'w') as f:
            f.write(f"Informe Urbanístico - {datos['datos_catastrales']['referencia']}")

    def generar_informe_kml(self, datos: Dict, output_path: str):
        """Simula la generación de un KML"""
        logger.info(f"Generando KML en {output_path}")
        with open(output_path, 'w') as f:
            f.write(f"<kml><Document><name>{datos['datos_catastrales']['referencia']}</name></Document></kml>")

def main():
    parser = argparse.ArgumentParser(description='Generador de Informes Urbanísticos')
    parser.add_argument('--ref', type=str, help='Referencia catastral')
    parser.add_argument('--provincia', type=str, help='Provincia')
    parser.add_argument('--municipio', type=str, help='Municipio')
    parser.add_argument('--via', type=str, help='Vía')
    parser.add_argument('--numero', type=str, help='Número')
    parser.add_argument('--output', type=str, default='informe.json', help='Archivo de salida')
    parser.add_argument('--config', type=str, help='Archivo de configuración')
    
    args = parser.parse_args()
    
    generador = InformeUrbanistico(args.config)
    informe = generador.generar_informe_completo(
        ref_catastral=args.ref,
        provincia=args.provincia,
        municipio=args.municipio,
        via=args.via,
        numero=args.numero
    )
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(informe, f, indent=2, ensure_ascii=False)
        
    print(f"Informe generado: {args.output}")
    print(f"Estado: {informe['estado']}")
    
    if informe['estado'] == 'completado':
        pdf_path = args.output.replace('.json', '.pdf')
        generador.generar_informe_pdf(informe, pdf_path)
        print(f"PDF generado: {pdf_path}")
        
        kml_path = args.output.replace('.json', '.kml')
        generador.generar_informe_kml(informe, kml_path)
        print(f"KML generado: {kml_path}")

if __name__ == '__main__':
    main()
