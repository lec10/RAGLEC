#!/usr/bin/env python
"""
Script para probar el logging en el archivo rag_app.log.
"""

import logging
import os
import sys

# Configurar logging exactamente como en Main.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rag_app.log", mode='w'),  # Modo 'w' para sobrescribir
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Función principal."""
    logger.info("=== PRUEBA DE LOGGING ===")
    logger.info(f"Directorio actual: {os.getcwd()}")
    logger.info(f"Ruta del archivo de log: {os.path.abspath('rag_app.log')}")
    logger.info(f"El archivo existe: {os.path.exists('rag_app.log')}")
    
    # Verificar permisos
    try:
        perm = oct(os.stat('rag_app.log').st_mode)[-3:]
        logger.info(f"Permisos del archivo: {perm}")
    except Exception as e:
        logger.error(f"Error al verificar permisos: {e}")
    
    # Intentar escribir directamente
    try:
        with open('rag_app.log', 'a') as f:
            f.write("Prueba de escritura directa\n")
        logger.info("Escritura directa exitosa")
    except Exception as e:
        logger.error(f"Error al escribir directamente: {e}")
    
    logger.info("Prueba de logging completada")

if __name__ == "__main__":
    main() 