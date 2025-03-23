#!/usr/bin/env python
"""
Script para mostrar el contenido y metadatos de un chunk específico de la base de datos
buscándolo por su índice (chunk_index) dentro de metadata.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Añadir la ruta del proyecto al path para poder importar los módulos de la aplicación
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar módulos necesarios después de añadir la ruta
from app.database.supabase_client import get_supabase_client

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_metadata(metadata):
    """Formatea los metadatos para una mejor visualización."""
    if not metadata:
        return "No hay metadatos"
    
    formatted = []
    for key, value in metadata.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, indent=2, ensure_ascii=False)
        formatted.append(f"{key}: {value}")
    return "\n".join(formatted)

def show_chunk_by_index(chunk_index, file_id, supabase):
    """Muestra el contenido y metadatos de un chunk específico buscando por chunk_index."""
    try:
        # Usar el enfoque estándar de la API de Supabase para buscar el chunk
        result = supabase.table("documents").select("*").filter("metadata->>chunk_index", "eq", str(chunk_index))
        if file_id:
            result = result.filter("metadata->>file_id", "eq", file_id)
        result = result.execute()
        
        if not result.data or len(result.data) == 0:
            if file_id:
                logger.error(f"No se encontró chunk con índice {chunk_index} y file_id {file_id}")
            else:
                logger.error(f"No se encontró chunk con índice {chunk_index}")
            return False
        
        chunk = result.data[0]
        
        # Mostrar información del chunk
        print("\n=== Información del Chunk ===")
        print(f"ID: {chunk['id']}")
        print(f"Chunk Index: {chunk['metadata'].get('chunk_index', 'No disponible')}")
        print(f"Total Chunks: {chunk['metadata'].get('total_chunks', 'No disponible')}")
        print(f"File ID: {chunk['metadata'].get('file_id', 'No disponible')}")
        print(f"File Name: {chunk['metadata'].get('name', 'No disponible')}")
        print(f"Fecha de creación: {chunk['created_at']}")
        
        print("\n=== Contenido ===")
        print(chunk['content'])
        
        print("\n=== Metadatos Completos ===")
        print(format_metadata(chunk['metadata']))
        
        return True
        
    except Exception as e:
        logger.error(f"Error al buscar el chunk: {e}")
        return False

def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description='Muestra el contenido y metadatos de un chunk específico por su índice.')
    parser.add_argument('chunk_index', type=int, help='Índice del chunk a mostrar (chunk_index)')
    parser.add_argument('--file_id', '-f', help='ID del archivo al que pertenece el chunk (opcional)')
    
    args = parser.parse_args()
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar que las variables necesarias estén definidas
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        logger.error("Las variables de entorno SUPABASE_URL y SUPABASE_KEY deben estar definidas en el archivo .env")
        return 1
    
    # Inicializar cliente de Supabase
    try:
        supabase_store = get_supabase_client()
        supabase = supabase_store.get_client()
        logger.info("Conexión a Supabase establecida correctamente")
    except Exception as e:
        logger.error(f"Error al conectar con Supabase: {e}")
        return 1
    
    # Mostrar el chunk por su índice
    if not show_chunk_by_index(args.chunk_index, args.file_id, supabase):
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 