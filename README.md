# RAGLEC - Sistema RAG para Consulta de Documentos

RAGLEC es una aplicación de Retrieval Augmented Generation (RAG) que monitorea una carpeta de Google Drive, procesa los documentos para crear una base de datos vectorial, y permite realizar consultas sobre el contenido de esos documentos.

## Características

- **Monitoreo de Google Drive**: Detecta automáticamente archivos nuevos, modificados o eliminados en una carpeta específica de Google Drive.
- **Procesamiento de Documentos**: Soporta múltiples formatos de documentos (PDF, DOCX, TXT) y los divide en fragmentos para su procesamiento.
- **Base de Datos Vectorial**: Utiliza Supabase con la extensión pgvector para almacenar y buscar documentos por similitud semántica.
- **Generación de Embeddings**: Utiliza el modelo text-embedding-3-small de OpenAI para generar embeddings de alta calidad.
- **Consultas RAG**: Permite realizar consultas en lenguaje natural sobre el contenido de los documentos.
- **Interfaz de Chat**: Proporciona una interfaz de línea de comandos para interactuar con el sistema.

## Requisitos

- Python 3.8 o superior
- Cuenta de OpenAI con acceso a la API
- Cuenta de Supabase con la extensión pgvector habilitada
- Cuenta de Google Cloud con acceso a la API de Google Drive
- Archivo de credenciales de servicio de Google Cloud

## Instalación

1. Clona este repositorio:
   ```
   git clone https://github.com/tu-usuario/RAGLEC.git
   cd RAGLEC
   ```

2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Crea un archivo `.env` basado en `.env.example` y configura tus credenciales:
   ```
   cp .env.example .env
   # Edita el archivo .env con tus credenciales
   ```

## Configuración

### OpenAI API

1. Obtén una clave API de OpenAI en [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Añade la clave a tu archivo `.env`:
   ```
   OPENAI_API_KEY=tu_clave_api_aqui
   ```

### Supabase

1. Crea una cuenta en [Supabase](https://supabase.com/)
2. Crea un nuevo proyecto y habilita la extensión pgvector
3. Crea una tabla para almacenar los documentos con la siguiente estructura:
   ```sql
   CREATE TABLE documents (
     id TEXT PRIMARY KEY,
     content TEXT,
     metadata JSONB,
     embedding VECTOR(1536),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```
4. Crea una función para buscar documentos por similitud:
   ```sql
   CREATE OR REPLACE FUNCTION match_documents(
     query_embedding VECTOR(1536),
     match_threshold FLOAT,
     match_count INT
   )
   RETURNS TABLE (
     id TEXT,
     content TEXT,
     metadata JSONB,
     similarity FLOAT
   )
   LANGUAGE plpgsql
   AS $$
   BEGIN
     RETURN QUERY
     SELECT
       documents.id,
       documents.content,
       documents.metadata,
       1 - (documents.embedding <=> query_embedding) AS similarity
     FROM documents
     WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
     ORDER BY similarity DESC
     LIMIT match_count;
   END;
   $$;
   ```
5. Añade la URL y la clave de Supabase a tu archivo `.env`:
   ```
   SUPABASE_URL=tu_url_de_supabase
   SUPABASE_KEY=tu_clave_de_supabase
   SUPABASE_COLLECTION_NAME=documents
   ```

### Google Drive API

1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilita la API de Google Drive
3. Crea una cuenta de servicio y descarga el archivo de credenciales JSON
4. Añade la ruta al archivo de credenciales y el ID de la carpeta a monitorear a tu archivo `.env`:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=ruta/a/tu/archivo-credenciales.json
   GOOGLE_DRIVE_FOLDER_ID=id_de_la_carpeta_a_monitorear
   ```

## Uso

### Procesar todos los documentos

Para procesar todos los documentos en la carpeta de Google Drive:

```
python main.py process
```

### Iniciar el monitoreo

Para iniciar el monitoreo de la carpeta de Google Drive:

```
python main.py monitor
```

### Iniciar la interfaz de chat

Para iniciar la interfaz de chat y realizar consultas:

```
python main.py chat
```

### Administrar la base de datos vectorial

Para administrar la base de datos vectorial, utiliza el siguiente comando:

```
python main.py admin [comando]
```

Comandos disponibles:

- `list`: Lista los archivos en la base de datos
- `show [file_id]`: Muestra los detalles de un archivo
  - `--chunks`: Muestra información de los fragmentos
  - `--content`: Muestra el contenido de los fragmentos
  - `--full`: Muestra el contenido completo de los fragmentos
- `delete [file_id]`: Elimina un archivo de la base de datos
  - `-f, --force`: No pedir confirmación
- `queries`: Lista las consultas realizadas
  - `--limit [num]`: Número máximo de consultas a mostrar
- `setup`: Ejecuta el script de configuración de la base de datos
  - `--check`: Verifica la configuración de la base de datos
- `export`: Exporta datos de la base de datos
  - `--files`: Exportar información de archivos
  - `--queries`: Exportar consultas
  - `--documents`: Exportar documentos (fragmentos)
  - `-o, --output [file]`: Archivo de salida

Ejemplos:

```
# Listar archivos en la base de datos
python main.py admin list

# Mostrar detalles de un archivo
python main.py admin show abc123 --chunks

# Eliminar un archivo
python main.py admin delete abc123

# Exportar datos
python main.py admin export --files --queries -o export_data.json
```

## Estructura del Proyecto

```
RAGLEC/
├── app/
│   ├── config/             # Configuración de la aplicación
│   ├── core/               # Componentes principales
│   ├── database/           # Gestión de la base de datos vectorial
│   ├── document_processing/ # Procesamiento de documentos
│   ├── drive/              # Integración con Google Drive
│   ├── query/              # Sistema de consultas RAG
│   └── utils/              # Utilidades
├── .env.example            # Ejemplo de archivo de variables de entorno
├── main.py                 # Script principal
├── README.md               # Documentación
└── requirements.txt        # Dependencias
```

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para sugerir cambios o mejoras. 