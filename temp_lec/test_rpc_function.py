"""
Script para probar directamente la función RPC get_chunks_by_file_id en Supabase.
Este script utiliza el cliente de Supabase para ejecutar consultas directas
y verificar el comportamiento de la función RPC.
"""

import os
import sys
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from app.database.supabase_client import get_supabase_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_rpc_function():
    """Prueba directamente la función RPC get_chunks_by_file_id en Supabase."""
    try:
        # Obtener el cliente de Supabase
        supabase = get_supabase_client().get_client()
        
        # Primero, obtener un file_id válido de los documentos
        print("Buscando documentos para obtener un file_id válido...")
        
        # Consultar los primeros 5 documentos
        result = supabase.table("documents").select("metadata").limit(5).execute()
        
        if not result.data:
            logger.info("No se encontraron documentos en la base de datos.")
            return
        
        # Buscar un file_id válido en los metadatos de los documentos
        file_ids = []
        for doc in result.data:
            metadata = doc.get('metadata', {})
            
            # Si metadata es una cadena JSON, convertirla a diccionario
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    continue
            
            # Buscar file_id en metadata
            file_id = None
            if isinstance(metadata, dict):
                # Intentar diferentes posibles ubicaciones para file_id
                file_id = metadata.get('file_id')
                if not file_id:
                    # Buscar en source o en cualquier otra estructura anidada
                    for key, value in metadata.items():
                        if isinstance(value, dict) and 'file_id' in value:
                            file_id = value['file_id']
                            break
            
            if file_id and file_id not in file_ids:
                file_ids.append(file_id)
        
        print(f"Se encontraron {len(file_ids)} file_ids únicos: {file_ids}")
        
        # Si no hay file_ids, usar un ID fijo para probar
        if not file_ids:
            file_ids = ['1UVkoJj_YlwZzQIjFXP47yzu0U95Cmbhy']
            print(f"No se encontraron file_ids en los metadatos. Usando ID fijo: {file_ids[0]}")
        
        # Probar la función RPC con cada file_id encontrado
        for file_id in file_ids:
            print(f"\nProbando función RPC get_chunks_by_file_id con file_id: {file_id}")
            
            # Ejecutar la función RPC
            try:
                result = supabase.rpc(
                    "get_chunks_by_file_id",
                    {"file_id": file_id}
                ).execute()
                
                print(f"Resultado: {len(result.data)} fragmentos encontrados")
                
                # Mostrar los metadatos del primer fragmento (si existe)
                if result.data:
                    print(f"Metadatos del primer fragmento: {result.data[0].get('metadata', {})}")
                
            except Exception as e:
                logger.error(f"Error al ejecutar la función RPC: {e}")
            
            # Probar una consulta SQL directa para comparar
            print(f"\nProbando consulta SQL directa para file_id: {file_id}")
            try:
                # En PostgreSQL, la sintaxis para acceder a campos JSONB es con ->>
                query = f"""
                SELECT id, metadata 
                FROM documents 
                WHERE metadata->>'file_id' = '{file_id}'
                LIMIT 5
                """
                
                print(f"Consulta SQL: {query}")
                
                # Ejecutar la consulta SQL
                result = supabase.postgrest.rpc("execute_sql", {"sql": query}).execute()
                
                print(f"Resultado de la consulta SQL: {result.data}")
                
            except Exception as e:
                logger.error(f"Error al ejecutar la consulta SQL: {e}")
                print("Nota: Es posible que la función 'execute_sql' no exista en su instancia de Supabase")
                
                # Intentar con una consulta directa a la tabla
                try:
                    print("\nIntentando una consulta directa a la tabla documents:")
                    # Usar la sintaxis del cliente de Supabase para filtrar por JSONB
                    result = supabase.table("documents").select("id, metadata").eq("metadata->>file_id", file_id).limit(5).execute()
                    
                    print(f"Resultado de la consulta directa: {len(result.data)} documentos encontrados")
                    if result.data:
                        print(f"Primer documento: {result.data[0]}")
                except Exception as inner_e:
                    logger.error(f"Error en la consulta directa: {inner_e}")
        
    except Exception as e:
        logger.error(f"Error en la prueba de la función RPC: {e}")

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Ejecutar la prueba
    test_rpc_function() 