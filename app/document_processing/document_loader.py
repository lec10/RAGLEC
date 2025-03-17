"""
Carga y procesamiento de documentos.
Este módulo proporciona funciones para cargar y procesar documentos de diferentes formatos.
"""

import logging
import os
from typing import List, Dict, Any, Optional
import hashlib
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.config.settings import CHUNK_SIZE, CHUNK_OVERLAP

# Configurar logging
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Clase para cargar y procesar documentos de diferentes formatos."""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """Inicializa el procesador de documentos.
        
        Args:
            chunk_size: Tamaño de los fragmentos de texto.
            chunk_overlap: Superposición entre fragmentos.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        logger.info(f"Procesador de documentos inicializado con chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def load_document(self, file_path: str) -> Optional[List[Document]]:
        """Carga un documento desde un archivo.
        
        Args:
            file_path: Ruta al archivo.
            
        Returns:
            List[Document] o None: Lista de documentos si se cargó correctamente, None en caso contrario.
        """
        try:
            file_extension = Path(file_path).suffix.lower()
            
            # Seleccionar el cargador adecuado según la extensión del archivo
            if file_extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_extension in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            elif file_extension == ".txt":
                loader = TextLoader(file_path)
            else:
                # Para otros formatos, intentar con el cargador genérico
                loader = UnstructuredFileLoader(file_path)
            
            # Cargar el documento
            documents = loader.load()
            logger.info(f"Documento {file_path} cargado correctamente")
            return documents
        except Exception as e:
            logger.error(f"Error al cargar el documento {file_path}: {e}")
            return None
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Divide los documentos en fragmentos más pequeños.
        
        Args:
            documents: Lista de documentos a dividir.
            
        Returns:
            List[Document]: Lista de fragmentos de documentos.
        """
        try:
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Documento dividido en {len(chunks)} fragmentos")
            return chunks
        except Exception as e:
            logger.error(f"Error al dividir el documento: {e}")
            return []
    
    def process_file(self, file_path: str, file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesa un archivo completo y devuelve los fragmentos con metadatos.
        
        Args:
            file_path: Ruta al archivo.
            file_metadata: Metadatos del archivo.
            
        Returns:
            List[Dict[str, Any]]: Lista de fragmentos con sus metadatos.
        """
        # Cargar el documento
        documents = self.load_document(file_path)
        if not documents:
            return []
        
        # Dividir el documento en fragmentos
        chunks = self.split_documents(documents)
        
        # Preparar los fragmentos con metadatos
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Generar un ID único para el fragmento
            chunk_id = self._generate_chunk_id(file_metadata.get("file_id", ""), i)
            
            # Combinar los metadatos del archivo con los del fragmento
            combined_metadata = {
                **file_metadata,
                "chunk_index": i,
                "chunk_id": chunk_id,
                "total_chunks": len(chunks)
            }
            
            # Añadir el fragmento procesado
            processed_chunks.append({
                "id": chunk_id,
                "content": chunk.page_content,
                "metadata": combined_metadata
            })
        
        return processed_chunks
    
    def _generate_chunk_id(self, file_id: str, chunk_index: int) -> str:
        """Genera un ID único para un fragmento de documento.
        
        Args:
            file_id: ID del archivo.
            chunk_index: Índice del fragmento.
            
        Returns:
            str: ID único del fragmento.
        """
        # Combinar el ID del archivo y el índice del fragmento
        combined = f"{file_id}_{chunk_index}"
        
        # Generar un hash para asegurar la unicidad
        return hashlib.md5(combined.encode()).hexdigest() 