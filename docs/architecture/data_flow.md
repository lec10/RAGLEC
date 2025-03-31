# Flujo de Datos

Este documento describe en detalle cómo fluyen los datos a través de los diferentes componentes del sistema RAGLEC.

## 1. Procesamiento de Documentos

### Flujo de Ingesta de Documentos

```
+-------------+     +---------------+     +----------------+     +---------------+
|             |     |               |     |                |     |               |
| Google      |---->| Document      |---->| Embedding      |---->| Vector        |
| Drive       |     | Processor     |     | Generator      |     | Database      |
|             |     |               |     |                |     |               |
+-------------+     +---------------+     +----------------+     +---------------+
```

1. **Detección del Documento**:
   - El monitor de Google Drive detecta un nuevo archivo o cambios en un archivo existente
   - Se obtiene información básica del archivo (ID, nombre, tipo MIME)

2. **Descarga y Extracción**:
   - El archivo se descarga temporalmente
   - El procesador de documentos extrae el texto según el formato

3. **Segmentación en Fragmentos**:
   - El texto se divide en fragmentos de aproximadamente 1000 caracteres con 200 caracteres de superposición
   - Cada fragmento recibe un ID único y metadata (índice, total de fragmentos, etc.)

4. **Generación de Embeddings**:
   - Cada fragmento se envía a la API de OpenAI para generar un vector de embedding
   - Los embeddings tienen una dimensión de 1536 (text-embedding-3-small)

5. **Almacenamiento en Base de Datos**:
   - Cada fragmento se guarda en la tabla 'documents' con:
     - Identificador único
     - Contenido de texto
     - Vector de embedding
     - Metadata (nombre de archivo, ID de archivo, índice, etc.)
   - Se actualiza la información del archivo en la tabla 'files'

## 2. Flujo de Consultas

### Procesamiento de Consultas del Usuario (CLI)

```
+-------------+     +---------------+     +----------------+     +---------------+     +----------------+
|             |     |               |     |                |     |               |     |                |
| Chat        |---->| RAG Query     |---->| Embedding      |---->| Vector        |---->| OpenAI         |
| Interface   |     | System        |     | Generator      |     | Database      |     | LLM            |
|             |     |               |     |                |     |               |     |                |
+-------------+     +---------------+     +----------------+     +---------------+     +----------------+
      ^                                                                                       |
      |                                                                                       |
      +---------------------------------------------------------------------------------------+
```

### Procesamiento de Consultas del Usuario (Web)

```
+-------------+     +---------------+     +----------------+     +---------------+     +----------------+
|             |     |               |     |                |     |               |     |                |
| Web         |---->| API           |---->| RAG Query      |---->| Vector        |---->| OpenAI         |
| Interface   |     | Endpoint      |     | System         |     | Database      |     | LLM            |
|             |     |               |     |                |     |               |     |                |
+-------------+     +---------------+     +----------------+     +---------------+     +----------------+
      ^                                                                                       |
      |                                                                                       |
      +---------------------------------------------------------------------------------------+
```

1. **Entrada de Consulta**:
   - El usuario introduce una consulta en la interfaz de chat (CLI o web)
   - La consulta se envía al sistema RAG

2. **Vectorización de la Consulta**:
   - La consulta se envía al generador de embeddings
   - Se genera un vector de embedding para la consulta

3. **Búsqueda por Similitud**:
   - El vector se utiliza para buscar documentos similares en la base de datos
   - La búsqueda utiliza la función SQL personalizada `match_documents`
   - Se aplica un umbral de similitud (configurable) para filtrar resultados irrelevantes
   - Se recuperan hasta 5 documentos (por defecto)

4. **Generación de Respuesta**:
   - Los documentos recuperados se combinan con la consulta para crear un prompt
   - El prompt se envía a la API de OpenAI (modelo gpt-4o-mini)
   - El LLM genera una respuesta basada en los documentos proporcionados

5. **Presentación al Usuario**:
   - La respuesta se muestra al usuario en la interfaz correspondiente
   - Se muestran las fuentes utilizadas (metadatos de los documentos)
   - La consulta y respuesta se registran en la base de datos para análisis

## 3. Flujo de Datos Web

### Interacción con la Interfaz Web

1. **Solicitud del Usuario**:
   - El usuario accede a la interfaz web a través de un navegador
   - La aplicación web se carga desde el servidor de Vercel

2. **Envío de Consulta**:
   - El usuario introduce una consulta en la interfaz
   - La aplicación web envía la consulta al backend mediante una solicitud HTTP

3. **Procesamiento de la Consulta**:
   - El backend procesa la consulta utilizando el sistema RAG
   - Se genera una respuesta como se describió anteriormente

4. **Respuesta al Usuario**:
   - La respuesta se envía de vuelta a la aplicación web
   - La interfaz muestra la respuesta y las fuentes al usuario
   - La aplicación web puede mostrar elementos visuales adicionales (citas, enlaces, etc.)

## 4. Detalles Técnicos de los Datos

### Estructura de la Base de Datos

**Tabla: documents**
- `id`: TEXT (Primary Key) - Identificador único del fragmento
- `content`: TEXT - Contenido de texto del fragmento
- `metadata`: JSONB - Metadatos del fragmento
- `embedding`: VECTOR(1536) - Vector de embedding del fragmento
- `file_id`: TEXT - Identificador del archivo al que pertenece el fragmento (referencia a la tabla 'files')
- `created_at`: TIMESTAMP - Fecha de creación
- `updated_at`: TIMESTAMP - Fecha de última actualización

**Tabla: files**
- `id`: TEXT (Primary Key) - ID de Google Drive del archivo
- `name`: TEXT - Nombre del archivo
- `mime_type`: TEXT - Tipo MIME del archivo
- `source`: TEXT - Fuente del archivo (default: 'google_drive')
- `last_modified`: TIMESTAMP - Fecha de última modificación
- `processed_at`: TIMESTAMP - Fecha de procesamiento
- `status`: TEXT - Estado del procesamiento
- `metadata`: JSONB - Metadatos adicionales

**Tabla: queries**
- `id`: SERIAL (Primary Key) - Identificador único de la consulta
- `query`: TEXT - Consulta realizada
- `response`: TEXT - Respuesta generada
- `sources`: JSONB - Fuentes utilizadas
- `created_at`: TIMESTAMP - Fecha de la consulta
- `user_feedback`: INTEGER - Valoración opcional del usuario

**Tabla: healthcheck**
- `id`: SERIAL (Primary Key) - Identificador único
- `status`: TEXT - Estado de salud del sistema
- `last_check`: TIMESTAMP - Última verificación de salud

### Funciones SQL

La función `match_documents` implementa la búsqueda por similitud coseno:

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

Función `get_chunks_by_file_id` para obtener los fragmentos de un archivo:

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

Función `delete_chunks_by_file_id` para eliminar los fragmentos de un archivo:

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

## 5. Consideraciones sobre el Flujo de Datos

### Puntos Críticos

1. **Generación de Embeddings**:
   - Es uno de los procesos más costosos en términos de recursos
   - Se realizan llamadas a la API de OpenAI, con costes asociados
   - Actualmente no se implementa caché de vectores para consultas frecuentes

2. **Umbral de Similitud**:
   - Un umbral demasiado alto puede filtrar documentos relevantes
   - Un umbral demasiado bajo puede incluir documentos irrelevantes
   - Según las pruebas, un umbral de 0.1 ofrece buen balance para los documentos actuales

3. **Tamaño de los Fragmentos**:
   - Fragmentos muy pequeños pueden perder contexto
   - Fragmentos muy grandes pueden diluir la relevancia
   - El tamaño actual (1000 caracteres) es un compromiso

4. **Interfaz Web**:
   - La latencia de la API puede afectar la experiencia del usuario
   - Es necesario manejar adecuadamente los errores y estados de carga
   - La interfaz debe ser responsiva y accesible desde diferentes dispositivos

### Optimizaciones Futuras

1. **Caché de Consultas Frecuentes**:
   - Almacenar resultados de consultas comunes
   - Reducir tiempo de respuesta y costes de API

2. **Indexación Avanzada**:
   - Implementar índices más eficientes para grandes volúmenes de documentos
   - Considerar técnicas como HNSW para búsqueda aproximada más rápida

3. **Procesamiento Paralelo**:
   - Paralelizar la generación de embeddings para múltiples fragmentos
   - Reducir tiempo de procesamiento para documentos grandes

4. **API RESTful Completa**:
   - Desarrollar una API completa para integración con otras aplicaciones
   - Implementar autenticación y limitación de tasa 