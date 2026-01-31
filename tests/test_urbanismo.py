#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para el módulo de urbanismo
"""

import unittest
import os
import json
from urbanismo import InformeUrbanistico

class TestUrbanismo(unittest.TestCase):
    def setUp(self):
        self.config_path = 'proyecto_gis/config/urbanismo_config.json'
        self.generador = InformeUrbanistico(self.config_path)
        
    def test_config_loading(self):
        """Verifica que la configuración se carga correctamente"""
        self.assertIsNotNone(self.generador.config)
        self.assertIn('urls', self.generador.config)
        
    def test_generar_informe_rc(self):
        """Prueba la generación de informe por referencia catastral"""
        rc = "1234567VK1234N0001AB"
        informe = self.generador.generar_informe_completo(ref_catastral=rc)
        
        self.assertEqual(informe['estado'], 'completado')
        self.assertEqual(informe['datos_catastrales']['referencia'], rc)
        self.assertIn('urbanismo', informe)
        
    def test_generar_informe_direccion(self):
        """Prueba la generación de informe por dirección"""
        informe = self.generador.generar_informe_completo(
            via="Calle Mayor",
            numero="1",
            municipio="Madrid"
        )
        
        self.assertEqual(informe['estado'], 'completado')
        self.assertIn('Calle Mayor', informe['datos_catastrales']['localizacion'])

    def test_afecciones_detection(self):
        """Verifica que se detectan las afecciones territoriales"""
        informe = self.generador.generar_informe_completo(ref_catastral="TEST")
        afecciones = informe.get('afecciones', [])
        
        self.assertTrue(len(afecciones) > 0)
        # En nuestro mock, patrimonio es True
        patrimonio = next((a for a in afecciones if a['tipo'] == 'Patrimonio'), None)
        self.assertIsNotNone(patrimonio)
        self.assertTrue(patrimonio['afectado'])

if __name__ == '__main__':
    unittest.main()
