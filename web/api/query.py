from http.server import BaseHTTPRequestHandler
import json
import os
import traceback
import time
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from datetime import datetime
# El módulo re (regular expressions) proporciona soporte para expresiones regulares
# Se utiliza para buscar y manipular patrones de texto de forma avanzada
# Algunas funciones principales son:
#  - re.search(): Busca un patrón en cualquier parte del texto
#  - re.match(): Busca un patrón al inicio del texto
#  - re.findall(): Encuentra todas las ocurrencias de un patrón
#  - re.sub(): Sustituye patrones encontrados por otro texto
import re

# Configurar logging para reducir mensajes innecesarios
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)  # Solo mostrar advertencias y errores
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Archivo para logs detallados (solo en desarrollo)
LOG_DEBUG = os.getenv("LOG_DEBUG", "false").lower() == "true"
LOG_FILE = os.path.join(os.path.dirname(__file__), 'api_log.txt')

def log_to_file(message):
    """Función para registrar mensajes en un archivo de log si está habilitado el modo debug"""
    if not LOG_DEBUG:
        return
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()}: {message}\n")
    except Exception as e:
        logger.error(f"Error al escribir en log: {e}")

# Cargar variables de entorno una sola vez para todas las solicitudes
load_dotenv()

# Cliente global de OpenAI - para evitar inicializarlo en cada solicitud
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    try:
        OPENAI_CLIENT = OpenAI(api_key=openai_api_key)
        logger.info("Cliente OpenAI inicializado correctamente")
        log_to_file("Cliente OpenAI inicializado")
    except Exception as e:
        logger.error(f"Error al inicializar cliente OpenAI: {e}")
        OPENAI_CLIENT = None
else:
    logger.error("API key de OpenAI no encontrada en variables de entorno")
    OPENAI_CLIENT = None

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Credenciales de Supabase no encontradas en variables de entorno")
    log_to_file("Faltan credenciales de Supabase")

# Configuración global
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
MAX_RESPONSE_TIME = float(os.getenv("MAX_RESPONSE_TIME", "15.0"))  # Tiempo máximo de respuesta
logger.info(f"Modelo OpenAI: {DEFAULT_MODEL}, Modelo de embedding: {DEFAULT_EMBEDDING_MODEL}")

# Cache para evitar generar embeddings repetidos
EMBEDDING_CACHE = {}

# Función para formatear las fuentes de manera segura
def formatSources(sources):
    """Formatea las fuentes para asegurar que tengan un formato consistente"""
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

def register_query_in_database(query, response, sources):
    """Registra una consulta en la base de datos.
    
    Args:
        query: Texto de la consulta.
        response: Respuesta generada.
        sources: Fuentes utilizadas.
    
    Returns:
        int or None: ID de la consulta registrada, o None si hubo un error.
    """
    try:
        # Serializar sources como una cadena JSON para almacenarla en la BD
        sources_json = json.dumps(sources)
        
        # Datos para guardar en la tabla queries
        query_data = {
            "query": query,
            "response": response,
            "sources": sources_json,
            "created_at": datetime.now().isoformat()
        }
        
        # Insertar en la tabla
        supabase_conn = create_client(SUPABASE_URL, SUPABASE_KEY)
        insert_result = supabase_conn.table("queries").insert(query_data).execute()
        logger.info("Consulta registrada correctamente en la tabla 'queries'")
        
        # Obtener el ID de la consulta insertada
        if insert_result.data and len(insert_result.data) > 0:
            query_id = insert_result.data[0].get("id")
            logger.info(f"ID de la consulta: {query_id}")
            return query_id
        return None
    except Exception as e:
        logger.error(f"Error al registrar la consulta en la tabla 'queries': {str(e)}")
        return None

def get_embedding(text, use_cache=True):
    """Genera un embedding para el texto dado usando la API de OpenAI con caché opcional."""
    if not text:
        logger.error("Texto vacío para generar embedding")
        raise ValueError("No se puede generar embedding para texto vacío")
    
    start_time = time.time()
    
    # Usar caché si está habilitado
    if use_cache and text in EMBEDDING_CACHE:
        logger.info(f"Usando embedding en caché para: {text[:30]}...")
        return EMBEDDING_CACHE[text]
    
    logger.info("Iniciando generación de embedding...")
    
    text = text.replace("\n", " ")
    try:
        response = OPENAI_CLIENT.embeddings.create(
            input=[text],
            model=DEFAULT_EMBEDDING_MODEL
        )
        logger.info(f"Embedding generado correctamente en {time.time() - start_time:.3f}s")
        
        embedding = response.data[0].embedding
        
        # Guardar en caché si está habilitado
        if use_cache:
            EMBEDDING_CACHE[text] = embedding
            
        return embedding
    except Exception as e:
        logger.error(f"Error al generar embedding: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Error en generación de embedding: {str(e)}")

def process_query(query, similarity_threshold=0.1, num_results=5, timeout=MAX_RESPONSE_TIME, conversation_history=[]):
    """Procesa una consulta usando la API de OpenAI y Supabase directamente."""
    start_time = time.time()
    query_steps = {}
    
    try:
        # Inicializar clientes
        if not OPENAI_CLIENT:
            return {"error": "API key de OpenAI no configurada"}
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            return {"error": "Credenciales de Supabase no configuradas"}
            
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            init_time = time.time() - start_time
            query_steps["init"] = init_time
            logger.info(f"Clientes inicializados en {init_time:.3f}s")
        except Exception as e:
            logger.error(f"Error al inicializar Supabase: {str(e)}")
            return {"error": f"Error al conectar con Supabase: {str(e)}"}
        
        # 1. Generar embedding de la consulta
        logger.info("Generando embedding de la consulta...")
        embed_start = time.time()
        
        try:
            query_embedding = get_embedding(query)
            query_steps["embedding"] = time.time() - embed_start
            logger.info(f"Embedding generado en {query_steps['embedding']:.3f}s")
        except Exception as e:
            logger.error(f"Error al generar embedding: {str(e)}")
            return {"error": f"Error al generar embedding: {str(e)}"}
        
        # 2. Buscar documentos similares
        logger.info("Buscando documentos similares...")
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
                    try:
                        # Intentar deserializar si viene como string
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)
                        else:
                            metadata = {}  # Si no es un diccionario ni string, usar uno vacío
                    except Exception as e:
                        logger.warning(f"Error al deserializar metadata: {e}")
                        metadata = {}  # Si hay error al deserializar, usar uno vacío
                    
                    logger.warning(f"Metadata no es un diccionario: {type(metadata)}")
                
                # Log detallado del metadata para debugging
                logger.info(f"Metadata original: {json.dumps(metadata)}")
                
                # Asegurar que total_chunks siempre sea un número (1 por defecto si no existe)
                total_chunks = metadata.get('total_chunks')
                if total_chunks is None:
                    total_chunks = 1
                    logger.warning("total_chunks no encontrado en metadata, usando valor por defecto: 1")
                else:
                    # Intentar convertir a número si es string
                    try:
                        total_chunks = int(total_chunks)
                    except (ValueError, TypeError):
                        logger.warning(f"Error al convertir total_chunks: {total_chunks}, usando valor por defecto: 1")
                        total_chunks = 1
                        
                # Log de información de los campos principales        
                logger.info(f"Valores extraídos - file_name: '{metadata.get('name', 'Desconocido')}', " +
                          f"chunk_index: {metadata.get('chunk_index', 0)}, total_chunks: {total_chunks}")
                        
                documents.append({
                    'content': doc.get('content', 'Contenido no disponible'),
                    'file_name': metadata.get('name', 'Desconocido'),
                    'file_id': metadata.get('file_id', ''),
                    'chunk_index': metadata.get('chunk_index', 0),
                    'total_chunks': total_chunks,  # Usar el valor procesado
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
        
        # Formatear el historial de conversación para incluirlo en el prompt
        conversation_context = ""
        if conversation_history and isinstance(conversation_history, list) and len(conversation_history) > 0:
            logger.info(f"Formateando historial de conversación ({len(conversation_history)} mensajes)")
            for message in conversation_history:
                role = message.get('role', '')
                content = message.get('content', '')
                if role and content:
                    conversation_context += f"{role.capitalize()}: {content}\n\n"
            logger.info(f"Historial formateado: {len(conversation_context)} caracteres")
        
        # Crear el prompt con instrucciones estrictas
        system_message = """Eres un asistente restrictivo que SOLAMENTE puede responder usando la información de los documentos proporcionados.
NUNCA uses conocimiento general o información externa a los documentos.
DEBES citar la fuente exacta de cada pieza de información como (Documento #, Fragmento # de #).
Si los documentos NO contienen información relevante, debes responder: "No puedo responder esta pregunta con los documentos proporcionados"."""
        
        user_message = f"""
INSTRUCCIONES ESTRICTAS:
1. Responde ÚNICAMENTE usando la información presente en los documentos proporcionados.
2. NO utilices NINGÚN conocimiento que no esté en los documentos.
3. Cada afirmación DEBE terminar con su cita (Documento #, Fragmento # de #).
4. Si no encuentras información relevante en los documentos, responde: "No puedo responder esta pregunta con los documentos proporcionados".

{f"Conversación previa:\n{conversation_context}\n" if conversation_context else ""}

Documentos disponibles:
{context}

Pregunta actual: {query}

RECUERDA: Solo puedes usar información de los documentos proporcionados. Cita TODAS las fuentes.
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
                temperature=0.3,  # Reducir temperatura para respuestas más deterministas (antes era 0.7)
                max_tokens=max_tokens,
                timeout=openai_timeout
            )
            
            response_text = completion.choices[0].message.content
            query_steps["openai_call"] = time.time() - openai_start
            
            # Verificar que la respuesta incluya citas de documentos
            if documents and not re.search(r'\(Documento \d+', response_text):
                logger.warning("La respuesta no contiene citas a los documentos - agregando advertencia")
                response_text += "\n\nADVERTENCIA: Esta respuesta puede no estar basada en los documentos proporcionados. Por favor, solicita aclaración."
                
                # Opcional: Forzar una respuesta que indique que no se encontró información
                # response_text = "No puedo responder esta pregunta con información específica de los documentos proporcionados. Por favor, reformula tu pregunta o solicita información disponible en los documentos."
            
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
        
        # Ya no registramos la consulta aquí para evitar duplicados
        # La consulta ya se registra en el manejador HTTP (Handler.do_POST)
        
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

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_POST(self):
        # Configurar CORS y respuesta
        origin = self.headers.get('Origin', '*')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        start_time = time.time()
        logger.info(f"=== INICIO DE SOLICITUD === {time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_to_file(f"Inicio de petición POST a {self.path}")
        
        try:
            # Obtener el cuerpo de la solicitud
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                response = {'error': 'No se recibieron datos en la solicitud'}
                self.wfile.write(json.dumps(response).encode())
                logger.error("No se recibieron datos en la solicitud")
                log_to_file("Error: No se recibieron datos en la solicitud")
                return
                
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError as e:
                response = {'error': f'Error al decodificar JSON: {str(e)}'}
                self.wfile.write(json.dumps(response).encode())
                logger.error(f"Error al decodificar JSON: {str(e)}")
                log_to_file(f"Error: JSON inválido - {str(e)}")
                return
                
            logger.info(f"Datos recibidos - tamaño: {len(post_data)} bytes: {time.time() - start_time:.3f}s")
            log_to_file(f"Datos recibidos: {json.dumps(data)[:200]}...")
            
            # Obtener la consulta
            query = data.get('query', '')
            # Obtener el historial de conversación si existe
            conversation_history = data.get('conversation_history', [])
            logger.info(f"Consulta recibida: '{query[:50]}...' (tiempo: {time.time() - start_time:.3f}s)")
            logger.info(f"Historial de conversación recibido: {len(conversation_history)} mensajes")
            
            if not query:
                response = {'error': 'La consulta está vacía'}
                self.wfile.write(json.dumps(response).encode())
                logger.info(f"Consulta vacía - terminando: {time.time() - start_time:.3f}s")
                log_to_file("Error: consulta vacía")
                return
            
            # Verificar que todos los clientes estén disponibles
            if not OPENAI_CLIENT:
                response = {'error': 'API key de OpenAI no configurada'}
                self.wfile.write(json.dumps(response).encode())
                logger.error("API key de OpenAI no configurada")
                log_to_file("Error: API key de OpenAI no configurada")
                return
                
            if not SUPABASE_URL or not SUPABASE_KEY:
                response = {'error': 'Credenciales de Supabase no configuradas'}
                self.wfile.write(json.dumps(response).encode())
                logger.error("Credenciales de Supabase no configuradas")
                log_to_file("Error: Credenciales de Supabase no configuradas")
                return
            
            # Procesar la consulta con el sistema RAG optimizado
            try:
                logger.info(f"Iniciando process_query: {time.time() - start_time:.3f}s")
                log_to_file(f"Iniciando process_query con consulta: {query}")
                
                # Control de tiempo máximo para evitar timeout
                remaining_time = MAX_RESPONSE_TIME - (time.time() - start_time)
                logger.info(f"Tiempo restante para respuesta: {remaining_time:.3f}s")
                
                if remaining_time < 5.0:
                    # Si queda muy poco tiempo, enviamos una respuesta de error
                    response = {'error': 'Tiempo insuficiente para procesar la consulta'}
                    self.wfile.write(json.dumps(response).encode())
                    logger.warning(f"Tiempo insuficiente para procesar: {remaining_time:.3f}s")
                    log_to_file(f"Error: Tiempo insuficiente ({remaining_time:.3f}s)")
                    return
                
                # Procesar la consulta con el tiempo restante como límite
                rag_result = process_query(
                    query, 
                    timeout=remaining_time,
                    conversation_history=conversation_history
                )
                log_to_file(f"Resultado de process_query recibido")
                
                process_time = time.time() - start_time
                logger.info(f"process_query completado en {process_time:.3f}s")
                
                # Verificar el tipo de rag_result
                if not isinstance(rag_result, dict):
                    logger.error(f"Tipo inesperado de rag_result: {type(rag_result)}")
                    response = {'error': f"Error interno: resultado inesperado"}
                    self.wfile.write(json.dumps(response).encode())
                    log_to_file(f"Error: Tipo inesperado de rag_result: {type(rag_result)}")
                    return
                
                if "error" in rag_result:
                    logger.error(f"Error devuelto por process_query: {rag_result['error']}")
                    response = {'error': f"No se pudo procesar tu consulta: {rag_result['error']}"}
                    self.wfile.write(json.dumps(response).encode())
                    log_to_file(f"Error en process_query: {rag_result['error']}")
                    return
                
                # Verificar que rag_result contiene respuesta y fuentes
                if "response" not in rag_result:
                    logger.error("rag_result no contiene campo 'response'")
                    response = {'error': "Error interno: formato de respuesta incorrecto"}
                    self.wfile.write(json.dumps(response).encode())
                    log_to_file("Error: rag_result no contiene campo 'response'")
                    return
                
                # Asegurar que sources sea una lista
                if "sources" not in rag_result or not isinstance(rag_result["sources"], list):
                    logger.warning("rag_result contiene sources en formato incorrecto, ajustando")
                    rag_result["sources"] = []
                
                # Normalizar las fuentes usando la función de formato segura
                rag_result["sources"] = formatSources(rag_result["sources"])
                
                logger.info(f"Respuesta generada ({len(rag_result['response'])} caracteres): {rag_result['response'][:100]}...")
                
                # Registrar la consulta en la tabla 'queries'
                query_id = register_query_in_database(query, rag_result["response"], rag_result["sources"])
                if query_id:
                    rag_result["query_id"] = query_id
                
                # Enviar respuesta
                logger.info(f"Enviando respuesta al cliente: {time.time() - start_time:.3f}s")
                response_json = json.dumps(rag_result)
                log_to_file(f"Respuesta preparada (longitud: {len(response_json)})")
                self.wfile.write(response_json.encode())
                logger.info(f"=== FIN DE SOLICITUD === Total: {time.time() - start_time:.3f}s")
            except Exception as e:
                logger.error(f"Error en process_query: {str(e)}")
                logger.error(traceback.format_exc())
                trace = traceback.format_exc()
                log_to_file(f"Excepción en process_query: {str(e)}\n{trace[:300]}...")
                response = {'error': f"Error en process_query: {str(e)}"}
                self.wfile.write(json.dumps(response).encode())
                logger.info(f"=== ERROR EN SOLICITUD === Total: {time.time() - start_time:.3f}s")
            
        except Exception as e:
            # Obtener el traceback completo
            error_traceback = traceback.format_exc()
            logger.error(f"Error general: {str(e)}")
            logger.error(error_traceback)
            log_to_file(f"Error general: {str(e)}\n{error_traceback[:300]}...")
            
            response = {
                'error': f"Error general: {str(e)}",
                'traceback': error_traceback
            }
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"=== ERROR GENERAL EN SOLICITUD === Total: {time.time() - start_time:.3f}s")

