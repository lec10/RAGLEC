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
import json
import time

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
            drive_modified_time = file_data.get('modifiedTime', '')
            
            logger.info(f"Procesando archivo nuevo: {file_name} ({file_id})")
            logger.info(f"Fecha de modificación de Google Drive: {drive_modified_time}")
            
            # Verificar si el archivo ya ha sido procesado
            chunks = self.vector_db.get_chunks_by_file_id(file_id)
            if chunks:
                logger.info(f"El archivo {file_name} ya ha sido procesado previamente, actualizando")
                return self.process_modified_file(file_data)
            
            # Guardar explícitamente la fecha de modificación de Google Drive en la tabla files
            if file_id:
                try:
                    logger.info(f"Creando registro en tabla files con fecha de Google Drive: {drive_modified_time}")
                    
                    # Verificar si ya existe un registro
                    response = self.vector_db.supabase.table("files").select("*").eq("id", file_id).execute()
                    
                    # Datos para crear o actualizar
                    file_record = {
                        "id": file_id,
                        "name": file_name,
                        "mime_type": file_data.get('mimeType', ''),
                        "source": "google_drive",
                        "processed_at": datetime.now().isoformat(),
                        "status": "processing"
                    }
                    
                    # Siempre usar la fecha de Google Drive, nunca la fecha del sistema
                    if drive_modified_time:
                        file_record["last_modified"] = drive_modified_time
                    
                    if not response.data or len(response.data) == 0:
                        # Crear un nuevo registro
                        self.vector_db.supabase.table("files").insert(file_record).execute()
                        logger.info(f"Registro creado en tabla files")
                    else:
                        # Actualizar registro existente
                        self.vector_db.supabase.table("files").update(file_record).eq("id", file_id).execute()
                        logger.info(f"Registro actualizado en tabla files")
                
                except Exception as e:
                    logger.error(f"Error al guardar en tabla files: {e}")
            
            # Descargar el archivo
            local_path = self.drive_client.download_file(file_id)
            if not local_path:
                logger.error(f"No se pudo descargar el archivo {file_id}")
                return
            
            # Preparar metadatos (sin incluir modified_time)
            file_metadata = {
                "file_id": file_id,
                "name": file_name,
                "source": "google_drive",
                "mime_type": file_data.get('mimeType', ''),
                "checksum": file_data.get('md5Checksum', '')
            }
            
            # Procesar el archivo
            self._process_file(local_path, file_metadata)
            
            # Actualizar el estado a "processed" sin cambiar la fecha de modificación
            try:
                self.vector_db.supabase.table("files").update({
                    "status": "processed",
                    "processed_at": datetime.now().isoformat()
                }).eq("id", file_id).execute()
                
                logger.info(f"Estado actualizado a 'processed' en tabla files")
            except Exception as e:
                logger.error(f"Error al actualizar estado: {e}")
            
            # Eliminar el archivo local después de procesarlo
            os.remove(local_path)
            logger.info(f"Archivo {file_name} procesado correctamente")
        except Exception as e:
            logger.error(f"Error al procesar el archivo nuevo {file_data.get('id', '')}: {e}")
    
    def process_modified_file(self, file_data: Dict[str, Any]):
        """Procesa un archivo modificado.
        
        Args:
            file_data: Metadatos del archivo modificado.
        """
        try:
            file_id = file_data.get('id')
            file_name = file_data.get('name', 'Desconocido')
            drive_modified_time = file_data.get('modifiedTime', '')
            
            logger.info(f"Procesando archivo modificado: {file_name} ({file_id})")
            logger.info(f"Fecha de modificación de Google Drive: {drive_modified_time}")
            
            # Verificar si el archivo ha cambiado realmente comparando fechas
            response = self.vector_db.supabase.table("files").select("last_modified").eq("id", file_id).execute()
            
            if response.data and len(response.data) > 0:
                db_modified_time = response.data[0].get('last_modified', '')
                logger.info(f"Fecha almacenada en BD: {db_modified_time}")
                
                # Normalizar formatos de fecha para comparación correcta
                drive_time_normalized = self._normalize_date_string(drive_modified_time)
                db_time_normalized = self._normalize_date_string(db_modified_time)
                
                logger.info(f"[FECHA] Comparando: Drive={drive_time_normalized} | BD={db_time_normalized}")
                
                # Comparación de fechas normalizadas
                if drive_time_normalized == db_time_normalized:
                    logger.info(f"El archivo {file_name} no ha cambiado (misma fecha después de normalizar), omitiendo procesamiento")
                    return
            
            # Actualizar la fecha de Google Drive en la tabla files
            try:
                logger.info(f"Actualizando fecha de modificación: {drive_modified_time}")
                
                update_data = {
                    "status": "processing",
                    "processed_at": datetime.now().isoformat()
                }
                
                # Solo incluir last_modified si tenemos un valor de Google Drive
                if drive_modified_time:
                    update_data["last_modified"] = drive_modified_time
                
                self.vector_db.supabase.table("files").update(update_data).eq("id", file_id).execute()
                logger.info(f"Fecha actualizada en tabla files")
            except Exception as e:
                logger.error(f"Error al actualizar fecha: {e}")
            
            # Eliminar los fragmentos existentes
            deleted_count = self.vector_db.delete_chunks_by_file_id(file_id)
            logger.info(f"Se eliminaron {deleted_count} fragmentos existentes de la tabla 'documents' para el archivo {file_id}")
            
            # Descargar y procesar el archivo
            local_path = self.drive_client.download_file(file_id)
            if not local_path:
                logger.error(f"No se pudo descargar el archivo {file_id}")
                return
            
            # Preparar metadatos para el procesamiento (sin incluir modified_time)
            file_metadata = {
                "file_id": file_id,
                "name": file_name,
                "source": "google_drive",
                "mime_type": file_data.get('mimeType', ''),
                "checksum": file_data.get('md5Checksum', '')
            }
            
            # Procesar el archivo
            self._process_file(local_path, file_metadata)
            
            # Actualizar el estado sin modificar la fecha
            try:
                self.vector_db.supabase.table("files").update({
                    "status": "processed",
                    "processed_at": datetime.now().isoformat()
                }).eq("id", file_id).execute()
                
                logger.info(f"Estado actualizado a 'processed' en tabla files")
            except Exception as e:
                logger.error(f"Error al actualizar estado: {e}")
            
            # Eliminar el archivo local
            os.remove(local_path)
            logger.info(f"Archivo modificado {file_name} procesado correctamente")
        except Exception as e:
            logger.error(f"Error al procesar el archivo modificado {file_data.get('id', '')}: {e}")
    
    def process_deleted_file(self, file_data: Dict[str, Any]):
        """Procesa un archivo eliminado.
        
        Args:
            file_data: Metadatos del archivo.
            
        Esta función:
        1. Verifica que el archivo existe en la tabla 'files'
        2. Elimina todos los fragmentos asociados al archivo de la tabla 'documents' usando la columna file_id
        3. Elimina el registro del archivo de la tabla 'files'
        """
        try:
            file_id = file_data.get('id')
            file_name = file_data.get('name', 'Desconocido')
            
            logger.info(f"Procesando archivo eliminado: {file_name} ({file_id})")
            
            # Verificar que el archivo existe en la base de datos
            response = self.vector_db.supabase.table("files").select("*").eq("id", file_id).execute()
            if not response.data or len(response.data) == 0:
                logger.warning(f"El archivo {file_name} ({file_id}) no existe en la tabla 'files'")
                return
                
            # Eliminar los fragmentos del archivo
            deleted_count = self.vector_db.delete_chunks_by_file_id(file_id)
            logger.info(f"Se eliminaron {deleted_count} fragmentos de la tabla 'documents' para el archivo {file_id}")
            
            # Eliminar el registro del archivo en la tabla 'files'
            response = self.vector_db.supabase.table("files").delete().eq("id", file_id).execute()
            deleted_files = len(response.data) if response.data else 0
            logger.info(f"Se eliminó el registro del archivo {file_name} ({file_id}) de la tabla 'files': {deleted_files} registros afectados")
        except Exception as e:
            logger.error(f"Error al procesar el archivo eliminado {file_data.get('id', '')}: {e}")
    
    def _process_file(self, file_path: str, file_metadata: Dict[str, Any]):
        """Procesa un archivo y lo añade a la base de datos vectorial.
        
        Args:
            file_path: Ruta al archivo local.
            file_metadata: Metadatos del archivo.
        """
        start_time = time.time()
        
        # Procesar el archivo para obtener fragmentos
        chunks = self.document_processor.process_file(file_path, file_metadata)
        
        if not chunks:
            logger.warning(f"No se pudieron extraer fragmentos del archivo {file_metadata.get('name')}")
            return
        
        chunks_count = len(chunks)
        logger.info(f"Se extrajeron {chunks_count} fragmentos del archivo {file_metadata.get('name')}")
        
        # Calcular estadísticas y estimaciones
        chunks_processing_time = time.time() - start_time
        logger.info(f"Extracción de fragmentos completada en {chunks_processing_time:.2f} segundos")
        
        # Mostrar advertencia si hay muchos fragmentos
        if chunks_count > 500:
            logger.warning(f"Documento grande detectado con {chunks_count} fragmentos. Puede tardar considerablemente.")
            est_total_time = (chunks_count / 20) * 3  # ~3 segundos por lote de 20 fragmentos
            logger.info(f"Tiempo estimado: {est_total_time/60:.1f} minutos para procesamiento completo")
        
        # Generar embeddings para cada fragmento y añadirlos a la base de datos
        embedding_start_time = time.time()
        logger.info(f"Iniciando generación de embeddings para {chunks_count} fragmentos...")
        
        # Preparar textos y metadatos para la generación de embeddings
        batch_texts = [chunk.get('content', '') for chunk in chunks]
        batch_metadata = [chunk.get('metadata', {}) for chunk in chunks]
        
        # Opcionalmente usar el contenido enriquecido si está disponible
        enriched_texts_metadata = []
        for chunk in chunks:
            if 'enriched_content' in chunk:
                # Crear un metadata especial que incluye el contenido enriquecido
                metadata = chunk.get('metadata', {}).copy()
                metadata['enriched_content'] = chunk.get('enriched_content')
                enriched_texts_metadata.append(metadata)
            else:
                enriched_texts_metadata.append(chunk.get('metadata', {}))
                
        # Generar embeddings utilizando metadatos enriquecidos
        embeddings = self.embedding_generator.generate_embeddings_batch(batch_texts, enriched_texts_metadata)
        
        embedding_time = time.time() - embedding_start_time
        logger.info(f"Generación de embeddings completada en {embedding_time:.2f} segundos")
        
        # Guardar en la base de datos
        db_start_time = time.time()
        logger.info(f"Guardando {chunks_count} fragmentos en la base de datos...")
        
        success_count = 0
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Registrar progreso cada 50 fragmentos o en el último
            if i % 50 == 0 or i == chunks_count - 1:
                logger.info(f"Guardando en BD: {i+1}/{chunks_count} fragmentos ({(i+1)/chunks_count*100:.1f}%)")
                
            if embedding:
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                chunk_id = chunk.get('id', self._generate_chunk_id(file_metadata.get("file_id", ""), i))
                
                # Añadir a la base de datos (solo guardar el contenido original, no el enriquecido)
                if self.vector_db.add_document(chunk_id, content, metadata, embedding):
                    success_count += 1
            else:
                logger.error(f"No se pudo generar embedding para el fragmento {i} del archivo {file_metadata.get('name')}")
        
        db_time = time.time() - db_start_time
        total_time = time.time() - start_time
        
        logger.info(f"Se añadieron {success_count} de {chunks_count} fragmentos a la base de datos")
        logger.info(f"Guardado en BD completado en {db_time:.2f} segundos")
        logger.info(f"Procesamiento total completado en {total_time:.2f} segundos (~{total_time/60:.2f} minutos)")
    
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
        """Procesa todos los archivos en la carpeta monitoreada.
        
        Esta función:
        1. Identifica archivos nuevos y los procesa
        2. Identifica archivos modificados y actualiza sus registros
        3. Identifica archivos eliminados y elimina sus registros
        """
        try:
            # Obtener la lista de archivos actuales en Google Drive
            current_files = self.drive_client.list_files()
            current_file_ids = {file['id']: file for file in current_files}
            
            logger.info(f"Se encontraron {len(current_files)} archivos en Google Drive")
            
            # Obtener la lista de archivos ya procesados en la base de datos
            processed_files = self._get_processed_files()
            
            logger.info(f"Se encontraron {len(processed_files)} archivos en la base de datos")
            
            # Identificar archivos eliminados (están en la BD pero no en Drive)
            deleted_file_ids = set(processed_files.keys()) - set(current_file_ids.keys())
            
            # Procesar archivos eliminados
            if deleted_file_ids:
                logger.info(f"Procesando {len(deleted_file_ids)} archivos eliminados...")
                for file_id in deleted_file_ids:
                    file_data = processed_files[file_id]
                    logger.info(f"Eliminando archivo: {file_data.get('name', 'Desconocido')} ({file_id})")
                    self.process_deleted_file(file_data)
                logger.info("Procesamiento de archivos eliminados completado")
            else:
                logger.info("No se encontraron archivos eliminados")
            
            # Procesar archivos actuales (nuevos o modificados)
            logger.info(f"Procesando {len(current_files)} archivos actuales...")
            for file_data in current_files:
                file_id = file_data['id']
                file_name = file_data.get('name', 'Desconocido')
                drive_modified_time = file_data.get('modifiedTime', '')
                
                logger.info(f"Verificando archivo: {file_name} ({file_id})")
                logger.info(f"[FECHA] Google Drive modifiedTime: {drive_modified_time}")
                
                if file_id in processed_files:
                    # Archivo ya existente, verificar si ha sido modificado usando la fecha de modificación
                    db_modified_time = processed_files[file_id].get('last_modified', '')
                    logger.info(f"[FECHA] Fecha en BD: {db_modified_time}")
                    
                    # Normalizar formatos de fecha para comparación correcta
                    drive_time_normalized = self._normalize_date_string(drive_modified_time)
                    db_time_normalized = self._normalize_date_string(db_modified_time)
                    
                    logger.info(f"[FECHA] Comparando: Drive={drive_time_normalized} | BD={db_time_normalized}")
                    
                    # Comparación de fechas normalizadas
                    if drive_time_normalized == db_time_normalized:
                        logger.info(f"Archivo sin cambios: {file_name} (fechas idénticas después de normalizar)")
                    else:
                        logger.info(f"Archivo modificado detectado: {file_name} (fechas diferentes después de normalizar)")
                        self.process_modified_file(file_data)
                else:
                    # Archivo nuevo
                    logger.info(f"Archivo nuevo detectado: {file_name}")
                    self.process_new_file(file_data)
            
            logger.info("Procesamiento de todos los archivos completado correctamente")
        except Exception as e:
            logger.error(f"Error al procesar todos los archivos: {e}")
            # Imprimir la traza completa del error para depuración
            import traceback
            logger.error(traceback.format_exc())
    
    def _get_processed_files(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de archivos ya procesados en la base de datos.
        
        Returns:
            Dict[str, Dict[str, Any]]: Diccionario con los IDs de archivos como claves
                                      y sus metadatos como valores.
        """
        try:
            # Consultar la tabla de 'files' en Supabase
            response = self.vector_db.supabase.table("files").select("*").execute()
            files = response.data
            
            # Organizar por ID de archivo
            files_dict = {}
            for file in files:
                file_id = file.get("id")
                if file_id:
                    # Convertir metadatos si están en formato string
                    if isinstance(file.get("metadata"), str):
                        try:
                            file["metadata"] = json.loads(file.get("metadata", "{}"))
                        except:
                            file["metadata"] = {}
                    
                    files_dict[file_id] = file
            
            return files_dict
        except Exception as e:
            logger.error(f"Error al obtener la lista de archivos procesados: {e}")
            return {}
    
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
    
    def _normalize_date_string(self, date_str: str) -> str:
        """Normaliza un string de fecha para comparación.
        
        Maneja varios formatos:
        - ISO con Z: 2021-10-04T15:16:30.000Z
        - ISO con offset: 2021-10-04T15:16:30+00:00
        
        Args:
            date_str: String de fecha a normalizar
            
        Returns:
            String normalizado (2021-10-04T15:16:30)
        """
        # Remover cualquier parte después del signo + (para ISO con offset)
        if '+' in date_str:
            date_str = date_str.split('+')[0]
        
        # Remover cualquier parte después del signo Z (para ISO con Z)
        if date_str.endswith('Z'):
            date_str = date_str[:-1]
        
        # Remover cualquier fracción de segundo (.000)
        if '.' in date_str:
            parts = date_str.split('.')
            date_str = parts[0]
        
        return date_str 