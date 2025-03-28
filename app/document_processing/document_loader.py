"""
Carga y procesamiento de documentos.
Este módulo proporciona funciones para cargar y procesar documentos de diferentes formatos.
"""

import logging
import os
from typing import List, Dict, Any, Optional
import hashlib
from pathlib import Path
import re

from langchain_community.document_loaders import (
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Importar PyMuPDF para manejo de PDFs
import fitz  # PyMuPDF

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
            
            # Usar PyMuPDF para PDFs
            if file_extension == ".pdf":
                documents = self._load_pdf_with_pymupdf(file_path)
            elif file_extension in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
                documents = loader.load()
            elif file_extension == ".txt":
                loader = TextLoader(file_path)
                documents = loader.load()
            else:
                # Para otros formatos, intentar con el cargador genérico
                loader = UnstructuredFileLoader(file_path)
                documents = loader.load()
            
            logger.info(f"Documento {file_path} cargado correctamente con {len(documents)} páginas/secciones")
            return documents
        except Exception as e:
            logger.error(f"Error al cargar el documento {file_path}: {e}")
            return None
    
    def _load_pdf_with_pymupdf(self, file_path: str) -> List[Document]:
        """Carga un PDF usando PyMuPDF (fitz) con mejor extracción de texto.
        
        Args:
            file_path: Ruta al archivo PDF.
            
        Returns:
            List[Document]: Lista de documentos, uno por página del PDF.
        """
        documents = []
        
        try:
            # Abrir el PDF
            pdf_document = fitz.open(file_path)
            
            for page_num, page in enumerate(pdf_document):
                # Extraer texto limpio de la página
                text = page.get_text("text")
                
                # Limpiar el texto: normalizar saltos de línea, espacios, etc.
                text = self._clean_pdf_text(text)
                
                # Crear un objeto Document para cada página
                metadata = {"page": page_num + 1, "source": file_path}
                doc = Document(page_content=text, metadata=metadata)
                documents.append(doc)
            
            pdf_document.close()
            
            logger.info(f"PDF cargado con éxito: {len(documents)} páginas")
            return documents
        
        except Exception as e:
            logger.error(f"Error al cargar el PDF con PyMuPDF: {e}")
            return []
    
    def _clean_pdf_text(self, text: str) -> str:
        """Limpia el texto extraído de un PDF para mejorar su calidad.
        
        Args:
            text: Texto extraído del PDF.
            
        Returns:
            str: Texto limpio y normalizado.
        """
        # Reemplazar saltos de línea múltiples por uno solo
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Eliminar guiones de palabras divididas al final de línea
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        
        # Eliminar espacios en blanco al inicio y fin de cada línea
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Eliminar saltos de línea innecesarios en párrafos (preservando párrafos reales)
        # Un párrafo real suele terminar con un punto seguido de un salto de línea
        text = re.sub(r'(?<!\.\s)\n(?![A-Z])', ' ', text)
        
        # Eliminar espacios múltiples
        text = re.sub(r' {2,}', ' ', text)
        
        return text
    
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
        # Determinar el tamaño de los fragmentos en función del tamaño del archivo
        file_size = os.path.getsize(file_path)
        original_chunk_size = self.chunk_size
        original_chunk_overlap = self.chunk_overlap
        
        # Para archivos grandes, usar fragmentos más grandes para reducir el número total
        if file_size > 10_000_000:  # 10 MB
            # Archivos muy grandes
            chunk_size = 8000
            chunk_overlap = 200
            logger.info(f"Archivo grande detectado ({file_size/1_000_000:.1f} MB). Usando chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
            
            # Actualizar el text_splitter con los nuevos valores
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len
            )
        elif file_size > 5_000_000:  # 5 MB
            # Archivos medianos
            chunk_size = 5000
            chunk_overlap = 150
            logger.info(f"Archivo mediano detectado ({file_size/1_000_000:.1f} MB). Usando chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
            
            # Actualizar el text_splitter con los nuevos valores
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len
            )
        
        try:
            # Cargar el documento
            documents = self.load_document(file_path)
            if not documents:
                return []
            
            # Extraer metadatos adicionales si es posible
            file_extension = Path(file_path).suffix.lower()
            file_name = file_metadata.get('name', os.path.basename(file_path))
            
            # Dividir el documento en fragmentos
            chunks = self.split_documents(documents)
            
            # Restaurar la configuración original después de procesar
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=original_chunk_size,
                chunk_overlap=original_chunk_overlap,
                length_function=len
            )
            
            # Preparar los fragmentos con metadatos
            processed_chunks = []
            total_chunks = len(chunks)
            
            logger.info(f"Procesando {total_chunks} fragmentos para el archivo {file_metadata.get('name', file_path)}")
            
            for i, chunk in enumerate(chunks):
                # Registrar progreso cada 50 fragmentos
                if i % 50 == 0 or i == total_chunks - 1:
                    logger.info(f"Progreso: {i+1}/{total_chunks} fragmentos procesados ({(i+1)/total_chunks*100:.1f}%)")
                
                # Generar un ID único para el fragmento
                chunk_id = self._generate_chunk_id(file_metadata.get("file_id", ""), i)
                
                # Extraer metadatos específicos del fragmento según el tipo de documento
                specific_metadata = {}
                
                # Para PDFs, obtener número de página si está disponible
                if file_extension == ".pdf" and hasattr(chunk, 'metadata') and 'page' in chunk.metadata:
                    specific_metadata['page'] = chunk.metadata['page']
                    specific_metadata['section'] = f"Página {chunk.metadata['page']}"
                
                # Añadir información de sección o posición relativa para todos los documentos
                chunk_position = f"Fragmento {i+1} de {total_chunks}"
                if 'page' in specific_metadata:
                    chunk_position = f"Página {specific_metadata['page']}, {chunk_position}"
                
                specific_metadata['position'] = chunk_position
                
                # Generar un título contextual para el fragmento
                content_preview = chunk.page_content[:100].replace('\n', ' ').strip()
                specific_metadata['title'] = f"{content_preview}..." if len(content_preview) >= 100 else content_preview
                
                # Simplificar los metadatos para reducir almacenamiento
                # Mantener solo: file_id, chunk_index, total_chunks, name, mime_type, page
                simplified_metadata = {
                    "file_id": file_metadata.get("file_id", ""),
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "name": file_name,
                    "mime_type": file_metadata.get("mime_type", f"application/{file_extension.replace('.', '')}")
                }
                
                # Añadir número de página si está disponible (solo para PDFs)
                if file_extension == ".pdf" and hasattr(chunk, 'metadata') and 'page' in chunk.metadata:
                    simplified_metadata["page"] = chunk.metadata['page']
                
                # IMPORTANTE: Nunca incluir modified_time en los metadatos de fragmentos
                
                # Crear contenido enriquecido para mejorar el embedding
                # Este contenido no se almacena, solo se usa para generar el embedding
                enriched_content = f"""ARCHIVO: {file_name}
TIPO: {file_extension.replace(".", "").upper()}
POSICIÓN: {chunk_position}
CONTENIDO:
{chunk.page_content}
"""
                
                # Añadir el fragmento procesado
                processed_chunks.append({
                    "id": chunk_id,
                    "content": chunk.page_content,
                    "enriched_content": enriched_content,  # Para usar en la generación de embeddings
                    "metadata": simplified_metadata
                })
            
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error al procesar el archivo {file_path}: {e}")
            # Restaurar la configuración original en caso de error
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=original_chunk_size,
                chunk_overlap=original_chunk_overlap,
                length_function=len
            )
            return []
    
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

    def _process_text_chunks(self, text_chunks: List[str], file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesa fragmentos de texto y añade metadatos.
        
        Args:
            text_chunks: Lista de fragmentos de texto.
            file_metadata: Metadatos del archivo.
            
        Returns:
            List[Dict[str, Any]]: Lista de fragmentos procesados con metadatos.
        """
        total_chunks = len(text_chunks)
        documents = []
        
        # Obtener los datos necesarios de file_metadata
        file_id = file_metadata.get("file_id", "")
        file_name = file_metadata.get("name", "")
        mime_type = file_metadata.get("mime_type", "")
        
        for i, text in enumerate(text_chunks):
            # Simplificar los metadatos para reducir almacenamiento
            # Mantener solo: file_id, chunk_index, total_chunks, name, mime_type, page
            metadata = {
                "file_id": file_id,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "name": file_name,
                "mime_type": mime_type,
            }
            
            # Añadir número de página si está disponible
            if "page" in file_metadata:
                metadata["page"] = file_metadata.get("page")
            
            chunk_id = self._generate_chunk_id(file_metadata.get("file_id", ""), i)
            
            documents.append({
                "id": chunk_id,
                "content": text,
                "metadata": metadata
            })

        return documents 