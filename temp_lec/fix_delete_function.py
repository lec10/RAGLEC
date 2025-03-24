#!/usr/bin/env python
"""
Script para corregir la función delete_chunks_by_file_id en Supabase.
"""

import os
import sys
import logging

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.supabase_client import get_supabase_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def fix_delete_function():
    """Corrige la función delete_chunks_by_file_id en Supabase."""
    try:
        # Obtener cliente de Supabase
        supabase_store = get_supabase_client()
        supabase = supabase_store.get_client()
        
        logger.info("Conectado a Supabase. Aplicando corrección...")
        
        # Leer el script SQL
        script_path = os.path.join("app", "database", "setup_scripts", "supabase_fix.sql")
        with open(script_path, "r") as f:
            sql_script = f.read()
        
        # Ejecutar el script SQL
        response = supabase.rpc("exec_sql", {"query": sql_script})
        
        logger.info("Corrección aplicada correctamente")
        logger.info("Ahora puedes ejecutar 'python Main.py process' nuevamente para eliminar los archivos borrados")
        
        return True
    except Exception as e:
        logger.error(f"Error al aplicar la corrección: {e}")
        return False

if __name__ == "__main__":
    fix_delete_function() 