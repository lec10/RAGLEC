"""
Configuración de la aplicación RAG.
Este módulo carga las variables de entorno necesarias para la aplicación.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde el archivo .env
dotenv_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path)

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_COLLECTION_NAME = os.getenv("SUPABASE_COLLECTION_NAME", "documents")

# Configuración de Google Drive
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Configuración de procesamiento de documentos
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 400 