"""
Gestión de la base de datos vectorial.
Este módulo proporciona funciones para gestionar documentos y embeddings en la base de datos vectorial.
"""

import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config.settings import SUPABASE_COLLECTION_NAME
from app.database.supabase_client import get_supabase_client

# Configurar logging
logger = logging.getLogger(__name__)

class VectorDatabase:
    """Clase para gestionar la base de datos vectorial."""
    
    def __init__(self, collection_name: str = None):
        """Inicializa la base de datos vectorial.
        
        Args:
            collection_name: Nombre de la colección a utilizar. Si no se proporciona,
                             se utiliza el valor de SUPABASE_COLLECTION_NAME.
        """
        self.collection_name = collection_name or SUPABASE_COLLECTION_NAME
        self.supabase_store = get_supabase_client()
        self.supabase = self.supabase_store.get_client()
        logger.info(f"Base de datos vectorial inicializada con colección: {self.collection_name}")
        
    def add_document(self, document_id: str, content: str, metadata: dict, embedding: List[float]) -> bool:
        """Añade un documento a la base de datos vectorial.
        
        Args:
            document_id: ID único del documento.
            content: Contenido del documento.
            metadata: Metadatos del documento.
            embedding: Vector de embedding del documento.
            
        Returns:
            bool: True si se agregó correctamente, False en caso contrario.
        """
        try:
            # Formatear el metadato en formato JSON para almacenamiento
            file_id = metadata.get("file_id", "")
            chunk_index = metadata.get("chunk_index", "")
            
            # Preparar los metadatos para almacenamiento
            metadata_json = json.dumps(metadata)
            
            # Verificar si el documento ya existe
            response = self.supabase.table(self.collection_name).select("*").eq("id", document_id).execute()
            
            if response.data and len(response.data) > 0:
                # Actualizar el documento existente
                logger.info(f"Actualizando fragmento existente {chunk_index} de archivo {file_id}")
                response = self.supabase.table(self.collection_name).update({
                    "content": content,
                    "metadata": metadata_json,
                    "embedding": embedding
                }).eq("id", document_id).execute()
            else:
                # Insertar nuevo documento
                logger.info(f"Insertando nuevo fragmento {chunk_index} de archivo {file_id}")
                response = self.supabase.table(self.collection_name).insert({
                    "id": document_id,
                    "content": content,
                    "metadata": metadata_json,
                    "embedding": embedding
                }).execute()
            
            # Actualizar o crear el registro de archivo en la tabla 'files'
            self._update_file_record(metadata)
            
            logger.debug(f"Documento {document_id} (fragmento {chunk_index}) añadido correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al añadir el documento {document_id}: {e}")
            return False
    
    def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any], embedding: List[float]) -> bool:
        """Actualiza un documento existente.
        
        Args:
            doc_id: Identificador único del documento.
            content: Nuevo contenido del documento.
            metadata: Nuevos metadatos del documento.
            embedding: Nuevo vector de embedding del documento.
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario.
        """
        try:
            # Preparar la actualización
            update_data = {
                "content": content,
                "metadata": metadata,
                "embedding": embedding,
                "updated_at": datetime.now().isoformat()
            }
            
            # Actualizar el documento
            result = self.supabase.table(self.collection_name).update(update_data).eq("id", doc_id).execute()
            
            # Actualizar el registro del archivo si es un fragmento de Google Drive
            if metadata.get("source") == "google_drive" and metadata.get("file_id"):
                self._update_or_create_file_record(metadata)
            
            logger.info(f"Documento {doc_id} actualizado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar el documento {doc_id}: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Elimina un documento de la base de datos.
        
        Args:
            doc_id: Identificador único del documento.
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario.
        """
        try:
            # Obtener los metadatos antes de eliminar
            doc = self.supabase.table(self.collection_name).select("metadata").eq("id", doc_id).execute()
            
            # Eliminar el documento
            result = self.supabase.table(self.collection_name).delete().eq("id", doc_id).execute()
            
            logger.info(f"Documento {doc_id} eliminado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar el documento {doc_id}: {e}")
            return False
    
    def similarity_search(self, query_embedding: List[float], top_k: int = 5, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Realiza una búsqueda por similitud.
        
        Args:
            query_embedding: Vector de embedding de la consulta.
            top_k: Número máximo de resultados a devolver.
            threshold: Umbral de similitud mínimo (valor predeterminado reducido a 0.1).
            
        Returns:
            List[Dict[str, Any]]: Lista de documentos similares.
        """
        try:
            # Verificar que query_embedding sea una lista de números
            if isinstance(query_embedding, str):
                # Convertir de string a lista si es necesario
                try:
                    query_embedding = json.loads(query_embedding)
                except:
                    logger.error("Error al convertir embedding de string a lista")
            
            # Realizar la búsqueda por similitud usando la función RPC
            result = self.supabase.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": top_k
                }
            ).execute()
            
            logger.info(f"Búsqueda por similitud completada: {len(result.data)} resultados")
            return result.data
            
        except Exception as e:
            logger.error(f"Error en la búsqueda por similitud: {e}")
            return []
    
    def get_chunks_by_file_id(self, file_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los fragmentos de un archivo específico.
        
        Args:
            file_id: Identificador único del archivo.
            
        Returns:
            List[Dict[str, Any]]: Lista de fragmentos del archivo.
        """
        try:
            # Usar la función RPC para obtener los fragmentos
            result = self.supabase.rpc(
                "get_chunks_by_file_id",
                {"file_id": file_id}
            ).execute()
            
            logger.info(f"Fragmentos obtenidos para el archivo {file_id}: {len(result.data)}")
            return result.data
            
        except Exception as e:
            logger.error(f"Error al obtener fragmentos del archivo {file_id}: {e}")
            return []
    
    def delete_chunks_by_file_id(self, file_id: str) -> int:
        """Elimina todos los fragmentos de un archivo específico.
        
        Args:
            file_id: Identificador único del archivo.
            
        Returns:
            int: Número de fragmentos eliminados.
        """
        try:
            # Primero contar cuántos fragmentos hay
            result = self.supabase.table(self.collection_name).select("id").filter("metadata->>file_id", "eq", file_id).execute()
            
            count = len(result.data) if result.data else 0
            
            if count == 0:
                logger.info(f"No se encontraron fragmentos para el archivo {file_id}")
                return 0
                
            # Luego eliminar los fragmentos
            result = self.supabase.table(self.collection_name).delete().filter("metadata->>file_id", "eq", file_id).execute()
            
            logger.info(f"Se eliminaron {count} fragmentos del archivo {file_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error al eliminar fragmentos del archivo {file_id}: {e}")
            return 0
    
    def _update_or_create_file_record(self, metadata: Dict[str, Any]) -> bool:
        """Actualiza o crea un registro de archivo.
        
        Args:
            metadata: Metadatos del fragmento.
            
        Returns:
            bool: True si se actualizó o creó correctamente, False en caso contrario.
        """
        try:
            file_id = metadata.get("file_id")
            if not file_id:
                return False
            
            chunk_index = metadata.get("chunk_index", "")
            
            # Verificar si el archivo ya existe
            existing_file = self.supabase.table("files").select("*").eq("id", file_id).execute()
            
            file_data = {
                "name": metadata.get("name", "Unknown"),
                "mime_type": metadata.get("mime_type", "application/octet-stream"),
                "source": metadata.get("source", "google_drive"),
                "last_modified": metadata.get("modified_time", datetime.now().isoformat()),
                "processed_at": datetime.now().isoformat(),
                "status": "processed",
                "metadata": json.dumps({
                    "total_chunks": metadata.get("total_chunks", 1),
                    "size": metadata.get("size", 0),
                    "checksum": metadata.get("checksum", "")
                })
            }
            
            if existing_file.data:
                # Actualizar el archivo existente
                result = self.supabase.table("files").update(file_data).eq("id", file_id).execute()
                logger.info(f"Registro de archivo {file_id} (fragmento {chunk_index}) actualizado")
            else:
                # Crear un nuevo registro de archivo
                file_data["id"] = file_id
                result = self.supabase.table("files").insert(file_data).execute()
                logger.info(f"Registro de archivo {file_id} (fragmento {chunk_index}) creado")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar registro de archivo: {e}")
            return False
    
    def _update_file_record(self, metadata: Dict[str, Any]) -> bool:
        """Actualiza o crea un registro de archivo.
        
        Args:
            metadata: Metadatos del fragmento.
            
        Returns:
            bool: True si se actualizó o creó correctamente, False en caso contrario.
        """
        try:
            file_id = metadata.get("file_id")
            if not file_id:
                return False
            
            chunk_index = metadata.get("chunk_index", "")
            
            # Verificar si el archivo ya existe
            existing_file = self.supabase.table("files").select("*").eq("id", file_id).execute()
            
            file_data = {
                "name": metadata.get("name", "Unknown"),
                "mime_type": metadata.get("mime_type", "application/octet-stream"),
                "source": metadata.get("source", "google_drive"),
                "last_modified": metadata.get("modified_time", datetime.now().isoformat()),
                "processed_at": datetime.now().isoformat(),
                "status": "processed",
                "metadata": json.dumps({
                    "total_chunks": metadata.get("total_chunks", 1),
                    "size": metadata.get("size", 0),
                    "checksum": metadata.get("checksum", "")
                })
            }
            
            if existing_file.data:
                # Actualizar el archivo existente
                result = self.supabase.table("files").update(file_data).eq("id", file_id).execute()
                logger.info(f"Registro de archivo {file_id} (fragmento {chunk_index}) actualizado")
            else:
                # Crear un nuevo registro de archivo
                file_data["id"] = file_id
                result = self.supabase.table("files").insert(file_data).execute()
                logger.info(f"Registro de archivo {file_id} (fragmento {chunk_index}) creado")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar registro de archivo: {e}")
            return False
    
    def log_query(self, query: str, response: str, sources: List[Dict[str, Any]]) -> bool:
        """Registra una consulta en la base de datos.
        
        Args:
            query: Consulta realizada.
            response: Respuesta generada.
            sources: Fuentes utilizadas para generar la respuesta.
            
        Returns:
            bool: True si se registró correctamente, False en caso contrario.
        """
        try:
            # Preparar los datos de la consulta
            query_data = {
                "query": query,
                "response": response,
                "sources": sources,
                "created_at": datetime.now().isoformat()
            }
            
            # Insertar la consulta
            result = self.supabase.table("queries").insert(query_data).execute()
            
            logger.info(f"Consulta registrada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar la consulta: {e}")
            return False
    
    def get_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene las consultas registradas.
        
        Args:
            limit: Número máximo de consultas a devolver.
            
        Returns:
            List[Dict[str, Any]]: Lista de consultas.
        """
        try:
            # Obtener las consultas
            result = self.supabase.table("queries").select("*").order("created_at", desc=True).limit(limit).execute()
            
            logger.info(f"Consultas obtenidas: {len(result.data)}")
            return result.data
            
        except Exception as e:
            logger.error(f"Error al obtener las consultas: {e}")
            return [] 