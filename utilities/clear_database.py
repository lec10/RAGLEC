#!/usr/bin/env python
"""
Script para limpiar todas las tablas de la base de datos Supabase utilizada por RAGLEC.
Este script borrará todos los datos de las tablas documents, files y queries.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Añadir la ruta del proyecto al path para poder importar los módulos de la aplicación
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar módulos necesarios después de añadir la ruta
from app.database.supabase_client import get_supabase_client

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backup(supabase, table_name, output_dir="backups"):
    """Crea un backup de los datos de una tabla antes de borrarlos."""
    try:
        # Crear directorio de backups si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Obtener datos de la tabla
        result = supabase.table(table_name).select("*").execute()
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{table_name}_{timestamp}.json"
        
        # Guardar datos en archivo JSON
        with open(filename, 'w') as f:
            import json
            json.dump(result.data, f, indent=2)
        
        logger.info(f"Backup de la tabla {table_name} creado en {filename}")
        return True
    except Exception as e:
        logger.error(f"Error al crear backup de la tabla {table_name}: {e}")
        return False

def clear_table(supabase, table_name, create_backup_first=True, backup_dir="backups"):
    """Limpia todos los datos de una tabla."""
    try:
        # Crear backup si se solicita
        if create_backup_first:
            backup_created = create_backup(supabase, table_name, backup_dir)
            if not backup_created and not confirm_action(f"No se pudo crear backup de {table_name}. ¿Desea continuar con la eliminación?"):
                return False
        
        # Eliminar todos los registros - método diferente según la tabla
        if table_name == "queries":
            # La tabla queries usa ID numérico, necesita una condición WHERE
            logger.info(f"Usando método alternativo para tabla {table_name} con ID numérico")
            # Usar una condición que siempre sea verdadera para una columna numérica
            result = supabase.table(table_name).delete().gte("id", 0).execute()
        else:
            # Para tablas con ID tipo texto
            result = supabase.table(table_name).delete().neq("id", "placeholder_to_delete_all").execute()
        
        # Verificar resultado
        logger.info(f"Tabla {table_name} limpiada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al limpiar la tabla {table_name}: {e}")
        return False

def confirm_action(message):
    """Solicita confirmación al usuario para una acción."""
    response = input(f"{message} (y/n): ").lower().strip()
    return response in ['y', 'yes', 's', 'si', 'sí']

def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description='Limpia las tablas de la base de datos Supabase de RAGLEC.')
    parser.add_argument('--no-backup', action='store_true', help='No crear backups antes de borrar datos')
    parser.add_argument('--no-confirm', action='store_true', help='No solicitar confirmación antes de borrar datos')
    parser.add_argument('--backup-dir', default='backups', help='Directorio donde guardar los backups')
    parser.add_argument('--tables', nargs='+', default=['documents', 'files', 'queries'], 
                        help='Tablas específicas a limpiar (por defecto: documents, files, queries)')
    
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
    
    # Confirmar la operación si no se especificó --no-confirm
    if not args.no_confirm:
        tables_str = ", ".join(args.tables)
        if not confirm_action(f"¿Está seguro que desea borrar TODOS los datos de las tablas: {tables_str}? Esta acción NO se puede deshacer."):
            logger.info("Operación cancelada por el usuario")
            return 0
    
    # Procesar cada tabla
    success = True
    for table_name in args.tables:
        logger.info(f"Procesando tabla: {table_name}")
        if not clear_table(supabase, table_name, not args.no_backup, args.backup_dir):
            success = False
    
    if success:
        logger.info("Todas las tablas han sido limpiadas correctamente")
    else:
        logger.warning("No se pudieron limpiar todas las tablas. Revise los mensajes de error.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 