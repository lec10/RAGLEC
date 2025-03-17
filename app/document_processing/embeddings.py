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
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 5) -> List[Optional[List[float]]]:
        """Genera embeddings para una lista de textos en lotes.
        
        Args:
            texts: Lista de textos para generar embeddings.
            batch_size: Tamaño del lote para procesar.
            
        Returns:
            List[Optional[List[float]]]: Lista de vectores de embedding.
        """
        embeddings = []
        
        # Procesar en lotes para evitar límites de tasa
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Esperar un poco entre lotes para evitar límites de tasa
            if i > 0:
                time.sleep(1)
            
            # Generar embeddings para el lote
            for text in batch:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
        
        return embeddings 