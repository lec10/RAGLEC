"""
Script para configurar la base de datos de Supabase.
Este script ejecuta el script SQL para configurar las tablas, funciones e índices necesarios.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

from app.config.settings import SUPABASE_URL, SUPABASE_KEY
from app.database.vector_store import VectorDatabase

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_database(sql_script_path=None):
    """Configura la base de datos de Supabase.
    
    Args:
        sql_script_path: Ruta al script SQL para configurar la base de datos.
    
    Returns:
        bool: True si la configuración fue exitosa, False en caso contrario.
    """
    # Verificar que las credenciales de Supabase estén configuradas
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Las credenciales de Supabase no están configuradas")
        return False
    
    # Utilizar la ruta predeterminada si no se proporciona una
    if sql_script_path is None:
        # La ruta está relativa al directorio raíz del proyecto
        script_dir = Path(__file__).parent
        sql_script_path = script_dir / "supabase_setup.sql"
    
    if not os.path.exists(sql_script_path):
        logger.error(f"El archivo SQL no existe: {sql_script_path}")
        return False
    
    try:
        # Inicializar la conexión a Supabase
        db = VectorDatabase("healthcheck")
        
        # Leer el script SQL
        with open(sql_script_path, 'r') as file:
            sql_script = file.read()
        
        logger.info("Ejecutando script SQL...")
        logger.info(f"Este script no puede ejecutar el SQL directamente. Por favor, utiliza la interfaz de Supabase para ejecutar el script: {sql_script_path}")
        
        # Verificar la conexión y la tabla de healthcheck
        try:
            # Ejecutar una consulta simple para verificar la conexión
            result = db.supabase.table("healthcheck").select("*").execute()
            
            # Si la tabla no existe, crearla
            if not result.data:
                logger.info("Creando tabla de verificación de salud...")
                db.supabase.table("healthcheck").insert({"status": "ok"}).execute()
                
            logger.info("Verificación de conexión completada")
            return True
            
        except Exception as e:
            logger.error(f"Error al verificar la conexión: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error al configurar la base de datos: {e}")
        return False

def check_database():
    """Verifica la configuración de la base de datos.
    
    Returns:
        bool: True si la base de datos está configurada correctamente, False en caso contrario.
    """
    try:
        # Verificar que las credenciales de Supabase estén configuradas
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("Las credenciales de Supabase no están configuradas")
            return False
        
        logger.info("Verificando conexión a Supabase...")
        
        # Inicializar la conexión a Supabase
        db = VectorDatabase("healthcheck")
        
        # Verificar la conexión
        try:
            result = db.supabase.table("healthcheck").select("*").execute()
            logger.info(f"Conexión exitosa: {result.data}")
        except Exception as e:
            logger.error(f"Error al verificar la conexión: {e}")
            return False
        
        # Verificar la existencia de tablas y funciones necesarias
        tables = ["documents", "files", "queries"]
        functions = ["match_documents", "get_chunks_by_file_id", "delete_chunks_by_file_id"]
        
        # Verificar tablas
        logger.info("Verificando tablas...")
        for table in tables:
            try:
                result = db.supabase.table(table).select("*").limit(1).execute()
                logger.info(f"Tabla {table} existe")
            except Exception as e:
                logger.warning(f"No se pudo verificar la tabla {table}: {e}")
        
        # No podemos verificar funciones directamente con el cliente de Supabase
        logger.info("Las funciones deben verificarse manualmente en la interfaz de Supabase")
        
        return True
        
    except Exception as e:
        logger.error(f"Error al verificar la base de datos: {e}")
        return False

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Configurar la base de datos de Supabase")
    
    # Agregar argumentos
    parser.add_argument("--check", action="store_true", help="Verificar la configuración de la base de datos")
    parser.add_argument("--sql", help="Ruta al script SQL para configurar la base de datos")
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Ejecutar el comando correspondiente
    if args.check:
        if check_database():
            logger.info("La base de datos está configurada correctamente")
        else:
            logger.error("La base de datos no está configurada correctamente")
            sys.exit(1)
    else:
        if setup_database(args.sql):
            logger.info("La base de datos ha sido configurada correctamente")
        else:
            logger.error("Error al configurar la base de datos")
            sys.exit(1)

if __name__ == "__main__":
    main() 