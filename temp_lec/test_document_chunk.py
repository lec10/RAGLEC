#!/usr/bin/env python
"""
Script para probar la generación de embeddings con un fragmento real del documento.
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, Any, List, Optional

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la configuración y componentes necesarios
from app.config.settings import OPENAI_API_KEY, EMBEDDING_MODEL
from app.document_processing.document_loader import DocumentProcessor
from openai import OpenAI, OpenAIError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def test_document_chunk(file_path: str, chunk_index: int = None):
    """Prueba la generación de embeddings con un fragmento real del documento.
    
    Args:
        file_path: Ruta al archivo PDF.
        chunk_index: Índice del fragmento a probar. Si es None, prueba todos los fragmentos.
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"El archivo {file_path} no existe")
            return False
            
        # Cargar el documento y dividirlo en fragmentos
        logger.info(f"Procesando archivo: {file_path}")
        doc_processor = DocumentProcessor()
        
        # Preparar metadatos básicos
        file_metadata = {
            "file_id": os.path.basename(file_path),
            "name": os.path.basename(file_path),
            "mime_type": "application/pdf"
        }
        
        # Procesar el archivo para obtener fragmentos
        start_time = time.time()
        chunks = doc_processor.process_file(file_path, file_metadata)
        processing_time = time.time() - start_time
        
        if not chunks:
            logger.error(f"No se pudieron extraer fragmentos del archivo {file_path}")
            return False
            
        logger.info(f"Se extrajeron {len(chunks)} fragmentos en {processing_time:.2f} segundos")
        
        # Inicializar el cliente de OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Determinar qué fragmentos probar
        if chunk_index is not None:
            if chunk_index < 0 or chunk_index >= len(chunks):
                logger.error(f"Índice de fragmento {chunk_index} fuera de rango (0-{len(chunks)-1})")
                return False
            test_chunks = [chunks[chunk_index]]
            logger.info(f"Probando el fragmento {chunk_index} de {len(chunks)}")
        else:
            # Si no se especifica un índice, probar algunos fragmentos distribuidos
            sample_indices = [0, len(chunks)//4, len(chunks)//2, (3*len(chunks))//4, len(chunks)-1]
            test_chunks = [chunks[i] for i in sample_indices if i < len(chunks)]
            logger.info(f"Probando {len(test_chunks)} fragmentos de muestra del documento")
        
        # Probar la generación de embeddings para cada fragmento
        for i, chunk in enumerate(test_chunks):
            chunk_idx = chunk_index if chunk_index is not None else sample_indices[i]
            logger.info(f"Probando fragmento {chunk_idx}...")
            
            content = chunk.get('content', '')
            content_length = len(content)
            token_estimate = content_length // 4  # Estimación aproximada: 4 caracteres por token
            
            logger.info(f"Longitud del contenido: {content_length} caracteres (≈{token_estimate} tokens)")
            
            # Mostrar una vista previa del contenido
            preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"Vista previa: {preview}")
            
            # Intentar generar el embedding
            try:
                start_time = time.time()
                response = client.embeddings.create(
                    input=content,
                    model=EMBEDDING_MODEL
                )
                
                elapsed_time = time.time() - start_time
                
                if response and hasattr(response, "data") and len(response.data) > 0:
                    embedding = response.data[0].embedding
                    embedding_length = len(embedding)
                    logger.info(f"Fragmento {chunk_idx}: Embedding generado exitosamente con {embedding_length} dimensiones en {elapsed_time:.2f} segundos")
                else:
                    logger.error(f"Fragmento {chunk_idx}: Error al generar embedding, respuesta vacía o inválida")
            except OpenAIError as e:
                logger.error(f"Fragmento {chunk_idx}: Error de OpenAI: {e}")
            except Exception as e:
                logger.error(f"Fragmento {chunk_idx}: Error general: {e}")
                
            # Pausar entre solicitudes para evitar límites de tasa
            if i < len(test_chunks) - 1:  # No esperar después del último fragmento
                time.sleep(1)
        
        return True
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        return False

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Probar la generación de embeddings con fragmentos de un documento')
    parser.add_argument('file_path', help='Ruta al archivo PDF')
    parser.add_argument('--chunk', type=int, help='Índice específico del fragmento a probar')
    args = parser.parse_args()
    
    # Verificar clave API
    if not OPENAI_API_KEY:
        logger.error("No se ha configurado la clave API de OpenAI")
        sys.exit(1)
    
    # Ejecutar prueba
    logger.info(f"=== Iniciando prueba con archivo: {args.file_path} ===")
    success = test_document_chunk(args.file_path, args.chunk)
    
    # Resultado final
    if success:
        logger.info("Prueba completada (puede haber errores en fragmentos específicos)")
    else:
        logger.error("La prueba falló en su configuración general")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 