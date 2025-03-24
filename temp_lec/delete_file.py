#!/usr/bin/env python
"""
Script para eliminar manualmente un archivo de la base de datos.
"""

import os
import sys
import logging
import argparse

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.vector_store import VectorDatabase

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def delete_file(file_id):
    """Elimina un archivo de la base de datos.
    
    Args:
        file_id (str): ID del archivo a eliminar.
    """
    try:
        # Obtener cliente de base de datos
        db = VectorDatabase()
        
        # Verificar que el archivo existe
        response = db.supabase.table("files").select("*").eq("id", file_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"El archivo con ID {file_id} no existe en la base de datos")
            return False
        
        file = response.data[0]
        logger.info(f"Eliminando archivo: {file.get('name', 'Desconocido')} ({file_id})")
        
        # Eliminar fragmentos
        deleted_count = db.delete_chunks_by_file_id(file_id)
        logger.info(f"Se eliminaron {deleted_count} fragmentos del archivo {file_id}")
        
        # Eliminar registro de archivo
        response = db.supabase.table("files").delete().eq("id", file_id).execute()
        deleted_files = len(response.data) if response.data else 0
        logger.info(f"Se eliminó el registro del archivo de la tabla 'files': {deleted_files} registros afectados")
        
        return True
    except Exception as e:
        logger.error(f"Error al eliminar el archivo {file_id}: {e}")
        return False

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Eliminar manualmente un archivo de la base de datos")
    parser.add_argument("file_id", help="ID del archivo a eliminar")
    
    args = parser.parse_args()
    
    if delete_file(args.file_id):
        logger.info("Archivo eliminado correctamente")
    else:
        logger.error("No se pudo eliminar el archivo")

if __name__ == "__main__":
    main() 