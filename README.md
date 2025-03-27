# RAGLEC - Sistema RAG para Consulta de Documentos

RAGLEC es una aplicación de Retrieval Augmented Generation (RAG) que monitorea una carpeta de Google Drive, procesa los documentos para crear una base de datos vectorial, y permite realizar consultas sobre el contenido de esos documentos.

## Características

- **Monitoreo de Google Drive**: Detecta automáticamente archivos nuevos, modificados o eliminados en una carpeta específica de Google Drive.
- **Procesamiento de Documentos**: Soporta múltiples formatos de documentos (PDF, DOCX, TXT) y los divide en fragmentos para su procesamiento.
- **Base de Datos Vectorial**: Utiliza Supabase con la extensión pgvector para almacenar y buscar documentos por similitud semántica.
- **Generación de Embeddings**: Utiliza el modelo text-embedding-3-small de OpenAI para generar embeddings de alta calidad.
- **Consultas RAG**: Permite realizar consultas en lenguaje natural sobre el contenido de los documentos.
- **Interfaz de Chat**: Proporciona una interfaz de línea de comandos para interactuar con el sistema.
- **Interfaz Web**: Incluye una interfaz web para realizar consultas al sistema mediante un navegador.
- **Documentación Completa**: Incluye documentación detallada en la carpeta `/docs` sobre la arquitectura, componentes y uso del sistema.
- **Utilidades de Mantenimiento**: Scripts para gestionar la base de datos y solucionar problemas comunes.

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

1. Crea una cuenta en [Supabase](https://supabase.com/) si aún no tienes una
2. Crea un nuevo proyecto
3. Habilita la extensión pgvector:
   - Vaya a la sección "Database" > "Extensions"
   - Busque "vector" y habilítelo
4. Obtenga la URL y la clave de API:
   - Vaya a "Project Settings" > "API"
   - Copie la URL del proyecto y la clave anon/public
5. Añade estas credenciales a tu archivo `.env`:

```
SUPABASE_URL=tu_url_de_supabase_aqui
SUPABASE_KEY=tu_clave_api_aqui
```

### Configuración SQL de Supabase

Una vez configurada tu cuenta de Supabase, debes ejecutar los siguientes scripts SQL para crear las tablas y funciones necesarias. Puedes hacerlo desde el Editor SQL en el panel de control de Supabase:

1. **Crear tabla de documentos**:
```sql
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. **Crear tabla de archivos**:
```sql
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mime_type TEXT,
    source TEXT,
    last_modified TIMESTAMP,
    status TEXT,
    chunk_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

3. **Crear tabla de consultas**:
```sql
CREATE TABLE IF NOT EXISTS queries (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    response TEXT,
    sources JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

4. **Crear función de búsqueda por similitud**:
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

5. **Crear índice para búsquedas más rápidas** (opcional pero recomendado):
```sql
CREATE INDEX ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Google Drive

1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilita la API de Google Drive
3. Configura credenciales de acceso y descarga el archivo JSON
4. Guarda el archivo en la carpeta `credentials/` del proyecto
5. Añade la ruta al archivo `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=credentials/tu-archivo-credenciales.json
```

6. Configura el ID de la carpeta de Google Drive a monitorear:
```
GOOGLE_DRIVE_FOLDER_ID=id_de_carpeta_aqui
```

## Uso

RAGLEC proporciona varios comandos a través del script principal `main.py`:

### Procesar Documentos

Para procesar documentos en la carpeta monitoreada de Google Drive:

```
python main.py process
```

### Interfaz de Chat

Para iniciar la interfaz de chat y realizar consultas:

```
python main.py chat
```

En la interfaz de chat, puedes usar los siguientes comandos:
- Cualquier texto para realizar una consulta
- `threshold [valor]`: Cambia el umbral de similitud (0-1)
- `statistics`: Muestra estadísticas de documentos
- `history [n]`: Muestra historial de consultas
- `performance`: Muestra métricas de rendimiento

### Administración de la Base de Datos

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

### Interfaz Web

Para iniciar la interfaz web localmente:

```
cd web
python -m http.server 8000
```

La interfaz web también puede ser desplegada en Vercel:

1. Crea una cuenta en [Vercel](https://vercel.com) si aún no tienes una
2. Instala la CLI de Vercel:
   ```
   npm install -g vercel
   ```
3. Navega a la carpeta web y despliega:
   ```
   cd web
   vercel
   ```

Una vez desplegada, podrás acceder a la interfaz web a través de la URL proporcionada por Vercel.

### Utilidades

En la carpeta `utilities/` se incluyen scripts útiles para el mantenimiento del sistema:

- `clear_database.py`: Limpia las tablas de la base de datos
  ```
  python utilities/clear_database.py [opciones]
  ```
  Opciones:
  - `--no-backup`: No crear backups antes de borrar
  - `--no-confirm`: No solicitar confirmación
  - `--tables [tabla1 tabla2]`: Especificar tablas a limpiar

## Parámetros Configurables

RAGLEC tiene varios parámetros configurables:

### Procesamiento de Documentos
- `CHUNK_SIZE`: Tamaño de los fragmentos (por defecto: 3000 caracteres)
- `CHUNK_OVERLAP`: Superposición entre fragmentos (por defecto: 400 caracteres)

### Generación de Embeddings
- `OPENAI_EMBEDDING_MODEL`: Modelo para embeddings (por defecto: text-embedding-3-small)

### Búsquedas por Similitud
- `DEFAULT_SIMILARITY_THRESHOLD`: Umbral de similitud (por defecto: 0.1)
- `DEFAULT_NUM_RESULTS`: Número de resultados (por defecto: 5)

## Estructura del Proyecto

```
RAGLEC/
├── app/                            # Paquete principal de la aplicación
│   ├── config/                     # Configuración de la aplicación
│   ├── core/                       # Componentes centrales
│   ├── database/                   # Gestión de la base de datos vectorial
│   ├── document_processing/        # Procesamiento de documentos
│   ├── drive/                      # Integración con Google Drive
│   ├── query/                      # Sistema de consultas RAG
│   └── utils/                      # Utilidades
├── docs/                           # Documentación detallada del sistema
│   ├── architecture/               # Arquitectura y diseño
│   ├── modules/                    # Documentación de módulos
│   ├── guides/                     # Guías de usuario
│   ├── api/                        # Documentación de API
│   ├── maintenance/                # Mantenimiento y solución de problemas
│   └── overview.md                 # Visión general del sistema
├── tests/                          # Pruebas automatizadas
├── utilities/                      # Scripts de utilidad y mantenimiento
├── .env.example                    # Ejemplo de archivo de variables de entorno
├── main.py                         # Script principal
├── README.md                       # Documentación
└── requirements.txt                # Dependencias
```

Para una descripción detallada de cada componente, consulta la [documentación completa](docs/overview.md).

## Documentación

La documentación completa del sistema se encuentra en la carpeta `/docs`. Incluye:

- Descripción detallada de la arquitectura
- Explicación de cada módulo y sus componentes
- Guías de instalación y uso
- Solución de problemas comunes
- Consideraciones de rendimiento y optimización

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para sugerir cambios o mejoras. 