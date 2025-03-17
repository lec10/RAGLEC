"""
Script para ejecutar todas las pruebas de la aplicación RAG.
"""

import unittest
import sys
import os

if __name__ == "__main__":
    # Añadir el directorio raíz al path para importar los módulos de la aplicación
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Descubrir y ejecutar todas las pruebas
    test_suite = unittest.defaultTestLoader.discover("tests")
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Salir con código de error si alguna prueba falló
    sys.exit(not result.wasSuccessful()) 