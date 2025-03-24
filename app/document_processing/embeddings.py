"""
Generación de embeddings con OpenAI.
Este módulo proporciona funciones para generar embeddings de texto utilizando OpenAI.
"""

import logging
from typing import List, Optional
import time

from langchain_openai import OpenAIEmbeddings
from openai import RateLimitError

from app.config.settings import OPENAI_API_KEY, EMBEDDING_MODEL

# Configurar logging
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Clase para generar embeddings de texto utilizando OpenAI."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL, api_key: str = OPENAI_API_KEY):
        """Inicializa el generador de embeddings.
        
        Args:
            model_name: Nombre del modelo de embeddings de OpenAI.
            api_key: Clave API de OpenAI.
        """
        self.model_name = model_name
        self.embeddings = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=api_key
        )
        logger.info(f"Generador de embeddings inicializado con el modelo {model_name}")
    
    def generate_embedding(self, text: str, max_retries: int = 3) -> Optional[List[float]]:
        """Genera un embedding para un texto.
        
        Args:
            text: Texto para generar el embedding.
            max_retries: Número máximo de reintentos en caso de error.
            
        Returns:
            List[float] o None: Vector de embedding si se generó correctamente, None en caso contrario.
        """
        retries = 0
        while retries < max_retries:
            try:
                embedding = self.embeddings.embed_query(text)
                return embedding
            except RateLimitError:
                wait_time = (2 ** retries) * 1  # Espera exponencial
                logger.warning(f"Límite de tasa alcanzado. Esperando {wait_time} segundos...")
                time.sleep(wait_time)
                retries += 1
            except Exception as e:
                logger.error(f"Error al generar embedding: {e}")
                return None
        
        logger.error(f"No se pudo generar el embedding después de {max_retries} intentos")
        return None
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[Optional[List[float]]]:
        """Genera embeddings para una lista de textos usando la API en modo batch real.
        
        Args:
            texts: Lista de textos para generar embeddings.
            batch_size: Tamaño del lote para procesar de una vez.
            
        Returns:
            List[Optional[List[float]]]: Lista de vectores de embedding.
        """
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        # Configurar el logger de httpx para incluir información adicional
        httpx_logger = logging.getLogger('httpx')
        original_level = httpx_logger.level
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_end = min(i+batch_size, len(texts))
            logger.info(f"Procesando lote {(i//batch_size)+1}/{total_batches} (fragmentos {i+1}-{batch_end} de {len(texts)})")
            
            # Logging antes de la llamada a la API
            logger.info(f"Enviando solicitud de embeddings para fragmentos {i+1}-{batch_end} de {len(texts)}")
            
            retries = 0
            max_retries = 5
            while retries < max_retries:
                try:
                    # Usar el método embed_documents de LangChain para procesar múltiples textos
                    # Este método está diseñado para manejar lotes de documentos
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    
                    # Logging después de la llamada a la API
                    logger.info(f"Respuesta recibida para fragmentos {i+1}-{batch_end} de {len(texts)} - HTTP 200 OK")
                    
                    all_embeddings.extend(batch_embeddings)
                    
                    # Breve pausa para evitar límites de tasa
                    if i + batch_size < len(texts):
                        time.sleep(0.2)
                    
                    break  # Salir del bucle de reintentos si tuvo éxito
                        
                except RateLimitError:
                    retries += 1
                    wait_time = (2 ** retries) * 2  # Espera exponencial: 2, 4, 8, 16, 32 segundos
                    logger.warning(f"Límite de tasa alcanzado en lote {(i//batch_size)+1} (fragmentos {i+1}-{batch_end}). Esperando {wait_time} segundos... (intento {retries}/{max_retries})")
                    time.sleep(wait_time)
                    
                except Exception as e:
                    logger.error(f"Error al generar embeddings para lote {(i//batch_size)+1} (fragmentos {i+1}-{batch_end}): {e}")
                    # En caso de error, añadir embeddings nulos para todo el lote
                    all_embeddings.extend([None] * len(batch))
                    break
            
            # Si se agotaron los reintentos, añadir embeddings nulos
            if retries >= max_retries:
                logger.error(f"No se pudo procesar el lote {(i//batch_size)+1} (fragmentos {i+1}-{batch_end}) después de {max_retries} intentos")
                all_embeddings.extend([None] * len(batch))
        
        # Verificar que tenemos la cantidad correcta de embeddings
        if len(all_embeddings) != len(texts):
            logger.warning(f"Discrepancia: se generaron {len(all_embeddings)} embeddings para {len(texts)} textos")
            # Rellenar con None si faltan algunos
            all_embeddings.extend([None] * (len(texts) - len(all_embeddings)))
        
        return all_embeddings
    
    def debug_embedding(self, text_sample: str = None) -> bool:
        """Función de diagnóstico para verificar si la API de OpenAI está funcionando correctamente.
        
        Args:
            text_sample: Texto de muestra para generar el embedding. Si es None, se usa un texto predeterminado.
            
        Returns:
            bool: True si la API funciona correctamente, False en caso contrario.
        """
        if text_sample is None:
            text_sample = "Este es un texto de prueba para verificar si la API de OpenAI está funcionando correctamente."
        
        try:
            logger.info(f"Ejecutando prueba de diagnóstico con la API de OpenAI utilizando modelo: {self.model_name}")
            
            # Intentar generar un embedding usando el método embed_query de LangChain
            start_time = time.time()
            
            embedding = self.embeddings.embed_query(text_sample)
            
            elapsed_time = time.time() - start_time
            
            # Verificar respuesta
            if embedding and len(embedding) > 0:
                embedding_length = len(embedding)
                logger.info(f"DIAGNÓSTICO EXITOSO: Embedding generado correctamente con {embedding_length} dimensiones")
                logger.info(f"Tiempo de respuesta: {elapsed_time:.2f} segundos")
                
                # Mostrar fragmento del embedding para verificación
                embedding_preview = str(embedding[:5]) + "..." + str(embedding[-5:])
                logger.info(f"Fragmento del embedding: {embedding_preview}")
                
                return True
            else:
                logger.error("DIAGNÓSTICO FALLIDO: No se pudo generar el embedding, respuesta vacía o inválida")
                return False
                
        except RateLimitError as e:
            logger.error(f"DIAGNÓSTICO FALLIDO: Error de límite de tasa de OpenAI: {e}")
            logger.warning("Es posible que hayas alcanzado tu límite de solicitudes a la API. Espera unos minutos.")
            return False
        except Exception as e:
            logger.error(f"DIAGNÓSTICO FALLIDO: Error general al conectar con la API de OpenAI: {e}")
            return False 