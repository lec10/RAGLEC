"""
Script para examinar cómo se almacenan los documentos en la base de datos.
Este script analiza la estructura de datos de documentos y archivos
para detectar posibles problemas en la forma en que se guarda el file_id.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from app.database.supabase_client import get_supabase_client
from app.database.vector_store import VectorDatabase
from app.core.document_manager import DocumentManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def examine_documents():
    """Examina los documentos almacenados en la base de datos."""
    try:
        # Inicializar la base de datos vectorial
        db = VectorDatabase()
        
        # 1. Analizar la tabla de documentos
        print("=== ANÁLISIS DE LA TABLA DOCUMENTS ===")
        
        # Obtener todos los documentos (limitado a 10 para no sobrecargar)
        result = db.supabase.table("documents").select("id, content, metadata, created_at").limit(10).execute()
        
        if not result.data:
            print("No se encontraron documentos en la tabla documents.")
            return
        
        print(f"Se encontraron {len(result.data)} documentos.")
        
        # Análisis de los metadatos
        print("\nAnalizando estructura de metadatos:")
        metadata_structures = {}
        
        for doc in result.data:
            metadata = doc.get('metadata', {})
            
            # Detectar el tipo de metadata
            metadata_type = type(metadata).__name__
            
            if metadata_type not in metadata_structures:
                metadata_structures[metadata_type] = {"count": 0, "keys": set()}
            
            metadata_structures[metadata_type]["count"] += 1
            
            # Si es un diccionario, recolectar las claves
            if isinstance(metadata, dict):
                metadata_structures[metadata_type]["keys"].update(metadata.keys())
        
        # Mostrar resultados del análisis de metadatos
        for type_name, info in metadata_structures.items():
            print(f"Tipo de metadata: {type_name}")
            print(f"  Cantidad: {info['count']}")
            
            if "keys" in info:
                print(f"  Claves encontradas: {sorted(list(info['keys']))}")
        
        # 2. Analizar la tabla de archivos
        print("\n=== ANÁLISIS DE LA TABLA FILES ===")
        
        # Obtener los archivos
        files_result = db.supabase.table("files").select("*").limit(10).execute()
        
        if not files_result.data:
            print("No se encontraron archivos en la tabla files.")
        else:
            print(f"Se encontraron {len(files_result.data)} archivos.")
            
            # Mostrar los IDs de los archivos
            file_ids = [file.get('id') for file in files_result.data]
            print(f"IDs de archivos: {file_ids}")
            
            # Verificar si estos IDs existen como file_id en los documentos
            for file_id in file_ids:
                chunks = db.get_chunks_by_file_id(file_id)
                print(f"Archivo {file_id}: {len(chunks)} fragmentos asociados")
        
        # 3. Verificar cómo se almacenan los documentos al procesar un archivo
        print("\n=== SIMULACIÓN DE PROCESAMIENTO DE ARCHIVO ===")
        print("Nota: Esta sección solo muestra cómo se estructurarían los metadatos al procesar un archivo")
        
        # Crear un gestor de documentos simulado
        doc_manager = DocumentManager()
        
        # Simular metadatos para un documento
        file_id = "example_file_123"
        file_metadata = {
            "file_id": file_id,
            "file_name": "example.txt",
            "mime_type": "text/plain",
            "source": "google_drive",
            "last_modified": "2023-01-01T00:00:00Z",
            "chunk_index": 0,
            "total_chunks": 2
        }
        
        # Mostrar cómo se generaría un ID de fragmento
        chunk_id = doc_manager._generate_chunk_id(file_id, 0)
        print(f"ID de fragmento generado para file_id={file_id}, chunk_index=0: {chunk_id}")
        
        # Mostrar la estructura de metadatos que se usaría
        print(f"Estructura de metadatos que se utilizaría:")
        print(json.dumps(file_metadata, indent=2))
        
    except Exception as e:
        logger.error(f"Error al examinar documentos: {e}")

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Ejecutar el análisis
    examine_documents() 