"""
Monitor de carpetas de Google Drive.
Este módulo proporciona funciones para monitorear cambios en una carpeta de Google Drive.
"""

import logging
import time
import json
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import threading

from app.drive.google_drive_client import GoogleDriveClient
from app.config.settings import GOOGLE_DRIVE_FOLDER_ID

# Configurar logging
logger = logging.getLogger(__name__)

class GoogleDriveFolderMonitor:
    """Clase para monitorear cambios en una carpeta de Google Drive."""
    
    def __init__(self, folder_id: str = GOOGLE_DRIVE_FOLDER_ID, check_interval: int = 60):
        """Inicializa el monitor de carpetas.
        
        Args:
            folder_id: ID de la carpeta a monitorear.
            check_interval: Intervalo de verificación en segundos.
        """
        self.folder_id = folder_id
        self.check_interval = check_interval
        self.drive_client = GoogleDriveClient(folder_id=folder_id)
        self.last_check_time = None
        self.known_files = {}  # Diccionario para almacenar los archivos conocidos
        self.running = False
        self.monitor_thread = None
        self.callbacks = {
            "new_file": [],
            "modified_file": [],
            "deleted_file": []
        }
        
        # Cargar el estado anterior si existe
        self._load_state()
        
        logger.info(f"Monitor de carpetas inicializado para la carpeta {folder_id}")
    
    def _load_state(self):
        """Carga el estado anterior del monitor desde un archivo."""
        state_file = "drive_monitor_state.json"
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    self.known_files = state.get("known_files", {})
                    last_check = state.get("last_check_time")
                    if last_check:
                        self.last_check_time = datetime.fromisoformat(last_check)
                logger.info("Estado del monitor cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar el estado del monitor: {e}")
    
    def _save_state(self):
        """Guarda el estado actual del monitor en un archivo."""
        state_file = "drive_monitor_state.json"
        try:
            state = {
                "known_files": self.known_files,
                "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None
            }
            with open(state_file, "w") as f:
                json.dump(state, f)
            logger.info("Estado del monitor guardado correctamente")
        except Exception as e:
            logger.error(f"Error al guardar el estado del monitor: {e}")
    
    def register_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Registra una función de callback para un tipo de evento.
        
        Args:
            event_type: Tipo de evento ('new_file', 'modified_file', 'deleted_file').
            callback: Función a llamar cuando ocurra el evento.
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"Callback registrado para el evento {event_type}")
        else:
            logger.error(f"Tipo de evento desconocido: {event_type}")
    
    def _trigger_callbacks(self, event_type: str, file_data: Dict[str, Any]):
        """Dispara los callbacks registrados para un tipo de evento.
        
        Args:
            event_type: Tipo de evento.
            file_data: Datos del archivo.
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(file_data)
                except Exception as e:
                    logger.error(f"Error en callback para {event_type}: {e}")
    
    def check_for_changes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Verifica si hay cambios en la carpeta monitoreada.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Diccionario con listas de archivos nuevos, modificados y eliminados.
        """
        current_time = datetime.now()
        
        # Obtener la lista actual de archivos
        current_files = {file['id']: file for file in self.drive_client.list_files()}
        
        # Identificar archivos nuevos, modificados y eliminados
        new_files = []
        modified_files = []
        deleted_files = []
        
        # Comprobar archivos nuevos y modificados
        for file_id, file_data in current_files.items():
            if file_id not in self.known_files:
                # Archivo nuevo
                new_files.append(file_data)
                self._trigger_callbacks("new_file", file_data)
            else:
                # Comprobar si el archivo ha sido modificado
                known_modified_time = self.known_files[file_id].get('modifiedTime', '')
                current_modified_time = file_data.get('modifiedTime', '')
                
                if current_modified_time > known_modified_time:
                    # Archivo modificado
                    modified_files.append(file_data)
                    self._trigger_callbacks("modified_file", file_data)
        
        # Comprobar archivos eliminados
        for file_id in self.known_files:
            if file_id not in current_files:
                # Archivo eliminado
                deleted_file = self.known_files[file_id]
                deleted_files.append(deleted_file)
                self._trigger_callbacks("deleted_file", deleted_file)
        
        # Actualizar la lista de archivos conocidos
        self.known_files = current_files
        self.last_check_time = current_time
        
        # Guardar el estado
        self._save_state()
        
        changes = {
            "new": new_files,
            "modified": modified_files,
            "deleted": deleted_files
        }
        
        logger.info(f"Cambios detectados: {len(new_files)} nuevos, {len(modified_files)} modificados, {len(deleted_files)} eliminados")
        return changes
    
    def start_monitoring(self):
        """Inicia el monitoreo de la carpeta en un hilo separado."""
        if self.running:
            logger.warning("El monitor ya está en ejecución")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo de la carpeta."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=self.check_interval + 5)
        logger.info("Monitoreo detenido")
    
    def _monitoring_loop(self):
        """Bucle principal de monitoreo."""
        while self.running:
            try:
                self.check_for_changes()
            except Exception as e:
                logger.error(f"Error en el bucle de monitoreo: {e}")
            
            # Esperar hasta la próxima verificación
            time.sleep(self.check_interval) 