# Módulo de Base de Datos

El módulo de base de datos proporciona funcionalidades para gestionar la base de datos vectorial, almacenar documentos y realizar búsquedas por similitud.

## Componentes

### 1. Vector Database (`vector_store.py`)

La clase `VectorDatabase` es el componente principal y proporciona una interfaz para interactuar con la base de datos vectorial.

#### Características Principales

- Almacenamiento y recuperación de documentos con embeddings
- Búsqueda semántica por similitud
- Gestión de metadatos de documentos
- Registro de consultas para análisis

#### Métodos Importantes

```python
def __init__(self, collection_name: str = None):
    """Inicializa la base de datos vectorial con una colección específica."""
    
def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any], embedding: List[float]) -> bool:
    """Añade un documento a la base de datos."""
    
def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any], embedding: List[float]) -> bool:
    """Actualiza un documento existente."""
    
def delete_document(self, doc_id: str) -> bool:
    """Elimina un documento de la base de datos."""
    
def similarity_search(self, query_embedding: List[float], top_k: int = 5, threshold: float = 0.1) -> List[Dict[str, Any]]:
    """Realiza una búsqueda por similitud."""
    
def log_query(self, query: str, response: str, sources: List[Dict[str, Any]]) -> bool:
    """Registra una consulta en la base de datos."""
    
def get_file_info(self, file_id: str) -> Dict[str, Any]:
    """Obtiene información de un archivo."""
    
def list_files(self, limit: int = 100) -> List[Dict[str, Any]]:
    """Lista los archivos en la base de datos."""
    
def get_chunks_by_file_id(self, file_id: str) -> List[Dict[str, Any]]:
    """Obtiene todos los fragmentos asociados a un archivo."""
    
def delete_chunks_by_file_id(self, file_id: str) -> int:
    """Elimina todos los fragmentos asociados a un archivo."""
```

### 2. Cliente Supabase (`supabase_client.py`)

Proporciona una abstracción para interactuar con la API de Supabase.

#### Características Principales

- Conexión a la base de datos Supabase
- Gestión de credenciales
- Implementación de patrones singleton para reutilización de conexiones

#### Métodos Importantes

```python
def get_supabase_client():
    """Obtiene una instancia del cliente Supabase."""
    
class SupabaseStore:
    def __init__(self):
        """Inicializa el cliente Supabase."""
        
    def get_client(self):
        """Obtiene el cliente de Supabase."""
```

### 3. Administración de la Base de Datos (`admin_cli.py`)

Proporciona una interfaz de línea de comandos para administrar la base de datos.

#### Características Principales

- Listar archivos en la base de datos
- Mostrar detalles de archivos y fragmentos
- Eliminar archivos
- Exportar datos

#### Comandos Disponibles

- `list`: Lista archivos en la base de datos
- `show [file_id]`: Muestra detalles de un archivo
- `delete [file_id]`: Elimina un archivo
- `setup`: Configura la base de datos
- `queries`: Muestra consultas registradas
- `export`: Exporta datos

## Configuración de la Base de Datos

### Esquema de Base de Datos (`supabase_unified.sql`)

El esquema define las tablas y funciones necesarias para el sistema.

#### Tablas Principales

1. **documents**: Almacena fragmentos de documentos y sus embeddings
   - `id`: TEXT (Primary Key)
   - `content`: TEXT
   - `metadata`: JSONB
   - `embedding`: VECTOR(1536)
   - `file_id`: TEXT
   - `created_at`: TIMESTAMP
   - `updated_at`: TIMESTAMP

2. **files**: Contiene información de los archivos procesados
   - `id`: TEXT (Primary Key)
   - `name`: TEXT
   - `mime_type`: TEXT
   - `source`: TEXT
   - `last_modified`: TIMESTAMP
   - `processed_at`: TIMESTAMP
   - `status`: TEXT
   - `metadata`: JSONB

3. **queries**: Registra las consultas realizadas y sus respuestas
   - `id`: SERIAL (Primary Key)
   - `query`: TEXT
   - `response`: TEXT
   - `sources`: JSONB
   - `created_at`: TIMESTAMP
   - `user_feedback`: INTEGER

4. **healthcheck**: Utilizada para verificar el estado del sistema
   - `id`: SERIAL (Primary Key)
   - `status`: TEXT
   - `last_check`: TIMESTAMP

#### Funciones SQL

1. **match_documents**: Implementa la búsqueda por similitud coseno

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

2. **get_chunks_by_file_id**: Obtiene los fragmentos asociados a un archivo

```sql
CREATE OR REPLACE FUNCTION get_chunks_by_file_id(file_id_param TEXT)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.metadata
    FROM documents
    WHERE 
        metadata->>'file_id' = file_id_param
        OR (file_id_param = documents.file_id AND documents.file_id IS NOT NULL);
END;
$$;
```

3. **delete_chunks_by_file_id**: Elimina los fragmentos asociados a un archivo

```sql
CREATE OR REPLACE FUNCTION delete_chunks_by_file_id(file_id TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Contar primero cuántos registros se eliminarán
    SELECT COUNT(*) INTO deleted_count
    FROM documents
    WHERE metadata->>'file_id' = file_id 
          OR (file_id = documents.file_id AND documents.file_id IS NOT NULL);
    
    -- Luego eliminar sin usar RETURNING
    DELETE FROM documents
    WHERE metadata->>'file_id' = file_id
          OR (file_id = documents.file_id AND documents.file_id IS NOT NULL);

    RETURN deleted_count;
END;
$$;
```

## Parámetros Importantes

### Umbral de Similitud

El parámetro `threshold` en la función `similarity_search` determina la similitud mínima requerida para considerar un documento como relevante:

- **Valor predeterminado**: 0.1
- **Rango válido**: 0.0 a 1.0
- **Recomendación**: Valores entre 0.1 y 0.3 suelen ofrecer buenos resultados

### Número de Resultados

El parámetro `top_k` determina el número máximo de documentos a devolver:

- **Valor predeterminado**: 5
- **Impacto**: Un valor mayor puede proporcionar más contexto pero también más ruido

## Gestión de Metadatos

Los metadatos se almacenan en formato JSONB y típicamente incluyen:

- `name`: Nombre del archivo
- `file_id`: ID del archivo en Google Drive
- `chunk_index`: Índice del fragmento
- `total_chunks`: Número total de fragmentos
- `mime_type`: Tipo MIME del archivo original
- `last_modified`: Última fecha de modificación
- `checksum`: Hash MD5 del contenido del archivo para detectar cambios

## Consideraciones de Rendimiento

1. **Índices**:
   - Se utiliza un índice `ivfflat` para la búsqueda eficiente de vectores
   - El parámetro `lists = 100` en el índice es un compromiso entre velocidad y precisión

2. **Costes de Operación**:
   - Las búsquedas por similitud son operaciones computacionalmente intensivas
   - El tamaño de la base de datos afecta directamente al rendimiento

3. **Estrategias de Optimización**:
   - Limitar el número de documentos en la colección
   - Utilizar fragmentos de tamaño apropiado
   - Ajustar el umbral de similitud según necesidades

## Ejemplo de Uso

```python
from app.database.vector_store import VectorDatabase

# Inicializar la base de datos
db = VectorDatabase()

# Realizar una búsqueda por similitud
results = db.similarity_search(
    query_embedding=embedding, 
    top_k=5,
    threshold=0.1
)

# Procesar resultados
for result in results:
    print(f"Similitud: {result['similarity']}")
    print(f"Contenido: {result['content'][:100]}...")
    print(f"Archivo: {result['metadata']['name']}")

# Obtener fragmentos de un archivo
chunks = db.get_chunks_by_file_id("archivo_id_123")

# Eliminar un archivo y sus fragmentos
deleted_count = db.delete_chunks_by_file_id("archivo_id_123")
print(f"Se eliminaron {deleted_count} fragmentos")
```

## Problemas Comunes y Soluciones

### No se encuentran resultados relevantes

Si la función `similarity_search` no devuelve resultados:

1. **Verificar el umbral**: Reducir el valor de `threshold` (p.ej., a 0.05)
2. **Comprobar embeddings**: Verificar que los embeddings se generan correctamente
3. **Examinar los datos**: Asegurarse de que existen documentos relevantes en la base de datos

### Rendimiento lento en grandes colecciones

Para mejorar el rendimiento con grandes volúmenes de datos:

1. **Optimizar índices**: Ajustar los parámetros del índice `ivfflat`
2. **Reducir dimensión**: Considerar técnicas de reducción de dimensionalidad
3. **Particionar datos**: Dividir la colección en subcolecciones temáticas

### Errores en las funciones RPC

Si ocurren errores al llamar a las funciones RPC como `get_chunks_by_file_id` o `delete_chunks_by_file_id`:

1. **Verificar los nombres de los parámetros**: Asegurarse de que coincidan con los definidos en SQL
2. **Comprobar la existencia de las funciones**: Verificar que se hayan creado en la base de datos
3. **Validar permisos**: Verificar que el usuario tenga permisos para ejecutar funciones RPC 