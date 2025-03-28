from http.server import BaseHTTPRequestHandler
import json
import os
import logging
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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
        
        logger.info("Recibiendo feedback del usuario")
        
        try:
            # Obtener el cuerpo de la solicitud
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Extraer datos
            query_id = data.get('query_id')
            feedback = data.get('feedback') # 1 para thumbs up, -1 para thumbs down
            
            logger.info(f"Feedback recibido - query_id: {query_id}, valor: {feedback}")
            
            if not query_id or feedback is None:
                response = {'error': 'Se requieren query_id y feedback'}
                self.wfile.write(json.dumps(response).encode())
                logger.error("Faltan parámetros requeridos")
                return
                
            # Verificar que tenemos las credenciales de Supabase
            if not SUPABASE_URL or not SUPABASE_KEY:
                response = {'error': 'Credenciales de Supabase no configuradas'}
                self.wfile.write(json.dumps(response).encode())
                logger.error("Credenciales de Supabase no configuradas")
                return
                
            # Actualizar el registro en la tabla queries
            try:
                # Conexión a Supabase
                logger.info(f"Conectando a Supabase para actualizar feedback de {query_id}")
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                # Actualizar el feedback
                logger.info(f"Actualizando registro en tabla queries con feedback={feedback}")
                result = supabase.table("queries").update({
                    "user_feedback": feedback
                }).eq("id", query_id).execute()
                
                # Verificar si se actualizó correctamente
                if not result.data or len(result.data) == 0:
                    logger.error(f"No se encontró la consulta con ID {query_id}")
                    logger.debug(f"Respuesta de Supabase: {result}")
                    response = {'error': f'No se encontró la consulta con ID {query_id}'}
                    self.wfile.write(json.dumps(response).encode())
                    return
                    
                logger.info(f"Feedback actualizado correctamente para la consulta {query_id}: {feedback}")
                response = {'success': True, 'message': 'Feedback registrado correctamente'}
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                logger.error(f"Error al actualizar el feedback: {str(e)}")
                logger.exception("Detalle del error:")
                response = {'error': f"Error al actualizar el feedback: {str(e)}"}
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            logger.error(f"Error general en endpoint de feedback: {str(e)}")
            logger.exception("Detalle del error:")
            response = {'error': f"Error general: {str(e)}"}
            self.wfile.write(json.dumps(response).encode()) 