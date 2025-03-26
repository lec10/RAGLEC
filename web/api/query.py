from http.server import BaseHTTPRequestHandler
import json
import os
import traceback
import time
from dotenv import load_dotenv

# Importar módulos de LangChain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from supabase import create_client

class handler(BaseHTTPRequestHandler):
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
        
        try:
            # Cargar variables de entorno
            load_dotenv()
            
            # Obtener el cuerpo de la solicitud
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Obtener la consulta
            query = data.get('query', '')
            
            if not query:
                response = {'error': 'La consulta está vacía'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Procesar la consulta con el sistema RAG independiente
            rag_result = process_query(query)
            
            # Enviar respuesta
            self.wfile.write(json.dumps(rag_result).encode())
            
        except Exception as e:
            # Obtener el traceback completo
            error_traceback = traceback.format_exc()
            
            response = {
                'error': str(e),
                'traceback': error_traceback,
                'api_key_set': bool(os.getenv("OPENAI_API_KEY")),
                'supabase_url_set': bool(os.getenv("SUPABASE_URL")),
                'supabase_key_set': bool(os.getenv("SUPABASE_KEY"))
            }
            self.wfile.write(json.dumps(response).encode())

def process_query(query, similarity_threshold=0.1, num_results=5):
    """Procesa una consulta usando el sistema RAG con LangChain."""
    start_time = time.time()
    
    try:
        # Inicializar componentes
        embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )
        
        # Conexión a Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # Generar embedding para la consulta
        query_embedding = embeddings.embed_query(query)
        
        # Buscar documentos relevantes en Supabase
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': num_results
            }
        ).execute()
        
        # Preparar documentos para LangChain
        documents = []
        if result.data:
            for doc in result.data:
                documents.append({
                    'content': doc['content'],
                    'file_name': doc['metadata'].get('name', 'Desconocido'),
                    'file_id': doc['metadata'].get('file_id', ''),
                    'chunk_index': doc['metadata'].get('chunk_index', 0),
                    'total_chunks': doc['metadata'].get('total_chunks', 0),
                    'similarity': doc['similarity']
                })
        
        # No se encontraron documentos relevantes
        if not documents:
            return {
                "response": "No se encontraron documentos relevantes para tu consulta. Por favor, intenta reformular tu pregunta o ajusta el umbral de similitud.",
                "sources": [],
                "metadata": {
                    "query": query,
                    "processing_time": time.time() - start_time,
                    "similarity_threshold": similarity_threshold,
                    "num_results": num_results
                }
            }
        
        # Construir el contexto para el prompt
        context = ""
        for i, doc in enumerate(documents):
            context += f"\nDocumento {i+1} (Fragmento {doc['chunk_index']+1} de {doc['total_chunks']}):\n{doc['content']}\n"
        
        # Configurar el modelo de lenguaje
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7,
        )
        
        # Crear el prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Eres un asistente especializado en responder consultas basándote exclusivamente en la información proporcionada."),
            ("human", """
            Responde a la siguiente pregunta basándote únicamente en la información proporcionada en los documentos.
            
            Contexto:
            {context}
            
            Pregunta: {query}
            
            Si la información no es suficiente para responder la pregunta completamente, indica qué parte de la información falta.
            Cita las fuentes en tu respuesta como (Documento #, Fragmento # de #).
            """)
        ])
        
        # Configurar la cadena RAG
        chain = (
            {"context": lambda _: context, "query": lambda x: x}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        # Ejecutar la cadena
        response_text = chain.invoke(query)
        
        # Guardar la consulta en la base de datos (opcional)
        try:
            supabase.table("queries").insert({
                "query": query,
                "response": response_text,
                "sources": json.dumps([{
                    "file_name": doc["file_name"],
                    "file_id": doc["file_id"],
                    "chunk_index": doc["chunk_index"],
                    "similarity": doc["similarity"]
                } for doc in documents]),
                "metadata": json.dumps({
                    "processing_time": time.time() - start_time,
                    "similarity_threshold": similarity_threshold,
                    "num_results": num_results
                })
            }).execute()
        except Exception as e:
            print(f"Error al guardar consulta: {e}")
        
        # Preparar resultado
        result = {
            "response": response_text,
            "sources": documents,
            "metadata": {
                "query": query,
                "processing_time": time.time() - start_time,
                "similarity_threshold": similarity_threshold,
                "num_results": num_results
            }
        }
        
        return result
    
    except Exception as e:
        print(f"Error en process_query: {e}")
        traceback.print_exc()
        return {"error": str(e)} 