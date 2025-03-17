"""
Gestor de documentos.
Este módulo coordina el procesamiento de documentos, la generación de embeddings y la base de datos vectorial.
"""

import logging
import os
from typing import Dict, Any, List, Optional
import uuid
import hashlib
from datetime import datetime

from app.drive.google_drive_client import GoogleDriveClient
from app.drive.folder_monitor import GoogleDriveFolderMonitor
from app.document_processing.document_loader import DocumentProcessor
from app.document_processing.embeddings import EmbeddingGenerator
from app.database.vector_store import VectorDatabase

# Configurar logging
logger = logging.getLogger(__name__)

class DocumentManager:
    """Clase para gestionar documentos y coordinar los diferentes componentes."""
    
    def __init__(self):
        """Inicializa el gestor de documentos."""
        self.drive_client = GoogleDriveClient()
        self.document_processor = DocumentProcessor()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_db = VectorDatabase()
        self.folder_monitor = GoogleDriveFolderMonitor()
        
        # Registrar callbacks para eventos de archivos
        self.folder_monitor.register_callback("new_file", self.process_new_file)
        self.folder_monitor.register_callback("modified_file", self.process_modified_file)
        self.folder_monitor.register_callback("deleted_file", self.process_deleted_file)
        
        logger.info("Gestor de documentos inicializado")
    
    def start(self):
        """Inicia el monitoreo de la carpeta de Google Drive."""
        self.folder_monitor.start_monitoring()
        logger.info("Gestor de documentos iniciado")
    
    def stop(self):
        """Detiene el monitoreo de la carpeta de Google Drive."""
        self.folder_monitor.stop_monitoring()
        logger.info("Gestor de documentos detenido")
    
    def process_new_file(self, file_data: Dict[str, Any]):
        """Procesa un archivo nuevo.
        
        Args:
            file_data: Metadatos del archivo.
        """
        try:
            file_id = file_data.get('id')
            file_name = file_data.get('name', 'Desconocido')
            
            logger.info(f"Procesando archivo nuevo: {file_name} ({file_id})")
            
            # Verificar si el archivo ya ha sido procesado
            chunks = self.vector_db.get_chunks_by_file_id(file_id)
            if chunks:
                logger.info(f"El archivo {file_name} ya ha sido procesado previamente, actualizando")
                return self.process_modified_file(file_data)
            
            # Descargar el archivo
            local_path = self.drive_client.download_file(file_id)
            if not local_path:
                logger.error(f"No se pudo descargar el archivo {file_id}")
                return
            
            # Preparar metadatos
            file_metadata = {
                "file_id": file_id,
                "name": file_name,
                "source": "google_drive",
                "modified_time": file_data.get('modifiedTime', ''),
                "mime_type": file_data.get('mimeType', ''),
                "checksum": file_data.get('md5Checksum', '')
            }
            
            # Procesar el archivo
            self._process_file(local_path, file_metadata)
            
            # Eliminar el archivo local después de procesarlo
            os.remove(local_path)
            logger.info(f"Archivo {file_name} procesado correctamente")
        except Exception as e:
            logger.error(f"Error al procesar el archivo nuevo {file_data.get('id', '')}: {e}")
    
    def process_modified_file(self, file_data: Dict[str, Any]):
        """Procesa un archivo modificado.
        
        Args:
            file_data: Metadatos del archivo.
        """
        try:
            file_id = file_data.get('id')
            file_name = file_data.get('name', 'Desconocido')
            checksum = file_data.get('md5Checksum', '')
            
            logger.info(f"Procesando archivo modificado: {file_name} ({file_id})")
            
            # Verificar si el archivo ha cambiado realmente
            chunks = self.vector_db.get_chunks_by_file_id(file_id)
            if chunks and chunks[0].get('metadata', {}).get('checksum') == checksum:
                logger.info(f"El archivo {file_name} no ha cambiado (mismo checksum), omitiendo procesamiento")
                return
            
            # Eliminar los fragmentos existentes
            deleted_count = self.vector_db.delete_chunks_by_file_id(file_id)
            logger.info(f"Se eliminaron {deleted_count} fragmentos existentes del archivo {file_id}")
            
            # Procesar el archivo como si fuera nuevo
            self.process_new_file(file_data)
            
            logger.info(f"Archivo modificado {file_name} procesado correctamente")
        except Exception as e:
            logger.error(f"Error al procesar el archivo modificado {file_data.get('id', '')}: {e}")
    
    def process_deleted_file(self, file_data: Dict[str, Any]):
        """Procesa un archivo eliminado.
        
        Args:
            file_data: Metadatos del archivo.
        """
        try:
            file_id = file_data.get('id')
            file_name = file_data.get('name', 'Desconocido')
            
            logger.info(f"Procesando archivo eliminado: {file_name} ({file_id})")
            
            # Eliminar los fragmentos del archivo
            deleted_count = self.vector_db.delete_chunks_by_file_id(file_id)
            logger.info(f"Se eliminaron {deleted_count} fragmentos del archivo {file_id}")
        except Exception as e:
            logger.error(f"Error al procesar el archivo eliminado {file_data.get('id', '')}: {e}")
    
    def _process_file(self, file_path: str, file_metadata: Dict[str, Any]):
        """Procesa un archivo y lo añade a la base de datos vectorial.
        
        Args:
            file_path: Ruta al archivo local.
            file_metadata: Metadatos del archivo.
        """
        # Procesar el archivo para obtener fragmentos
        chunks = self.document_processor.process_file(file_path, file_metadata)
        
        if not chunks:
            logger.warning(f"No se pudieron extraer fragmentos del archivo {file_metadata.get('name')}")
            return
        
        logger.info(f"Se extrajeron {len(chunks)} fragmentos del archivo {file_metadata.get('name')}")
        
        # Generar embeddings para cada fragmento y añadirlos a la base de datos
        batch_texts = [chunk.get('content', '') for chunk in chunks]
        embeddings = self.embedding_generator.generate_embeddings_batch(batch_texts)
        
        success_count = 0
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding:
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                chunk_id = chunk.get('id', self._generate_chunk_id(file_metadata.get("file_id", ""), i))
                
                # Imprimir los metadatos para depuración
                logger.debug(f"Metadatos creados para el documento {i+1}/{len(chunks)}: {metadata}")
                
                # Añadir a la base de datos
                if self.vector_db.add_document(chunk_id, content, metadata, embedding):
                    success_count += 1
            else:
                logger.error(f"No se pudo generar embedding para el fragmento {i} del archivo {file_metadata.get('name')}")
        
        logger.info(f"Se añadieron {success_count} de {len(chunks)} fragmentos a la base de datos")
    
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
    
    def process_all_files(self):
        """Procesa todos los archivos en la carpeta monitoreada."""
        try:
            # Obtener la lista de archivos
            files = self.drive_client.list_files()
            
            logger.info(f"Procesando {len(files)} archivos...")
            
            # Procesar cada archivo
            for file_data in files:
                self.process_new_file(file_data)
            
            logger.info("Todos los archivos procesados correctamente")
        except Exception as e:
            logger.error(f"Error al procesar todos los archivos: {e}")
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas sobre los documentos procesados.
        
        Returns:
            Dict[str, Any]: Estadísticas de los documentos.
        """
        try:
            # Para una implementación real, necesitaríamos consultas SQL más complejas
            # Aquí asumimos que podemos hacerlo a través de la API de Supabase
            
            # Por ahora, devolver información básica
            stats = {
                "total_files": 0,
                "total_chunks": 0,
                "last_processed": datetime.now().isoformat()
            }
            
            logger.info("Estadísticas de documentos obtenidas")
            return stats
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de documentos: {e}")
            return {
                "error": str(e),
                "total_files": 0,
                "total_chunks": 0
            } 