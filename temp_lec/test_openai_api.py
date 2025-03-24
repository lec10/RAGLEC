#!/usr/bin/env python
"""
Script para probar la conexión con la API de OpenAI.
Este script verifica si las credenciales de OpenAI funcionan correctamente
y si hay algún problema con los límites de tasa o bloqueos de cuenta.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la configuración y componentes necesarios
from app.config.settings import OPENAI_API_KEY, EMBEDDING_MODEL, LLM_MODEL
from openai import OpenAI, OpenAIError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def test_embeddings_api():
    """Prueba la API de embeddings de OpenAI."""
    try:
        logger.info(f"Probando API de embeddings usando modelo: {EMBEDDING_MODEL}")
        logger.info(f"Clave API de OpenAI: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-4:] if len(OPENAI_API_KEY) > 8 else '****'}")
        
        # Inicializar el cliente de OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Texto de prueba simple
        test_text = "Este es un texto de prueba para verificar si la API de OpenAI está funcionando correctamente."
        
        # Intentar generar un embedding
        logger.info("Enviando solicitud de embedding...")
        start_time = time.time()
        
        response = client.embeddings.create(
            input=test_text,
            model=EMBEDDING_MODEL
        )
        
        elapsed_time = time.time() - start_time
        
        # Verificar respuesta
        if response and hasattr(response, "data") and len(response.data) > 0:
            embedding = response.data[0].embedding
            embedding_length = len(embedding)
            logger.info(f"Embedding generado exitosamente: {embedding_length} dimensiones")
            logger.info(f"Tiempo de respuesta: {elapsed_time:.2f} segundos")
            return True
        else:
            logger.error("No se pudo generar el embedding, respuesta vacía o inválida")
            return False
            
    except OpenAIError as e:
        logger.error(f"Error de OpenAI: {e}")
        return False
    except Exception as e:
        logger.error(f"Error general: {e}")
        return False

def test_chat_api():
    """Prueba la API de chat de OpenAI."""
    try:
        logger.info(f"Probando API de chat usando modelo: {LLM_MODEL}")
        
        # Inicializar el cliente de OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Mensaje de prueba simple
        logger.info("Enviando solicitud de chat...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Eres un asistente útil."},
                {"role": "user", "content": "Hola, ¿estás funcionando?"}
            ],
            max_tokens=50
        )
        
        elapsed_time = time.time() - start_time
        
        # Verificar respuesta
        if response and hasattr(response, "choices") and len(response.choices) > 0:
            message = response.choices[0].message.content
            logger.info(f"Respuesta recibida: '{message}'")
            logger.info(f"Tiempo de respuesta: {elapsed_time:.2f} segundos")
            return True
        else:
            logger.error("No se pudo generar la respuesta, respuesta vacía o inválida")
            return False
            
    except OpenAIError as e:
        logger.error(f"Error de OpenAI: {e}")
        return False
    except Exception as e:
        logger.error(f"Error general: {e}")
        return False

def test_batch_embeddings():
    """Prueba la generación de embeddings en lote."""
    try:
        logger.info(f"Probando API de embeddings en lote usando modelo: {EMBEDDING_MODEL}")
        
        # Inicializar el cliente de OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Textos de prueba
        test_texts = [
            "Este es el primer texto de prueba.",
            "Este es el segundo texto de prueba.",
            "Este es el tercer texto de prueba."
        ]
        
        # Intentar generar embeddings en lote
        logger.info(f"Enviando solicitud de embeddings para {len(test_texts)} textos...")
        start_time = time.time()
        
        response = client.embeddings.create(
            input=test_texts,
            model=EMBEDDING_MODEL
        )
        
        elapsed_time = time.time() - start_time
        
        # Verificar respuesta
        if response and hasattr(response, "data") and len(response.data) == len(test_texts):
            logger.info(f"Embeddings generados exitosamente para {len(response.data)} textos")
            logger.info(f"Tiempo de respuesta: {elapsed_time:.2f} segundos")
            return True
        else:
            logger.error(f"Error: Se esperaban {len(test_texts)} embeddings, pero se recibieron {len(response.data) if hasattr(response, 'data') else 0}")
            return False
            
    except OpenAIError as e:
        logger.error(f"Error de OpenAI: {e}")
        return False
    except Exception as e:
        logger.error(f"Error general: {e}")
        return False

def main():
    """Función principal."""
    # Verificar clave API
    if not OPENAI_API_KEY:
        logger.error("No se ha configurado la clave API de OpenAI")
        sys.exit(1)
    
    # Ejecutar pruebas
    logger.info("=== Iniciando pruebas de API de OpenAI ===")
    
    # Prueba 1: API de embeddings
    embedding_success = test_embeddings_api()
    logger.info(f"Prueba de API de embeddings: {'EXITOSA' if embedding_success else 'FALLIDA'}")
    
    # Prueba 2: API de chat
    chat_success = test_chat_api()
    logger.info(f"Prueba de API de chat: {'EXITOSA' if chat_success else 'FALLIDA'}")
    
    # Prueba 3: API de embeddings en lote
    batch_success = test_batch_embeddings()
    logger.info(f"Prueba de API de embeddings en lote: {'EXITOSA' if batch_success else 'FALLIDA'}")
    
    # Resultado final
    logger.info("=== Resultados de las pruebas ===")
    overall_success = embedding_success and chat_success and batch_success
    if overall_success:
        logger.info("TODAS LAS PRUEBAS EXITOSAS - La API de OpenAI funciona correctamente")
    else:
        logger.error("ALGUNAS PRUEBAS FALLARON - Revisa los mensajes de error anteriores")
    
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main() 