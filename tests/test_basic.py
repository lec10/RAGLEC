"""
Tests básicos para verificar la funcionalidad del sistema RAG.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

class TestEnvironmentVariables(unittest.TestCase):
    """Pruebas para las variables de entorno."""
    
    def setUp(self):
        """Configuración para las pruebas."""
        # Configurar variables de entorno para las pruebas
        os.environ["OPENAI_API_KEY"] = "sk-test-key"
        os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
        os.environ["SUPABASE_KEY"] = "test-key"
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "test-credentials.json"
        os.environ["GOOGLE_DRIVE_FOLDER_ID"] = "test-folder-id"
        
        # Recargar los módulos para que tomen las nuevas variables de entorno
        if "app.config.settings" in sys.modules:
            del sys.modules["app.config.settings"]
    
    def tearDown(self):
        """Limpieza después de las pruebas."""
        # Restaurar variables de entorno
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        if "SUPABASE_URL" in os.environ:
            del os.environ["SUPABASE_URL"]
        if "SUPABASE_KEY" in os.environ:
            del os.environ["SUPABASE_KEY"]
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        if "GOOGLE_DRIVE_FOLDER_ID" in os.environ:
            del os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    
    def test_openai_api_key(self):
        """Prueba que la clave API de OpenAI esté configurada."""
        from app.config.settings import OPENAI_API_KEY
        self.assertEqual(OPENAI_API_KEY, "sk-test-key")
    
    def test_supabase_credentials(self):
        """Prueba que las credenciales de Supabase estén configuradas."""
        from app.config.settings import SUPABASE_URL, SUPABASE_KEY
        self.assertEqual(SUPABASE_URL, "https://test-project.supabase.co")
        self.assertEqual(SUPABASE_KEY, "test-key")


class TestEmbeddingGenerator(unittest.TestCase):
    """Pruebas para el generador de embeddings."""
    
    @patch('app.document_processing.embeddings.OpenAIEmbeddings')
    def test_generate_embedding(self, mock_embeddings):
        """Prueba la generación de un embedding."""
        # Configurar el mock
        mock_instance = mock_embeddings.return_value
        mock_instance.embed_query.return_value = [0.1] * 1536
        
        # Importar después de configurar el mock
        from app.document_processing.embeddings import EmbeddingGenerator
        
        # Crear el generador de embeddings
        generator = EmbeddingGenerator()
        
        # Probar la generación de embeddings
        embedding = generator.generate_embedding("Texto de prueba")
        
        # Verificar que se llamó al método correcto
        mock_instance.embed_query.assert_called_once_with("Texto de prueba")
        
        # Verificar el resultado
        self.assertEqual(len(embedding), 1536)


class TestVectorDatabase(unittest.TestCase):
    """Pruebas para la base de datos vectorial."""
    
    @patch('app.database.supabase_client.create_client')
    def test_add_document(self, mock_create_client):
        """Prueba la adición de un documento a la base de datos."""
        # Configurar el mock
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        
        # Configurar el comportamiento del mock para table().select()
        mock_select = MagicMock()
        mock_select.execute.return_value = MagicMock(data=[])
        
        # Configurar el comportamiento del mock para table().insert()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock(data=[{"id": "test-id"}])
        
        # Configurar el comportamiento del mock para table()
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value = mock_select
        mock_table.insert.return_value = mock_insert
        mock_client.table.return_value = mock_table
        
        # Importar después de configurar el mock
        from app.database.vector_store import VectorDatabase
        
        # Crear la base de datos vectorial
        db = VectorDatabase("test_collection")
        
        # Probar la inserción de un documento
        result = db.add_document(
            doc_id="test-id",
            content="Contenido de prueba",
            metadata={"source": "test"},
            embedding=[0.1] * 1536
        )
        
        # Verificar que se llamó a insert con los parámetros correctos
        mock_client.table.assert_called_with("test_collection")
        mock_table.insert.assert_called_once()
        self.assertTrue(result)


class TestGoogleDriveClient(unittest.TestCase):
    """Pruebas para el cliente de Google Drive."""
    
    @patch('app.drive.google_drive_client.build')
    @patch('app.drive.google_drive_client.service_account.Credentials.from_service_account_file')
    def test_list_files(self, mock_credentials, mock_build):
        """Prueba la lista de archivos de Google Drive."""
        # Configurar los mocks
        mock_credentials.return_value = MagicMock()
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Configurar el comportamiento del mock para files().list()
        mock_files = MagicMock()
        mock_service.files.return_value = mock_files
        mock_list = MagicMock()
        mock_files.list.return_value = mock_list
        mock_list.execute.return_value = {
            "files": [
                {"id": "file1", "name": "test.pdf", "mimeType": "application/pdf"}
            ]
        }
        
        # Importar después de configurar el mock
        from app.drive.google_drive_client import GoogleDriveClient
        
        # Crear el cliente de Google Drive
        client = GoogleDriveClient()
        
        # Probar la obtención de archivos
        files = client.list_files("test-folder-id")
        
        # Verificar que se llamó a list con los parámetros correctos
        mock_service.files.assert_called_once()
        mock_files.list.assert_called_once()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["id"], "file1")
        self.assertEqual(files[0]["name"], "test.pdf")


class TestDocumentProcessor(unittest.TestCase):
    """Pruebas para el procesador de documentos."""
    
    def test_text_splitter(self):
        """Prueba la división de texto en fragmentos."""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Texto de prueba
        text = "Este es un texto de prueba. " * 50
        
        # Crear un splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
            length_function=len
        )
        
        # Dividir el texto en fragmentos
        chunks = splitter.split_text(text)
        
        # Verificar que se generaron fragmentos
        self.assertTrue(len(chunks) > 0)
        
        # Verificar que los fragmentos tienen el tamaño adecuado
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 100 + 20)  # chunk_size + overlap


class TestRAGQuerySystem(unittest.TestCase):
    """Pruebas para el sistema de consulta RAG."""
    
    @patch('app.query.rag_query.ChatOpenAI')
    @patch('app.query.rag_query.ChatPromptTemplate')
    @patch('app.query.rag_query.VectorDatabase')
    @patch('app.query.rag_query.EmbeddingGenerator')
    def test_query(self, mock_embedding_generator, mock_vector_db, mock_prompt_template, mock_chat_openai):
        """Prueba la realización de una consulta RAG."""
        # Configurar los mocks
        mock_embedding_instance = MagicMock()
        mock_embedding_generator.return_value = mock_embedding_instance
        mock_embedding_instance.generate_embedding.return_value = [0.1] * 1536
        
        mock_db_instance = MagicMock()
        mock_vector_db.return_value = mock_db_instance
        mock_db_instance.similarity_search.return_value = [
            {
                "id": "doc1",
                "content": "Contenido de prueba 1",
                "metadata": {"source": "test1.pdf", "page": 1},
                "similarity": 0.9
            },
            {
                "id": "doc2",
                "content": "Contenido de prueba 2",
                "metadata": {"source": "test2.pdf", "page": 2},
                "similarity": 0.8
            }
        ]
        
        # Configurar el mock de ChatPromptTemplate
        mock_prompt_instance = MagicMock()
        mock_prompt_template.from_template.return_value = mock_prompt_instance
        
        # Configurar el mock de ChatOpenAI
        mock_llm_instance = MagicMock()
        mock_chat_openai.return_value = mock_llm_instance
        
        # Configurar el mock para la cadena
        mock_chain = MagicMock()
        mock_chain.invoke.return_value.content = "Respuesta de prueba"
        
        # Configurar el operador | para que devuelva mock_chain
        mock_prompt_instance.__or__.return_value = mock_chain
        
        # Importar después de configurar los mocks
        from app.query.rag_query import RAGQuerySystem
        
        # Crear el sistema de consulta RAG
        rag_system = RAGQuerySystem()
        
        # Probar la consulta
        result = rag_system.query("¿Pregunta de prueba?")
        
        # Verificar que se llamaron los métodos correctos
        mock_embedding_instance.generate_embedding.assert_called_once()
        mock_db_instance.similarity_search.assert_called_once()
        mock_prompt_instance.__or__.assert_called_once_with(mock_llm_instance)
        mock_chain.invoke.assert_called_once()
        
        # Verificar la respuesta
        self.assertIn("answer", result)
        self.assertIn("sources", result)
        self.assertEqual(result["answer"], "Respuesta de prueba")
        self.assertEqual(len(result["sources"]), 2)


if __name__ == "__main__":
    unittest.main() 