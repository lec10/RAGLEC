"""
Métricas de rendimiento para la aplicación RAG.
Este módulo proporciona funciones para hacer un seguimiento del rendimiento de la base de datos vectorial y el sistema RAG.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import statistics

# Configurar logging
logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Clase para hacer un seguimiento del rendimiento de la aplicación RAG."""
    
    def __init__(self):
        """Inicializa el rastreador de rendimiento."""
        self.metrics = {
            "embedding_generation": [],
            "similarity_search": [],
            "document_processing": [],
            "llm_response": [],
            "total_query_time": []
        }
        self.query_counts = 0
        logger.info("Rastreador de rendimiento inicializado")
    
    def track_time(self, operation: str) -> Callable:
        """Decorador para rastrear el tiempo de ejecución de una función.
        
        Args:
            operation: Nombre de la operación a rastrear.
        
        Returns:
            Callable: Función decorada.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                
                if operation in self.metrics:
                    self.metrics[operation].append(execution_time)
                    if len(self.metrics[operation]) > 100:
                        # Limitar a los últimos 100 valores para evitar un crecimiento excesivo
                        self.metrics[operation] = self.metrics[operation][-100:]
                
                logger.debug(f"Operación {operation} completada en {execution_time:.4f} segundos")
                return result
            return wrapper
        return decorator
    
    def track_query(self, query_time: float, embedding_time: float, search_time: float, llm_time: float):
        """Registra los tiempos de una consulta completa.
        
        Args:
            query_time: Tiempo total de la consulta.
            embedding_time: Tiempo de generación de embeddings.
            search_time: Tiempo de búsqueda por similitud.
            llm_time: Tiempo de respuesta del LLM.
        """
        self.metrics["total_query_time"].append(query_time)
        self.metrics["embedding_generation"].append(embedding_time)
        self.metrics["similarity_search"].append(search_time)
        self.metrics["llm_response"].append(llm_time)
        
        # Limitar a los últimos 100 valores
        for key in self.metrics:
            if len(self.metrics[key]) > 100:
                self.metrics[key] = self.metrics[key][-100:]
        
        self.query_counts += 1
        logger.debug(f"Consulta #{self.query_counts} registrada")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento.
        
        Returns:
            Dict[str, Any]: Estadísticas de rendimiento.
        """
        stats = {}
        
        for operation, times in self.metrics.items():
            if times:
                stats[operation] = {
                    "avg": statistics.mean(times),
                    "min": min(times),
                    "max": max(times),
                    "median": statistics.median(times),
                    "count": len(times),
                    "latest": times[-1]
                }
                
                # Calcular percentiles si hay suficientes datos
                if len(times) >= 10:
                    stats[operation]["p90"] = self._percentile(times, 90)
                    stats[operation]["p95"] = self._percentile(times, 95)
                    stats[operation]["p99"] = self._percentile(times, 99)
            else:
                stats[operation] = {
                    "avg": 0,
                    "min": 0,
                    "max": 0,
                    "median": 0,
                    "count": 0,
                    "latest": 0
                }
        
        stats["total_queries"] = self.query_counts
        stats["timestamp"] = datetime.now().isoformat()
        
        return stats
    
    def reset_metrics(self):
        """Reinicia las métricas de rendimiento."""
        for key in self.metrics:
            self.metrics[key] = []
        logger.info("Métricas de rendimiento reiniciadas")
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcula un percentil de los datos.
        
        Args:
            data: Datos para calcular el percentil.
            percentile: Percentil a calcular (0-100).
            
        Returns:
            float: Valor del percentil.
        """
        sorted_data = sorted(data)
        n = len(sorted_data)
        rank = percentile / 100 * (n - 1)
        
        if rank.is_integer():
            return sorted_data[int(rank)]
        else:
            lower_rank = int(rank)
            upper_rank = lower_rank + 1
            weight = rank - lower_rank
            return (1 - weight) * sorted_data[lower_rank] + weight * sorted_data[upper_rank]
    
    def log_performance_to_file(self, file_path: str = "performance_metrics.json"):
        """Registra las estadísticas de rendimiento en un archivo.
        
        Args:
            file_path: Ruta al archivo donde guardar las estadísticas.
        """
        try:
            stats = self.get_performance_stats()
            
            with open(file_path, "w") as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"Estadísticas de rendimiento guardadas en {file_path}")
        except Exception as e:
            logger.error(f"Error al guardar las estadísticas de rendimiento: {e}")

# Instancia global del rastreador de rendimiento
performance_tracker = PerformanceTracker() 