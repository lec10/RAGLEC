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

### Procesamiento de Consultas del Usuario

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

1. **Entrada de Consulta**:
   - El usuario introduce una consulta en la interfaz de chat
   - La consulta se envía al sistema RAG

2. **Vectorización de la Consulta**:
   - La consulta se envía al generador de embeddings
   - Se genera un vector de embedding para la consulta

3. **Búsqueda por Similitud**:
   - El vector se utiliza para buscar documentos similares en la base de datos
   - La búsqueda utiliza la función SQL personalizada `match_documents`
   - Se aplica un umbral de similitud (actualmente 0.1) para filtrar resultados irrelevantes
   - Se recuperan hasta 5 documentos (por defecto)

4. **Generación de Respuesta**:
   - Los documentos recuperados se combinan con la consulta para crear un prompt
   - El prompt se envía a la API de OpenAI (modelo gpt-4o-mini)
   - El LLM genera una respuesta basada en los documentos proporcionados

5. **Presentación al Usuario**:
   - La respuesta se muestra al usuario
   - Se muestran las fuentes utilizadas (metadatos de los documentos)
   - La consulta y respuesta se registran en la base de datos para análisis

## 3. Detalles Técnicos de los Datos

### Estructura de la Base de Datos

**Tabla: documents**
- `id`: TEXT (Primary Key) - Identificador único del fragmento
- `content`: TEXT - Contenido de texto del fragmento
- `metadata`: JSONB - Metadatos del fragmento
- `embedding`: VECTOR(1536) - Vector de embedding del fragmento
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
- `query`: TEXT - Consulta realizada
- `response`: TEXT - Respuesta generada
- `sources`: JSONB - Fuentes utilizadas
- `created_at`: TIMESTAMP - Fecha de la consulta

### Función SQL: match_documents

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

Esta función calcula la similitud coseno entre el embedding de la consulta y los embeddings almacenados, filtra según el umbral establecido, y devuelve los resultados ordenados por similitud.

## 4. Consideraciones sobre el Flujo de Datos

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