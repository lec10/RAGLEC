from http.server import BaseHTTPRequestHandler
import json
import os
import traceback
import time
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

# Configurar logging para reducir mensajes innecesarios
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)  # Solo mostrar advertencias y errores
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno una sola vez para todas las solicitudes
load_dotenv()

# Cliente global de OpenAI - para evitar inicializarlo en cada solicitud
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    OPENAI_CLIENT = OpenAI(api_key=openai_api_key)
else:
    OPENAI_CLIENT = None

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configuración global
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
DEFAULT_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
MAX_RESPONSE_TIME = 15.0  # Tiempo máximo de respuesta

# Función para formatear las fuentes de manera segura
def formatSources(sources):
    formatted_sources = []
    
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            logger.error(f"Fuente no es un diccionario: {type(source)}")
            continue
            
        formatted_sources.append({
            'content': source.get('content', 'Contenido no disponible'),
            'file_name': source.get('file_name', 'Desconocido'),
            'file_id': source.get('file_id', ''),
            'chunk_index': source.get('chunk_index', 0),
            'total_chunks': source.get('total_chunks', 0),
            'similarity': source.get('similarity', 0)
        })
    
    return formatted_sources

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_POST(self):
        # Configurar CORS y respuesta
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        start_time = time.time()
        logger.info(f"=== INICIO DE SOLICITUD === {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Obtener el cuerpo de la solicitud
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            logger.info(f"Datos recibidos - tamaño: {len(post_data)} bytes: {time.time() - start_time:.3f}s")
            
            # Obtener la consulta
            query = data.get('query', '')
            logger.info(f"Consulta recibida: '{query[:50]}...' (tiempo: {time.time() - start_time:.3f}s)")
            
            if not query:
                response = {'error': 'La consulta está vacía'}
                self.wfile.write(json.dumps(response).encode())
                logger.info(f"Consulta vacía - terminando: {time.time() - start_time:.3f}s")
                return
            
            # Verificar que todos los clientes estén disponibles
            if not OPENAI_CLIENT:
                response = {'error': 'API key de OpenAI no configurada'}
                self.wfile.write(json.dumps(response).encode())
                logger.error("API key de OpenAI no configurada")
                return
                
            if not SUPABASE_URL or not SUPABASE_KEY:
                response = {'error': 'Credenciales de Supabase no configuradas'}
                self.wfile.write(json.dumps(response).encode())
                logger.error("Credenciales de Supabase no configuradas")
                return
            
            # Procesar la consulta con el sistema RAG optimizado
            try:
                logger.info(f"Iniciando process_query: {time.time() - start_time:.3f}s")
                
                # Control de tiempo máximo para evitar timeout
                remaining_time = MAX_RESPONSE_TIME - (time.time() - start_time)
                logger.info(f"Tiempo restante para respuesta: {remaining_time:.3f}s")
                
                if remaining_time < 5.0:
                    # Si queda muy poco tiempo, enviamos una respuesta de error
                    response = {'error': 'Tiempo insuficiente para procesar la consulta'}
                    self.wfile.write(json.dumps(response).encode())
                    logger.warning(f"Tiempo insuficiente para procesar: {remaining_time:.3f}s")
                    return
                
                # Procesar la consulta con el tiempo restante como límite
                rag_result = process_query(query, timeout=remaining_time)
                
                process_time = time.time() - start_time
                logger.info(f"process_query completado en {process_time:.3f}s")
                
                # Verificar el tipo de rag_result
                if not isinstance(rag_result, dict):
                    logger.error(f"Tipo inesperado de rag_result: {type(rag_result)}")
                    response = {'error': f"Error interno: resultado inesperado"}
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                if "error" in rag_result:
                    logger.error(f"Error devuelto por process_query: {rag_result['error']}")
                    response = {'error': f"No se pudo procesar tu consulta: {rag_result['error']}"}
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                # Verificar que rag_result contiene respuesta y fuentes
                if "response" not in rag_result:
                    logger.error("rag_result no contiene campo 'response'")
                    response = {'error': "Error interno: formato de respuesta incorrecto"}
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                # Asegurar que sources sea una lista
                if "sources" not in rag_result or not isinstance(rag_result["sources"], list):
                    logger.warning("rag_result contiene sources en formato incorrecto, ajustando")
                    rag_result["sources"] = []
                
                # Normalizar las fuentes usando la función de formato segura
                rag_result["sources"] = formatSources(rag_result["sources"])
                
                logger.info(f"Respuesta generada ({len(rag_result['response'])} caracteres): {rag_result['response'][:100]}...")
                
                # Enviar respuesta
                logger.info(f"Enviando respuesta al cliente: {time.time() - start_time:.3f}s")
                self.wfile.write(json.dumps(rag_result).encode())
                logger.info(f"=== FIN DE SOLICITUD === Total: {time.time() - start_time:.3f}s")
            except Exception as e:
                logger.error(f"Error en process_query: {str(e)}")
                logger.error(traceback.format_exc())
                response = {'error': f"Error en process_query: {str(e)}"}
                self.wfile.write(json.dumps(response).encode())
                logger.info(f"=== ERROR EN SOLICITUD === Total: {time.time() - start_time:.3f}s")
            
        except Exception as e:
            # Obtener el traceback completo
            error_traceback = traceback.format_exc()
            logger.error(f"Error general: {str(e)}")
            logger.error(error_traceback)
            
            response = {
                'error': f"Error general: {str(e)}",
                'traceback': error_traceback
            }
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"=== ERROR GENERAL EN SOLICITUD === Total: {time.time() - start_time:.3f}s")

def get_embedding(text):
    """Genera un embedding para el texto dado usando la API de OpenAI."""
    start_time = time.time()
    logger.info("Iniciando generación de embedding...")
    
    text = text.replace("\n", " ")
    try:
        response = OPENAI_CLIENT.embeddings.create(
            input=[text],
            model=DEFAULT_EMBEDDING_MODEL
        )
        logger.info(f"Embedding generado correctamente en {time.time() - start_time:.3f}s")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error al generar embedding: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Error en generación de embedding: {str(e)}")

def process_query(query, similarity_threshold=0.1, num_results=5, timeout=MAX_RESPONSE_TIME):
    """Procesa una consulta usando la API de OpenAI y Supabase directamente."""
    start_time = time.time()
    query_steps = {}
    
    try:
        # Conexión a Supabase (una conexión por solicitud)
        logger.info(f"Conectando a Supabase: {SUPABASE_URL[:20]}...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        query_steps["init_supabase"] = time.time() - start_time
        
        # Generar embedding para la consulta
        logger.info("Generando embedding para la consulta...")
        embedding_start = time.time()
        try:
            query_embedding = get_embedding(query)
            logger.info(f"Embedding generado: {len(query_embedding)} dimensiones")
            query_steps["embedding"] = time.time() - embedding_start
        except Exception as e:
            logger.error(f"Error al generar embedding: {str(e)}")
            return {"error": f"Error al generar embedding: {str(e)}"}
        
        # Control de tiempo restante
        time_used = time.time() - start_time
        time_remaining = timeout - time_used
        logger.info(f"Tiempo usado: {time_used:.3f}s, restante: {time_remaining:.3f}s")
        
        if time_remaining < 5.0:
            return {"error": "Tiempo insuficiente para completar la consulta"}
        
        # Buscar documentos relevantes en Supabase
        logger.info("Buscando documentos relevantes...")
        search_start = time.time()
        try:
            result = supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': num_results
                }
            ).execute()
            query_steps["search_docs"] = time.time() - search_start
        except Exception as e:
            logger.error(f"Error en búsqueda de Supabase: {str(e)}")
            return {"error": f"Error en búsqueda de documentos: {str(e)}"}
        
        # Actualizar tiempo restante
        time_used = time.time() - start_time
        time_remaining = timeout - time_used
        logger.info(f"Tiempo usado: {time_used:.3f}s, restante: {time_remaining:.3f}s")
        
        if time_remaining < 3.0:
            return {"error": "Tiempo insuficiente después de la búsqueda"}
        
        # Preparar documentos
        logger.info("Procesando resultados de la búsqueda...")
        documents = []
        if result.data:
            logger.info(f"Se encontraron {len(result.data)} documentos relevantes")
            for doc in result.data:
                # Verificar que doc sea un diccionario
                if not isinstance(doc, dict):
                    logger.error(f"Documento no es un diccionario: {type(doc)}")
                    continue
                    
                # Verificar que metadata existe y es un diccionario
                metadata = doc.get('metadata', {})
                if not isinstance(metadata, dict):
                    metadata = {}  # Si no es un diccionario, usar uno vacío
                    logger.warning(f"Metadata no es un diccionario: {type(metadata)}")
                    
                documents.append({
                    'content': doc.get('content', 'Contenido no disponible'),
                    'file_name': metadata.get('name', 'Desconocido'),
                    'file_id': metadata.get('file_id', ''),
                    'chunk_index': metadata.get('chunk_index', 0),
                    'total_chunks': metadata.get('total_chunks', 0),
                    'similarity': doc.get('similarity', 0)
                })
        
        # No se encontraron documentos relevantes
        if not documents:
            logger.warning("No se encontraron documentos relevantes para la consulta")
            query_steps["total"] = time.time() - start_time
            return {
                "response": "No se encontraron documentos relevantes para tu consulta. Por favor, intenta reformular tu pregunta o ajusta el umbral de similitud.",
                "sources": [],
                "metadata": {
                    "query": query,
                    "processing_time": time.time() - start_time,
                    "similarity_threshold": similarity_threshold,
                    "num_results": num_results,
                    "query_steps": query_steps
                }
            }
        
        # Construir el contexto
        logger.info("Construyendo contexto para el prompt...")
        context_start = time.time()
        context = ""
        for i, doc in enumerate(documents):
            context += f"\nDocumento {i+1} (Fragmento {doc['chunk_index']+1} de {doc['total_chunks']}):\n{doc['content']}\n"
        query_steps["context_building"] = time.time() - context_start
        
        # Actualizar tiempo restante
        time_used = time.time() - start_time
        time_remaining = timeout - time_used
        logger.info(f"Tiempo usado: {time_used:.3f}s, restante: {time_remaining:.3f}s")
        
        if time_remaining < 3.0:
            return {"error": "Tiempo insuficiente después de construir el contexto"}
        
        # Llamar directamente a la API de OpenAI
        logger.info("Llamando a la API de OpenAI...")
        logger.info(f"Usando modelo: {DEFAULT_MODEL}")
        
        # Crear el prompt
        system_message = "Eres un asistente especializado en responder consultas basándote exclusivamente en la información proporcionada."
        user_message = f"""
        Responde a la siguiente pregunta basándote únicamente en la información proporcionada en los documentos.
        
        Contexto:
        {context}
        
        Pregunta: {query}
        
        Si la información no es suficiente para responder la pregunta completamente, indica qué parte de la información falta.
        Cita las fuentes en tu respuesta como (Documento #, Fragmento # de #).
        """
        
        # Adaptamos los tokens según el tiempo restante
        max_tokens = 1000
        if time_remaining < 10.0:
            max_tokens = 500  # Reducir tokens si queda poco tiempo
        
        # Llamar a la API con timeout adaptado al tiempo restante
        openai_start = time.time()
        try:
            # Usamos un timeout reducido - nunca mayor que el tiempo restante menos un margen
            openai_timeout = min(time_remaining - 1.0, 15.0)
            
            completion = OPENAI_CLIENT.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                timeout=openai_timeout
            )
            
            response_text = completion.choices[0].message.content
            query_steps["openai_call"] = time.time() - openai_start
            
            logger.info(f"Hora fin de llamada a OpenAI: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Tiempo total de llamada a OpenAI: {time.time() - openai_start:.2f}s")
            logger.info("Respuesta generada correctamente")
            logger.info(f"Longitud de la respuesta: {len(response_text)}")
        
        except Exception as e:
            logger.error(f"Error en llamada a OpenAI: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Manejar específicamente errores de timeout
            error_str = str(e).lower()
            if "timeout" in error_str:
                return {
                    "response": "Lo siento, la respuesta está tomando demasiado tiempo. Por favor, intenta una pregunta más específica o más corta.",
                    "sources": documents,
                    "metadata": {
                        "error": "timeout",
                        "query": query,
                        "processing_time": time.time() - start_time,
                        "similarity_threshold": similarity_threshold,
                        "num_results": num_results,
                        "query_steps": query_steps
                    }
                }
            
            return {"error": f"Error al generar respuesta con OpenAI: {str(e)}"}
        
        # Preparar resultado
        processing_time = time.time() - start_time
        logger.info(f"Proceso completo en {processing_time:.2f} segundos")
        query_steps["total"] = processing_time
        
        # Log detallado de tiempos por etapa
        for step, duration in query_steps.items():
            logger.info(f"  - Tiempo {step}: {duration:.3f}s")
        
        result = {
            "response": response_text,
            "sources": documents,
            "metadata": {
                "query": query,
                "processing_time": processing_time,
                "similarity_threshold": similarity_threshold,
                "num_results": num_results,
                "query_steps": query_steps
            }
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error en process_query: {e}")
        logger.error(traceback.format_exc())
        query_steps["error_time"] = time.time() - start_time
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "metadata": {
                "query_steps": query_steps
            }
        }

