#!/usr/bin/env python
"""
Script de depuración para identificar problemas con el procesamiento de archivos.
"""

import os
import sys
import logging
from pprint import pprint

# Configurar logging básico para este script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.document_manager import DocumentManager
from app.drive.google_drive_client import GoogleDriveClient
from app.database.vector_store import VectorDatabase

def debug_document_manager():
    """Depura el gestor de documentos."""
    print("\n=== DEBUGGING DOCUMENT MANAGER ===\n")
    
    # Inicializar componentes
    drive_client = GoogleDriveClient()
    vector_db = VectorDatabase()
    document_manager = DocumentManager()
    
    # 1. Verificar archivos en Google Drive
    print("\n--- ARCHIVOS EN GOOGLE DRIVE ---\n")
    try:
        drive_files = drive_client.list_files()
        print(f"Archivos encontrados en Google Drive: {len(drive_files)}")
        for i, file in enumerate(drive_files, 1):
            print(f"{i}. {file.get('name')} (ID: {file.get('id')})")
    except Exception as e:
        print(f"Error al listar archivos de Google Drive: {e}")
    
    # 2. Verificar archivos en la base de datos
    print("\n--- ARCHIVOS EN BASE DE DATOS ---\n")
    try:
        response = vector_db.supabase.table("files").select("*").execute()
        db_files = response.data
        print(f"Archivos encontrados en la base de datos: {len(db_files)}")
        for i, file in enumerate(db_files, 1):
            print(f"{i}. {file.get('name')} (ID: {file.get('id')})")
    except Exception as e:
        print(f"Error al listar archivos de la base de datos: {e}")
    
    # 3. Verificar fragmentos en la colección de embeddings
    print("\n--- FRAGMENTOS EN COLECCIÓN DE EMBEDDINGS ---\n")
    try:
        for file in db_files:
            file_id = file.get('id')
            chunks = vector_db.get_chunks_by_file_id(file_id)
            print(f"Fragmentos para {file.get('name')}: {len(chunks)}")
    except Exception as e:
        print(f"Error al listar fragmentos: {e}")
    
    # 4. Verificar el funcionamiento de process_all_files
    print("\n--- SIMULACIÓN DE PROCESS_ALL_FILES ---\n")
    try:
        # Obtener archivos actuales de Drive
        current_files = drive_client.list_files()
        current_file_ids = {file['id']: file for file in current_files}
        print(f"Archivos en Drive: {len(current_file_ids)}")
        
        # Obtener archivos procesados
        # Esta es una adaptación del método _get_processed_files que agregamos
        response = vector_db.supabase.table("files").select("*").execute()
        files = response.data
        processed_files = {}
        for file in files:
            file_id = file.get("id")
            if file_id:
                processed_files[file_id] = file
        print(f"Archivos procesados en BD: {len(processed_files)}")
        
        # Identificar archivos eliminados
        deleted_file_ids = set(processed_files.keys()) - set(current_file_ids.keys())
        print(f"Archivos detectados como eliminados: {len(deleted_file_ids)}")
        for file_id in deleted_file_ids:
            file = processed_files[file_id]
            print(f"  - {file.get('name')} (ID: {file_id})")
            
        # Verificar si se llamaría a process_deleted_file
        if deleted_file_ids:
            print("\nSe debería llamar a process_deleted_file para:")
            for file_id in deleted_file_ids:
                print(f"  - {processed_files[file_id].get('name')}")
    except Exception as e:
        print(f"Error en la simulación: {e}")

if __name__ == "__main__":
    debug_document_manager() 