#!/usr/bin/env python
"""
Script para identificar y eliminar registros huérfanos en la tabla de documentos.
Estos son fragmentos cuyos file_id ya no existen en la tabla 'files'.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.supabase_client import get_supabase_client
from app.config.settings import SUPABASE_COLLECTION_NAME
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), "orphans_cleanup.log"))
    ]
)

logger = logging.getLogger(__name__)

def identify_orphaned_chunks(dry_run=True):
    """
    Identifica y opcionalmente elimina fragmentos huérfanos en la base de datos.
    
    Args:
        dry_run (bool): Si es True, solo identifica sin eliminar. Si es False, elimina los fragmentos.
    
    Returns:
        dict: Estadísticas de la operación
    """
    logger.info("Iniciando identificación de fragmentos huérfanos...")
    
    try:
        # Obtener cliente de Supabase
        supabase_store = get_supabase_client()
        supabase = supabase_store.get_client()
        collection_name = SUPABASE_COLLECTION_NAME
        
        logger.info(f"Conectado a Supabase. Colección: {collection_name}")
        
        # 1. Obtener todos los IDs de archivos en la tabla 'files'
        logger.info("Obteniendo lista de archivos en la tabla 'files'...")
        response_files = supabase.table("files").select("id").execute()
        existing_file_ids = set([file['id'] for file in response_files.data]) if response_files.data else set()
        
        logger.info(f"Encontrados {len(existing_file_ids)} archivos en la tabla 'files'")
        
        # 2. Obtener todos los fragmentos con sus metadatos
        logger.info("Obteniendo todos los fragmentos de la tabla de documentos...")
        response_chunks = supabase.table(collection_name).select("id, metadata").execute()
        
        if not response_chunks.data:
            logger.info("No se encontraron fragmentos en la base de datos")
            return {"status": "completed", "orphaned_chunks": 0, "deleted": 0}
        
        logger.info(f"Encontrados {len(response_chunks.data)} fragmentos en total")
        
        # 3. Identificar fragmentos huérfanos
        orphaned_chunks = []
        file_id_to_chunks = {}
        file_id_not_found = set()
        
        for chunk in response_chunks.data:
            metadata = chunk.get('metadata', '{}')
            # Convertir metadata a diccionario si es string
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            file_id = metadata.get('file_id')
            if not file_id:
                logger.warning(f"Fragmento {chunk['id']} sin file_id en metadata")
                continue
                
            # Agrupar chunks por file_id para estadísticas
            if file_id not in file_id_to_chunks:
                file_id_to_chunks[file_id] = []
            file_id_to_chunks[file_id].append(chunk['id'])
            
            # Verificar si el archivo existe en la tabla 'files'
            if file_id not in existing_file_ids:
                orphaned_chunks.append({
                    'id': chunk['id'],
                    'file_id': file_id
                })
                file_id_not_found.add(file_id)
        
        # Mostrar estadísticas de archivos huérfanos
        if file_id_not_found:
            logger.info(f"Se encontraron {len(file_id_not_found)} file_ids que no existen en la tabla 'files':")
            for i, file_id in enumerate(file_id_not_found):
                chunk_count = len(file_id_to_chunks.get(file_id, []))
                logger.info(f"  {i+1}. file_id: {file_id} - {chunk_count} fragmentos")
        
        if orphaned_chunks:
            logger.info(f"Se encontraron {len(orphaned_chunks)} fragmentos huérfanos en total")
            
            if not dry_run:
                # 4. Eliminar los fragmentos huérfanos
                logger.info("Iniciando eliminación de fragmentos huérfanos...")
                
                # Eliminar en lotes para evitar problemas con consultas muy grandes
                batch_size = 50
                deleted_count = 0
                
                for i in range(0, len(orphaned_chunks), batch_size):
                    batch = orphaned_chunks[i:i+batch_size]
                    batch_ids = [chunk['id'] for chunk in batch]
                    
                    try:
                        # Eliminar fragmentos del lote
                        for chunk_id in batch_ids:
                            supabase.table(collection_name).delete().eq("id", chunk_id).execute()
                            deleted_count += 1
                        
                        logger.info(f"Eliminados {deleted_count}/{len(orphaned_chunks)} fragmentos ({i+1}-{min(i+len(batch), len(orphaned_chunks))})")
                    except Exception as e:
                        logger.error(f"Error al eliminar lote {i//batch_size + 1}: {str(e)}")
                
                logger.info(f"Eliminación completada. Total eliminados: {deleted_count} de {len(orphaned_chunks)}")
                
                return {
                    "status": "completed", 
                    "orphaned_chunks": len(orphaned_chunks),
                    "deleted": deleted_count,
                    "orphaned_file_ids": len(file_id_not_found)
                }
            else:
                logger.info("MODO SIMULACIÓN: No se eliminaron fragmentos (dry_run=True)")
                return {
                    "status": "simulation", 
                    "orphaned_chunks": len(orphaned_chunks),
                    "deleted": 0,
                    "orphaned_file_ids": len(file_id_not_found)
                }
        else:
            logger.info("No se encontraron fragmentos huérfanos")
            return {"status": "completed", "orphaned_chunks": 0, "deleted": 0}
    
    except Exception as e:
        logger.error(f"Error durante la identificación de fragmentos huérfanos: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Identifica y elimina fragmentos huérfanos en la base de datos")
    parser.add_argument("--delete", action="store_true", help="Eliminar los fragmentos huérfanos (por defecto solo identifica)")
    
    args = parser.parse_args()
    
    # Por defecto, dry_run=True (solo identificar sin eliminar)
    dry_run = not args.delete
    
    print(f"{'MODO SIMULACIÓN' if dry_run else 'MODO ELIMINACIÓN'}: {'Identificando' if dry_run else 'Eliminando'} fragmentos huérfanos...")
    
    # Ejecutar la identificación/eliminación
    start_time = datetime.now()
    result = identify_orphaned_chunks(dry_run=dry_run)
    end_time = datetime.now()
    
    # Mostrar resultado
    if result["status"] == "error":
        print(f"\n❌ Error: {result.get('error', 'Error desconocido')}")
    else:
        print("\n✅ Proceso completado con éxito.")
        print(f"\nEstadísticas:")
        print(f"  - Fragmentos huérfanos encontrados: {result['orphaned_chunks']}")
        if not dry_run:
            print(f"  - Fragmentos eliminados: {result['deleted']}")
        print(f"  - IDs de archivos huérfanos: {result.get('orphaned_file_ids', 0)}")
        print(f"  - Tiempo total: {(end_time - start_time).total_seconds():.2f} segundos")
    
    if dry_run and result["orphaned_chunks"] > 0:
        print("\nPara eliminar estos fragmentos, ejecuta el script con el parámetro --delete:")
        print("python temp_lec/cleanup_orphans.py --delete") 