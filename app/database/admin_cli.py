"""
Interfaz de línea de comandos para administrar la base de datos vectorial.
Este módulo proporciona comandos para gestionar la base de datos vectorial en Supabase.
"""

import argparse
import logging
import sys
import os
import json
from tabulate import tabulate
from pathlib import Path
from datetime import datetime

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.vector_store import VectorDatabase
from app.database.setup_scripts.setup_database import setup_database, check_database
from app.config.settings import SUPABASE_URL, SUPABASE_KEY

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def list_files(args):
    """Lista los archivos en la base de datos.
    
    Args:
        args: Argumentos de la línea de comandos.
    """
    try:
        db = VectorDatabase()
        response = db.supabase.table("files").select("*").execute()
        files = response.data
        
        if not files:
            print("No hay archivos en la base de datos.")
            return
        
        # Formatear la salida en una tabla
        table_data = []
        for file in files:
            # Convertir la marca de tiempo a un formato legible
            processed_at = file.get("processed_at", "")
            if processed_at:
                try:
                    dt = datetime.fromisoformat(processed_at.replace("Z", "+00:00"))
                    processed_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            
            # Añadir fila a la tabla
            table_data.append([
                file.get("id", ""),
                file.get("name", ""),
                file.get("mime_type", ""),
                file.get("status", ""),
                processed_at
            ])
        
        # Imprimir la tabla
        headers = ["ID", "Nombre", "Tipo MIME", "Estado", "Procesado en"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print(f"\nTotal: {len(files)} archivos")
    except Exception as e:
        logger.error(f"Error al listar archivos: {e}")
        print(f"Error: {e}")

def show_file_details(args):
    """Muestra los detalles de un archivo.
    
    Args:
        args: Argumentos de la línea de comandos.
    """
    try:
        db = VectorDatabase()
        
        # Obtener el archivo
        response = db.supabase.table("files").select("*").eq("id", args.file_id).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"Archivo con ID {args.file_id} no encontrado.")
            return
        
        file = response.data[0]
        
        # Obtener los fragmentos del archivo
        chunks = db.get_chunks_by_file_id(args.file_id)
        
        # Imprimir detalles del archivo
        print(f"=== Detalles del archivo ===")
        print(f"ID: {file.get('id', '')}")
        print(f"Nombre: {file.get('name', '')}")
        print(f"Tipo MIME: {file.get('mime_type', '')}")
        print(f"Fuente: {file.get('source', '')}")
        print(f"Estado: {file.get('status', '')}")
        print(f"Procesado en: {file.get('processed_at', '')}")
        
        # Imprimir metadatos si están disponibles
        if file.get("metadata"):
            try:
                metadata = json.loads(file.get("metadata"))
                print("\nMetadatos:")
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
            except Exception:
                print(f"\nMetadatos: {file.get('metadata')}")
        
        # Imprimir información sobre los fragmentos
        print(f"\nFragmentos: {len(chunks)}")
        
        if args.show_chunks and chunks:
            print("\n=== Fragmentos ===")
            for i, chunk in enumerate(chunks, 1):
                print(f"\nFragmento {i}:")
                print(f"  ID: {chunk.get('id', '')}")
                print(f"  Índice: {chunk.get('metadata', {}).get('chunk_index', '')}")
                
                # Mostrar el contenido si se solicita
                if args.show_content:
                    print("\n  Contenido:")
                    content = chunk.get("content", "").strip()
                    # Limitar la longitud si es muy largo
                    if len(content) > 500 and not args.show_full_content:
                        content = content[:500] + "... (truncado)"
                    print(f"  {content}")
                    print()
    except Exception as e:
        logger.error(f"Error al mostrar detalles del archivo: {e}")
        print(f"Error: {e}")

def delete_file(args):
    """Elimina un archivo de la base de datos.
    
    Args:
        args: Argumentos de la línea de comandos.
    """
    try:
        db = VectorDatabase()
        
        # Verificar que el archivo existe
        response = db.supabase.table("files").select("*").eq("id", args.file_id).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"Archivo con ID {args.file_id} no encontrado.")
            return
        
        file = response.data[0]
        
        # Confirmar eliminación
        if not args.force:
            confirm = input(f"¿Estás seguro de que deseas eliminar el archivo '{file.get('name', args.file_id)}'? (s/N): ")
            if confirm.lower() != "s":
                print("Operación cancelada.")
                return
        
        # Eliminar el archivo y sus fragmentos
        deleted_count = db.delete_chunks_by_file_id(args.file_id)
        
        print(f"Se eliminaron {deleted_count} fragmentos del archivo '{file.get('name', args.file_id)}'.")
    except Exception as e:
        logger.error(f"Error al eliminar el archivo: {e}")
        print(f"Error: {e}")

def list_queries(args):
    """Lista las consultas realizadas.
    
    Args:
        args: Argumentos de la línea de comandos.
    """
    try:
        db = VectorDatabase()
        
        # Obtener las consultas
        response = db.supabase.table("queries").select("*").order("created_at", options={"ascending": False}).limit(args.limit).execute()
        queries = response.data
        
        if not queries:
            print("No hay consultas registradas.")
            return
        
        # Formatear la salida en una tabla
        table_data = []
        for query in queries:
            # Convertir la marca de tiempo a un formato legible
            created_at = query.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            
            # Truncar respuesta si es muy larga
            response_text = query.get("response", "")
            if len(response_text) > 50:
                response_text = response_text[:50] + "..."
            
            # Añadir fila a la tabla
            table_data.append([
                query.get("id", ""),
                query.get("query", ""),
                response_text,
                created_at
            ])
        
        # Imprimir la tabla
        headers = ["ID", "Consulta", "Respuesta", "Fecha"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print(f"\nTotal: {len(queries)} consultas")
    except Exception as e:
        logger.error(f"Error al listar consultas: {e}")
        print(f"Error: {e}")

def run_setup(args):
    """Ejecuta el script de configuración de la base de datos.
    
    Args:
        args: Argumentos de la línea de comandos.
    """
    if args.check:
        print("Verificando la configuración de la base de datos...")
        success = check_database()
        if success:
            print("La base de datos está configurada correctamente.")
        else:
            print("La base de datos no está configurada correctamente.")
            sys.exit(1)
    else:
        print("Configurando la base de datos...")
        success = setup_database()
        if success:
            print("La base de datos se ha configurado correctamente.")
        else:
            print("Error al configurar la base de datos.")
            sys.exit(1)

def export_data(args):
    """Exporta datos de la base de datos.
    
    Args:
        args: Argumentos de la línea de comandos.
    """
    try:
        db = VectorDatabase()
        data = {}
        
        # Exportar archivos
        if args.files:
            response = db.supabase.table("files").select("*").execute()
            data["files"] = response.data
        
        # Exportar consultas
        if args.queries:
            response = db.supabase.table("queries").select("*").execute()
            data["queries"] = response.data
        
        # Exportar documentos (fragmentos)
        if args.documents:
            # Advertencia: esto puede ser una operación costosa si hay muchos documentos
            response = db.supabase.table(db.collection_name).select("*").execute()
            data["documents"] = response.data
        
        # Guardar datos en un archivo
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"Datos exportados a {args.output}.")
        
        # Imprimir estadísticas
        stats = {
            "files": len(data.get("files", [])),
            "queries": len(data.get("queries", [])),
            "documents": len(data.get("documents", []))
        }
        
        print("\nEstadísticas:")
        for key, value in stats.items():
            if key in data:
                print(f"  {key}: {value}")
    except Exception as e:
        logger.error(f"Error al exportar datos: {e}")
        print(f"Error: {e}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Administrador de la base de datos vectorial")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando para listar archivos
    list_parser = subparsers.add_parser("list", help="Lista los archivos en la base de datos")
    
    # Comando para mostrar detalles de un archivo
    show_parser = subparsers.add_parser("show", help="Muestra los detalles de un archivo")
    show_parser.add_argument("file_id", help="ID del archivo a mostrar")
    show_parser.add_argument("--chunks", dest="show_chunks", action="store_true", help="Muestra información de los fragmentos")
    show_parser.add_argument("--content", dest="show_content", action="store_true", help="Muestra el contenido de los fragmentos")
    show_parser.add_argument("--full", dest="show_full_content", action="store_true", help="Muestra el contenido completo de los fragmentos")
    
    # Comando para eliminar un archivo
    delete_parser = subparsers.add_parser("delete", help="Elimina un archivo de la base de datos")
    delete_parser.add_argument("file_id", help="ID del archivo a eliminar")
    delete_parser.add_argument("-f", "--force", action="store_true", help="No pedir confirmación")
    
    # Comando para listar consultas
    queries_parser = subparsers.add_parser("queries", help="Lista las consultas realizadas")
    queries_parser.add_argument("--limit", type=int, default=20, help="Número máximo de consultas a mostrar")
    
    # Comando para ejecutar el script de configuración
    setup_parser = subparsers.add_parser("setup", help="Ejecuta el script de configuración de la base de datos")
    setup_parser.add_argument("--check", action="store_true", help="Verifica la configuración de la base de datos")
    
    # Comando para exportar datos
    export_parser = subparsers.add_parser("export", help="Exporta datos de la base de datos")
    export_parser.add_argument("--files", action="store_true", help="Exportar información de archivos")
    export_parser.add_argument("--queries", action="store_true", help="Exportar consultas")
    export_parser.add_argument("--documents", action="store_true", help="Exportar documentos (fragmentos)")
    export_parser.add_argument("-o", "--output", default="export.json", help="Archivo de salida")
    
    args = parser.parse_args()
    
    # Verificar que las credenciales estén configuradas
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Las credenciales de Supabase no están configuradas.")
        print("Por favor, configure las variables de entorno SUPABASE_URL y SUPABASE_KEY.")
        sys.exit(1)
    
    # Ejecutar el comando correspondiente
    if args.command == "list":
        list_files(args)
    elif args.command == "show":
        show_file_details(args)
    elif args.command == "delete":
        delete_file(args)
    elif args.command == "queries":
        list_queries(args)
    elif args.command == "setup":
        run_setup(args)
    elif args.command == "export":
        export_data(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 