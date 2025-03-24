#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para probar la consulta de documentos en la base de datos.
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv

from app.database.vector_store import VectorDatabase
from app.database.supabase_client import get_supabase_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def list_documents():
    """Lista los documentos almacenados en la base de datos."""
    try:
        # Inicializar VectorDatabase
        db = VectorDatabase()
        
        # Consultar documentos
        response = db.supabase.table("documents").select("id,content,metadata").limit(10).execute()
        docs = response.data
        
        print(f"Se encontraron {len(docs)} documentos:")
        for i, doc in enumerate(docs[:5], 1):  # Mostrar solo los primeros 5
            doc_id = doc.get('id', 'sin_id')
            content = doc.get('content', 'sin_contenido')[:50] + '...' if doc.get('content') else 'sin_contenido'
            metadata = doc.get('metadata', {})
            
            file_id = metadata.get('id') if metadata else 'desconocido'
            file_name = metadata.get('name') if metadata else 'desconocido'
            chunk_index = metadata.get('chunk_index') if metadata else 'desconocido'
            total_chunks = metadata.get('total_chunks') if metadata else 'desconocido'
            
            print(f"Documento {i}:")
            print(f"  ID: {doc_id}")
            print(f"  Contenido: {content}")
            print(f"  Archivo: {file_name} (ID: {file_id})")
            print(f"  Fragmento: {chunk_index} de {total_chunks}")
            print("---")
        
        # Consultar documentos por file_id específico
        file_id = '1UVkoJj_YlwZzQIjFXP47yzu0U95Cmbhy'  # ID del archivo PDF
        print(f"\nBuscando documentos con file_id: {file_id}")
        
        chunks = db.get_chunks_by_file_id(file_id)
        print(f"Se encontraron {len(chunks)} fragmentos para este archivo.")
        
        for i, chunk in enumerate(chunks[:3], 1):  # Mostrar solo los primeros 3
            chunk_id = chunk.get('id', 'sin_id')
            content = chunk.get('content', 'sin_contenido')[:50] + '...' if chunk.get('content') else 'sin_contenido'
            metadata = chunk.get('metadata', {})
            chunk_index = metadata.get('chunk_index') if metadata else 'desconocido'
            
            print(f"Fragmento {i}:")
            print(f"  ID: {chunk_id}")
            print(f"  Índice: {chunk_index}")
            print(f"  Contenido: {content}")
            print("---")
        
    except Exception as e:
        logger.error(f"Error al listar documentos: {e}")
        return False

def verify_file_id(file_id):
    """Verifica si existe un documento con el file_id especificado."""
    try:
        # Inicializar VectorDatabase
        db = VectorDatabase()
        
        # Consultar documentos con ese file_id
        chunks = db.get_chunks_by_file_id(file_id)
        
        if chunks:
            print(f"Se encontraron {len(chunks)} fragmentos para el archivo con ID: {file_id}")
            return True
        else:
            print(f"No se encontraron fragmentos para el archivo con ID: {file_id}")
            return False
    except Exception as e:
        logger.error(f"Error al verificar file_id: {e}")
        return False

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Listar documentos
    list_documents()
    
    # Si se especificó un file_id como argumento, verificarlo
    if len(sys.argv) > 1:
        file_id = sys.argv[1]
        print(f"\nVerificando file_id proporcionado: {file_id}")
        verify_file_id(file_id) 