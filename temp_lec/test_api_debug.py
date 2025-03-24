#!/usr/bin/env python
"""
Script de diagnóstico para verificar problemas con la API de OpenAI.
Este script verifica si hay algún problema con la API de OpenAI para generar embeddings
e intenta identificar la causa exacta del error.
"""

import os
import sys
import time
import logging

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la configuración y componentes necesarios
from app.config.settings import OPENAI_API_KEY, EMBEDDING_MODEL
from app.document_processing.embeddings import EmbeddingGenerator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def main():
    """Función principal."""
    # Verificar clave API
    if not OPENAI_API_KEY:
        logger.error("No se ha configurado la clave API de OpenAI")
        sys.exit(1)
    
    # Mostrar información del entorno
    logger.info("=== Iniciando diagnóstico de la API de OpenAI ===")
    logger.info(f"Modelo de embeddings: {EMBEDDING_MODEL}")
    logger.info(f"Clave API: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-4:] if len(OPENAI_API_KEY) > 8 else '****'}")
    
    # Crear el generador de embeddings
    embedding_generator = EmbeddingGenerator()
    
    # Prueba 1: Embedding de texto simple
    logger.info("\n=== Prueba 1: Texto simple ===")
    simple_test = "Este es un texto de prueba simple para verificar la API de OpenAI."
    test1_success = embedding_generator.debug_embedding(simple_test)
    
    # Prueba 2: Texto más largo
    logger.info("\n=== Prueba 2: Texto más largo ===")
    longer_test = "Este es un texto más largo para probar si la longitud del texto afecta la generación de embeddings. " * 5
    test2_success = embedding_generator.debug_embedding(longer_test)
    
    # Prueba 3: Texto con caracteres especiales
    logger.info("\n=== Prueba 3: Texto con caracteres especiales ===")
    special_chars_test = "Texto con caracteres especiales: áéíóú ñ Ñ ¿? ¡! € $ % & / \\ @"
    test3_success = embedding_generator.debug_embedding(special_chars_test)
    
    # Prueba 4: Texto en quechua (similar al documento problemático)
    logger.info("\n=== Prueba 4: Texto en quechua ===")
    quechua_test = """
    QUECHUA-ESPAÑOL
    Rimay, amauta, yachachiy, hamawt'a, ñawpa, kallpa.
    Allillanchu taytay, allillanchu mamay.
    Pachamama, Inti Tayta, Quyllur, Willka.
    """
    test4_success = embedding_generator.debug_embedding(quechua_test)
    
    # Resultados finales
    logger.info("\n=== Resultados del diagnóstico ===")
    all_tests = [
        ("Texto simple", test1_success),
        ("Texto largo", test2_success),
        ("Caracteres especiales", test3_success),
        ("Texto en quechua", test4_success)
    ]
    
    for test_name, success in all_tests:
        logger.info(f"Prueba - {test_name}: {'EXITOSA' if success else 'FALLIDA'}")
    
    overall_success = all(success for _, success in all_tests)
    if overall_success:
        logger.info("\nDIAGNÓSTICO GENERAL: La API de OpenAI está funcionando correctamente")
    else:
        failed_tests = [test_name for test_name, success in all_tests if not success]
        logger.error(f"\nDIAGNÓSTICO GENERAL: Se encontraron problemas en las pruebas: {', '.join(failed_tests)}")
        
        # Sugerencias basadas en los fallos
        logger.info("\n=== Sugerencias para resolver el problema ===")
        
        if not test1_success:
            logger.error("Problema fundamental con la API de OpenAI:")
            logger.error("  - Verifica que tu clave API sea válida y esté activa")
            logger.error("  - Comprueba que tengas saldo suficiente en tu cuenta de OpenAI")
            logger.error("  - Asegúrate de que el modelo de embeddings esté disponible")
        
        if test1_success and not test2_success:
            logger.warning("Problema con textos largos:")
            logger.warning("  - Es posible que estés excediendo el límite de tokens por solicitud")
            logger.warning("  - Considera dividir los textos en fragmentos más pequeños")
        
        if test1_success and not test3_success:
            logger.warning("Problema con caracteres especiales:")
            logger.warning("  - Puede ser necesario limpiar o normalizar los textos antes de procesarlos")
        
        if test1_success and not test4_success:
            logger.warning("Problema con texto en quechua:")
            logger.warning("  - El modelo puede tener dificultades con idiomas específicos")
            logger.warning("  - Considera pre-procesar el texto o utilizar un modelo diferente")
    
        logger.info("\nRecomendación general: Verifica los logs detallados durante el procesamiento")
        logger.info("del documento para identificar el error exacto que está ocurriendo.")
    
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main() 