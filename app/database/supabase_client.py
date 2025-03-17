"""
Cliente para interactuar con Supabase.
"""

import logging
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from app.config.settings import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

class SupabaseVectorStore:
    """Cliente para interactuar con Supabase."""
    
    def __init__(self):
        """Inicializa el cliente de Supabase."""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.error("Las credenciales de Supabase no están configuradas")
                self.client = None
            else:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("Cliente de Supabase inicializado")
        except Exception as e:
            logger.error(f"Error al conectar con Supabase: {e}")
            self.client = None
    
    def get_client(self) -> Optional[Client]:
        """Obtiene el cliente de Supabase.
        
        Returns:
            Optional[Client]: Cliente de Supabase o None si no se pudo inicializar.
        """
        return self.client
    
    def health_check(self) -> bool:
        """Verifica la conexión con Supabase.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario.
        """
        if not self.client:
            return False
        
        try:
            # Intentar una operación simple para verificar la conexión
            self.client.table("healthcheck").select("*").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Error al verificar la conexión con Supabase: {e}")
            return False

# Crear una instancia del cliente de Supabase
# No lo inicializamos aquí para evitar errores durante la importación
supabase_client = None

def get_supabase_client() -> SupabaseVectorStore:
    """Obtiene una instancia del cliente de Supabase.
    
    Returns:
        SupabaseVectorStore: Cliente de Supabase.
    """
    global supabase_client
    if supabase_client is None:
        supabase_client = SupabaseVectorStore()
    return supabase_client 