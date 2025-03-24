"""
Script principal para ejecutar la aplicación RAG.
Este script inicia el gestor de documentos y la interfaz de chat.
"""

import logging
import argparse
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.document_manager import DocumentManager
from app.query.chat_interface import CommandLineChatInterface
from app.config.settings import OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, GOOGLE_APPLICATION_CREDENTIALS
from app.database.admin_cli import main as admin_main

# Configurar logging de manera más robusta
# Primero eliminar cualquier handler existente
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configurar formato
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Configurar handler para archivo
file_handler = logging.FileHandler("rag_app.log", mode='a')
file_handler.setFormatter(log_format)

# Configurar handler para consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)

# Configurar logger raíz
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Obtener logger específico
logger = logging.getLogger(__name__)
logger.info("=== INICIO DE SESIÓN ===")
logger.info("Logger configurado para escribir en: {}".format(os.path.abspath("rag_app.log")))

def check_environment():
    """Verifica que las variables de entorno necesarias estén configuradas."""
    missing_vars = []
    
    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    
    if not SUPABASE_URL:
        missing_vars.append("SUPABASE_URL")
    
    if not SUPABASE_KEY:
        missing_vars.append("SUPABASE_KEY")
    
    if not GOOGLE_APPLICATION_CREDENTIALS:
        missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS")
    elif not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        logger.error(f"El archivo de credenciales de Google no existe: {GOOGLE_APPLICATION_CREDENTIALS}")
        missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS (archivo no encontrado)")
    
    if missing_vars:
        logger.error(f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")
        logger.error("Por favor, configura estas variables en el archivo .env")
        return False
    
    return True

def process_all_documents():
    """Procesa todos los documentos en la carpeta monitoreada."""
    logger.info("Iniciando procesamiento de todos los documentos...")
    
    document_manager = DocumentManager()
    document_manager.process_all_files()
    
    logger.info("Procesamiento de documentos completado")

def start_monitoring():
    """Inicia el monitoreo de la carpeta de Google Drive."""
    logger.info("Iniciando monitoreo de la carpeta de Google Drive...")
    
    document_manager = DocumentManager()
    document_manager.start()
    
    logger.info("Monitoreo iniciado. Presiona Ctrl+C para detener.")
    
    try:
        # Mantener el proceso en ejecución
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Deteniendo el monitoreo...")
        document_manager.stop()
        logger.info("Monitoreo detenido")

def start_chat():
    """Inicia la interfaz de chat."""
    logger.info("Iniciando interfaz de chat...")
    
    chat_interface = CommandLineChatInterface()
    chat_interface.run()

def run_admin(args):
    """Ejecuta la herramienta de administración de la base de datos."""
    # Eliminar el comando "admin" de los argumentos
    sys.argv.pop(1)
    
    # Ejecutar la herramienta de administración
    admin_main()

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Aplicación RAG para consulta de documentos")
    
    # Definir los subcomandos
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Subcomando para procesar todos los documentos
    process_parser = subparsers.add_parser("process", help="Procesa todos los documentos en la carpeta monitoreada")
    
    # Subcomando para iniciar el monitoreo
    monitor_parser = subparsers.add_parser("monitor", help="Inicia el monitoreo de la carpeta de Google Drive")
    
    # Subcomando para iniciar la interfaz de chat
    chat_parser = subparsers.add_parser("chat", help="Inicia la interfaz de chat")
    
    # Subcomando para ejecutar la herramienta de administración
    admin_parser = subparsers.add_parser("admin", help="Ejecuta la herramienta de administración de la base de datos")
    
    # Parsear los argumentos
    args = parser.parse_args()
    
    # Ejecutar el comando correspondiente
    if args.command == "process":
        # Verificar las variables de entorno
        if not check_environment():
            return
        process_all_documents()
    elif args.command == "monitor":
        # Verificar las variables de entorno
        if not check_environment():
            return
        start_monitoring()
    elif args.command == "chat":
        # Verificar las variables de entorno
        if not check_environment():
            return
        start_chat()
    elif args.command == "admin":
        # No verificar todas las variables de entorno
        # Solo necesitamos las credenciales de Supabase para la administración
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("Faltan las credenciales de Supabase")
            logger.error("Por favor, configura las variables SUPABASE_URL y SUPABASE_KEY en el archivo .env")
            return
        run_admin(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 