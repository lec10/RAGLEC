#!/usr/bin/env python
"""
Script para probar el registro en el log.
"""

import logging
import os

# Crear una ruta absoluta al archivo de log
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rag_app.log')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='w'),  # Modo 'w' para sobrescribir el archivo
        logging.StreamHandler()  # También mostrar en consola
    ]
)

logger = logging.getLogger("test_log")

def main():
    """Función principal."""
    logger.info("Prueba de registro en el log")
    logger.info(f"Archivo de log: {log_file}")
    logger.info(f"El archivo existe: {os.path.exists(log_file)}")
    logger.info(f"Permisos del archivo: {oct(os.stat(log_file).st_mode)[-3:]}")
    logger.info(f"Tamaño del archivo: {os.path.getsize(log_file)}")
    
    # Intentar escribir directamente en el archivo
    try:
        with open(log_file, 'a') as f:
            f.write("Prueba de escritura directa\n")
        logger.info("Escritura directa exitosa")
    except Exception as e:
        logger.error(f"Error al escribir directamente: {e}")
    
    logger.info("Fin de la prueba")

if __name__ == "__main__":
    main() 