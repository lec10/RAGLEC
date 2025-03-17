"""
Sistema de consultas RAG.
Este módulo proporciona funciones para realizar consultas RAG utilizando la base de datos vectorial.
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document

from app.document_processing.embeddings import EmbeddingGenerator
from app.database.vector_store import VectorDatabase
from app.config.settings import LLM_MODEL, OPENAI_API_KEY
from app.utils.performance_metrics import performance_tracker

# Configurar logging
logger = logging.getLogger(__name__)

class RAGQuerySystem:
    """Clase para realizar consultas RAG utilizando la base de datos vectorial."""
    
    def __init__(self, model_name: str = LLM_MODEL, api_key: str = OPENAI_API_KEY):
        """Inicializa el sistema de consultas RAG.
        
        Args:
            model_name: Nombre del modelo de lenguaje.
            api_key: Clave API de OpenAI.
        """
        self.embedding_generator = EmbeddingGenerator()
        self.vector_db = VectorDatabase()
        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            temperature=0.1
        )
        
        # Asignar el rastreador de rendimiento
        self.performance_tracker = performance_tracker
        
        # Plantilla para el prompt de RAG
        self.prompt_template = ChatPromptTemplate.from_template(
            """Eres un asistente útil que responde preguntas basándose únicamente en el contexto proporcionado.
            
            Contexto:
            {context}
            
            Pregunta: {question}
            
            Instrucciones importantes:
            1. Responde solo con información que esté presente en el contexto proporcionado.
            2. Si el contexto no contiene la información necesaria para responder, di "No tengo suficiente información para responder a esta pregunta."
            3. No uses conocimiento externo o general que no esté en el contexto.
            4. Proporciona respuestas detalladas y precisas basadas únicamente en el contexto.
            5. Cita las fuentes de información cuando sea posible, refiriéndote al nombre del documento y número de fragmento.
            6. Si hay información contradictoria en el contexto, señálala y explica las diferentes perspectivas.
            
            Respuesta:"""
        )
        
        logger.info(f"Sistema de consultas RAG inicializado con el modelo {model_name}")
    
    @performance_tracker.track_time("total_query_time")
    def query(self, question: str, num_results: int = 5, similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """Realiza una consulta RAG.
        
        Args:
            question: Pregunta del usuario.
            num_results: Número de resultados a recuperar.
            similarity_threshold: Umbral de similitud mínima (0-1).
            
        Returns:
            Dict[str, Any]: Respuesta y metadatos.
        """
        try:
            # Configurar temporalmente el logger a nivel DEBUG para ver los metadatos
            logger.setLevel(logging.DEBUG)
            
            logger.info(f"Procesando consulta: {question}")
            
            total_start_time = time.time()
            
            # Generar embedding para la consulta
            embedding_start_time = time.time()
            query_embedding = self.embedding_generator.generate_embedding(question)
            embedding_time = time.time() - embedding_start_time
            
            if not query_embedding:
                logger.error("No se pudo generar el embedding para la consulta")
                return {
                    "answer": "Lo siento, no pude procesar tu consulta en este momento.",
                    "sources": [],
                    "success": False
                }
            
            # Realizar búsqueda por similitud
            search_start_time = time.time()
            results = self.vector_db.similarity_search(
                query_embedding=query_embedding, 
                top_k=num_results,
                threshold=similarity_threshold
            )
            search_time = time.time() - search_start_time
            
            if not results:
                logger.warning("No se encontraron resultados para la consulta")
                response = {
                    "answer": "No encontré información relevante para responder a tu pregunta.",
                    "sources": [],
                    "success": True
                }
                
                # Registrar la consulta en la base de datos
                self.vector_db.log_query(question, response["answer"], response["sources"])
                
                # Registrar tiempos en el rastreador de rendimiento
                total_time = time.time() - total_start_time
                performance_tracker.track_query(
                    query_time=total_time,
                    embedding_time=embedding_time,
                    search_time=search_time,
                    llm_time=0.0  # No se llamó al LLM
                )
                
                return response
            
            # Preparar el contexto para el LLM
            context = self._prepare_context(results)
            
            # Generar la respuesta
            llm_start_time = time.time()
            chain = self.prompt_template | self.llm
            llm_response = chain.invoke({
                "context": context,
                "question": question
            })
            llm_time = time.time() - llm_start_time
            
            # Extraer las fuentes
            sources = self._extract_sources(results)
            
            response = {
                "answer": llm_response.content,
                "sources": sources,
                "success": True
            }
            
            # Registrar la consulta en la base de datos
            self.vector_db.log_query(question, response["answer"], sources)
            
            # Registrar tiempos en el rastreador de rendimiento
            total_time = time.time() - total_start_time
            performance_tracker.track_query(
                query_time=total_time,
                embedding_time=embedding_time,
                search_time=search_time,
                llm_time=llm_time
            )
            
            logger.info(f"Consulta procesada correctamente en {total_time:.3f} segundos")
            logger.debug(f"Tiempos de procesamiento: embedding={embedding_time:.3f}s, search={search_time:.3f}s, llm={llm_time:.3f}s")
            
            return response
        except Exception as e:
            logger.error(f"Error al procesar la consulta: {e}")
            return {
                "answer": "Lo siento, ocurrió un error al procesar tu consulta.",
                "sources": [],
                "success": False
            }
    
    def _prepare_context(self, results: List[Dict[str, Any]]) -> str:
        """Prepara el contexto para el LLM a partir de los resultados de la búsqueda.
        
        Args:
            results: Resultados de la búsqueda por similitud.
            
        Returns:
            str: Contexto formateado.
        """
        context_parts = []
        
        for i, result in enumerate(results):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            similarity = result.get("similarity", 0.0)
            
            # Extraer información relevante de los metadatos
            file_name = metadata.get("name", "Desconocido")
            chunk_index = metadata.get("chunk_index", 0)
            total_chunks = metadata.get("total_chunks", 1)
            
            # Formatear el fragmento con su fuente y información de similitud
            context_part = (
                f"[Documento {i+1}: {file_name} | "
                f"Fragmento {chunk_index + 1} de {total_chunks} | "
                f"Relevancia: {similarity:.2f}]\n{content}\n"
            )
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrae información de las fuentes de los resultados.
        
        Args:
            results: Resultados de la búsqueda por similitud.
            
        Returns:
            List[Dict[str, Any]]: Lista de fuentes.
        """
        sources = []
        
        for i, result in enumerate(results):
            metadata = result.get("metadata", {})
            similarity = result.get("similarity", 0.0)
            
            # Imprimir los metadatos para depuración
            logger.debug(f"Metadatos completos del resultado {i+1}: {metadata}")
            
            # Intentar obtener el file_id de varias fuentes posibles
            file_id = metadata.get("file_id", "")
            if not file_id:
                # Buscar en otras ubicaciones posibles
                file_id = metadata.get("id", "")
                if not file_id:
                    file_id = metadata.get("file", {}).get("id", "")
                    if not file_id:
                        # Verificar si viene desde el padre
                        file_id = result.get("file_id", "")
            
            logger.debug(f"File ID encontrado: {file_id}")
            
            # Extraer información relevante
            source = {
                "file_name": metadata.get("name", "Desconocido"),
                "file_id": file_id,
                "chunk_id": result.get("id", ""),
                "chunk_index": metadata.get("chunk_index", 0),
                "total_chunks": metadata.get("total_chunks", 1),
                "similarity": similarity,
                "rank": i + 1
            }
            
            sources.append(source)
        
        return sources
    
    def get_query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene el historial de consultas.
        
        Args:
            limit: Número máximo de consultas a devolver.
            
        Returns:
            List[Dict[str, Any]]: Historial de consultas.
        """
        try:
            # Obtener las consultas de la base de datos
            response = self.vector_db.client.table("queries") \
                .select("*") \
                .order("created_at", options={"ascending": False}) \
                .limit(limit) \
                .execute()
            
            queries = response.data
            
            # Procesar los resultados
            for query in queries:
                if "sources" in query and query["sources"]:
                    query["sources"] = json.loads(query["sources"])
            
            logger.info(f"Se obtuvieron {len(queries)} consultas del historial")
            return queries
        except Exception as e:
            logger.error(f"Error al obtener el historial de consultas: {e}")
            return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento de las consultas.
        
        Returns:
            Dict[str, Any]: Estadísticas de rendimiento.
        """
        return performance_tracker.get_performance_stats() 