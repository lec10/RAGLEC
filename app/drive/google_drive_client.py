"""
Cliente de Google Drive.
Este módulo proporciona funciones para interactuar con la API de Google Drive.
"""

import logging
import os
import io
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import tempfile

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.config.settings import GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_DRIVE_FOLDER_ID

# Configurar logging
logger = logging.getLogger(__name__)

class GoogleDriveClient:
    """Clase para interactuar con la API de Google Drive."""
    
    def __init__(self, credentials_path: str = GOOGLE_APPLICATION_CREDENTIALS, folder_id: str = GOOGLE_DRIVE_FOLDER_ID):
        """Inicializa el cliente de Google Drive.
        
        Args:
            credentials_path: Ruta al archivo de credenciales de servicio.
            folder_id: ID de la carpeta a monitorear.
        """
        self.credentials_path = credentials_path
        self.folder_id = folder_id
        self.service = self._create_drive_service()
        logger.info("Cliente de Google Drive inicializado")
    
    def _create_drive_service(self):
        """Crea un servicio de Google Drive.
        
        Returns:
            Servicio de Google Drive.
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=credentials)
            return service
        except Exception as e:
            logger.error(f"Error al crear el servicio de Google Drive: {e}")
            raise
    
    def list_files(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista los archivos en una carpeta de Google Drive.
        
        Args:
            folder_id: ID de la carpeta (opcional, usa el predeterminado si no se proporciona).
            
        Returns:
            List[Dict[str, Any]]: Lista de archivos con sus metadatos.
        """
        try:
            folder_id = folder_id or self.folder_id
            
            # Consultar los archivos en la carpeta
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, md5Checksum)",
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Se encontraron {len(files)} archivos en la carpeta {folder_id}")
            return files
        except Exception as e:
            logger.error(f"Error al listar archivos en la carpeta {folder_id}: {e}")
            return []
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los metadatos de un archivo.
        
        Args:
            file_id: ID del archivo.
            
        Returns:
            Dict[str, Any] o None: Metadatos del archivo si existe, None en caso contrario.
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, md5Checksum"
            ).execute()
            return file
        except Exception as e:
            logger.error(f"Error al obtener metadatos del archivo {file_id}: {e}")
            return None
    
    def download_file(self, file_id: str, output_path: Optional[str] = None) -> Optional[str]:
        """Descarga un archivo de Google Drive.
        
        Args:
            file_id: ID del archivo a descargar.
            output_path: Ruta donde guardar el archivo (opcional).
            
        Returns:
            str o None: Ruta al archivo descargado si se descargó correctamente, None en caso contrario.
        """
        try:
            # Obtener metadatos del archivo
            file_metadata = self.get_file_metadata(file_id)
            if not file_metadata:
                return None
            
            # Crear una solicitud para descargar el archivo
            request = self.service.files().get_media(fileId=file_id)
            
            # Si no se proporciona una ruta de salida, crear un archivo temporal
            if not output_path:
                # Crear un directorio temporal si no existe
                temp_dir = os.path.join(tempfile.gettempdir(), "google_drive_downloads")
                os.makedirs(temp_dir, exist_ok=True)
                
                # Generar un nombre de archivo basado en el ID y el nombre
                file_name = file_metadata.get('name', file_id)
                output_path = os.path.join(temp_dir, file_name)
            
            # Descargar el archivo
            with io.FileIO(output_path, 'wb') as file:
                downloader = MediaIoBaseDownload(file, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            logger.info(f"Archivo {file_id} descargado correctamente a {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error al descargar el archivo {file_id}: {e}")
            return None
    
    def get_file_changes(self, last_check_time: Optional[datetime] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Obtiene los cambios en los archivos desde la última verificación.
        
        Args:
            last_check_time: Hora de la última verificación (opcional).
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Diccionario con listas de archivos nuevos, modificados y eliminados.
        """
        try:
            # Obtener la lista actual de archivos
            current_files = self.list_files()
            
            # Si no hay tiempo de última verificación, considerar todos los archivos como nuevos
            if not last_check_time:
                return {
                    "new": current_files,
                    "modified": [],
                    "deleted": []
                }
            
            # Convertir last_check_time a formato ISO para comparar con modifiedTime
            last_check_iso = last_check_time.isoformat() + "Z"
            
            # Clasificar los archivos
            new_files = []
            modified_files = []
            
            for file in current_files:
                modified_time = file.get('modifiedTime', '')
                
                # Comparar las fechas de modificación
                if modified_time > last_check_iso:
                    # Verificar si el archivo es nuevo o modificado
                    file_metadata = self.get_file_metadata(file['id'])
                    if file_metadata:
                        modified_files.append(file_metadata)
                    else:
                        new_files.append(file)
            
            # No podemos determinar los archivos eliminados sin una lista previa
            # Esto se manejará en una capa superior que mantenga un registro de los archivos
            
            return {
                "new": new_files,
                "modified": modified_files,
                "deleted": []  # Se determinará en una capa superior
            }
        except Exception as e:
            logger.error(f"Error al obtener cambios en los archivos: {e}")
            return {"new": [], "modified": [], "deleted": []} 