from http.server import BaseHTTPRequestHandler
import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client
import traceback

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_GET(self):
        # Configurar CORS y respuesta
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        start_time = time.time()
        logger.info(f"=== INICIO DE DIAGNÓSTICO === {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        result = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "tiempo_inicio": start_time,
            "mensaje": "Diagnóstico del sistema RAGLEC"
        }
        
        try:
            # Cargar variables de entorno
            load_dotenv()
            result["load_dotenv"] = {
                "tiempo": time.time() - start_time
            }
            
            # Información del entorno
            openai_api_key = os.getenv("OPENAI_API_KEY")
            openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            result["env_info"] = {
                "openai_api_key": bool(openai_api_key),
                "openai_model": openai_model,
                "embedding_model": embedding_model,
                "supabase_url": bool(supabase_url),
                "supabase_key": bool(supabase_key)
            }
            
            # Test OpenAI
            try:
                if openai_api_key:
                    logger.info("Probando conexión con OpenAI...")
                    client = OpenAI(api_key=openai_api_key)
                    
                    # Test #1: Probar un modelo pequeño con un prompt corto
                    openai_start = time.time()
                    completion = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Eres un asistente útil."},
                            {"role": "user", "content": "Hola, responde brevemente."}
                        ],
                        max_tokens=20,
                        timeout=10.0
                    )
                    openai_time = time.time() - openai_start
                    
                    # Test #2: Generación de embedding
                    embedding_start = time.time()
                    embedding_response = client.embeddings.create(
                        input=["Prueba de generación de embedding para diagnóstico"],
                        model=embedding_model
                    )
                    embedding_time = time.time() - embedding_start
                    
                    result["openai_test"] = {
                        "funcionando": True,
                        "chat_completion": {
                            "respuesta": completion.choices[0].message.content,
                            "tiempo": openai_time,
                        },
                        "embedding": {
                            "dimensiones": len(embedding_response.data[0].embedding),
                            "tiempo": embedding_time
                        }
                    }
                else:
                    result["openai_test"] = {
                        "funcionando": False,
                        "error": "API key no configurada"
                    }
            except Exception as e:
                result["openai_test"] = {
                    "funcionando": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            
            # Test Supabase
            try:
                if supabase_url and supabase_key:
                    logger.info("Probando conexión con Supabase...")
                    supabase_start = time.time()
                    supabase = create_client(supabase_url, supabase_key)
                    
                    # Probar una consulta simple
                    response = supabase.table('documents').select('count', count='exact').limit(1).execute()
                    supabase_time = time.time() - supabase_start
                    
                    result["supabase_test"] = {
                        "funcionando": True,
                        "tiempo": supabase_time,
                        "documentos_count": response.count
                    }
                else:
                    result["supabase_test"] = {
                        "funcionando": False,
                        "error": "Credenciales de Supabase no configuradas"
                    }
            except Exception as e:
                result["supabase_test"] = {
                    "funcionando": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            
            # Test de función de búsqueda vectorial
            if result.get("openai_test", {}).get("funcionando", False) and result.get("supabase_test", {}).get("funcionando", False):
                try:
                    logger.info("Probando búsqueda vectorial...")
                    
                    # Generar embedding para una consulta de prueba
                    client = OpenAI(api_key=openai_api_key)
                    supabase = create_client(supabase_url, supabase_key)
                    query_text = "Prueba de búsqueda vectorial para diagnóstico"
                    
                    # Generar embedding
                    embedding_start = time.time()
                    embedding_response = client.embeddings.create(
                        input=[query_text],
                        model=embedding_model
                    )
                    query_embedding = embedding_response.data[0].embedding
                    embedding_time = time.time() - embedding_start
                    
                    # Realizar búsqueda vectorial
                    search_start = time.time()
                    search_result = supabase.rpc(
                        'match_documents',
                        {
                            'query_embedding': query_embedding,
                            'match_threshold': 0.1,
                            'match_count': 3
                        }
                    ).execute()
                    search_time = time.time() - search_start
                    
                    result["vector_search_test"] = {
                        "funcionando": True,
                        "embedding_tiempo": embedding_time,
                        "busqueda_tiempo": search_time,
                        "documentos_encontrados": len(search_result.data),
                        "tiempo_total": embedding_time + search_time
                    }
                except Exception as e:
                    result["vector_search_test"] = {
                        "funcionando": False,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
            
            # Tiempos totales
            result["tiempos"] = {
                "tiempo_total": time.time() - start_time,
                "timestamp_fin": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"=== FIN DE DIAGNÓSTICO === Total: {time.time() - start_time:.3f}s")
            
        except Exception as e:
            result["error_general"] = {
                "mensaje": str(e),
                "traceback": traceback.format_exc()
            }
            logger.error(f"Error en diagnóstico: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Devolver resultados
        self.wfile.write(json.dumps(result).encode()) 