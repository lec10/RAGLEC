-- Habilitar la extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear tabla para los documentos (con campo file_id incluido)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),
    file_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índice para búsquedas eficientes
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Crear índice para búsquedas por file_id
CREATE INDEX IF NOT EXISTS documents_file_id_idx ON documents(file_id);

-- Crear tabla para la información de los archivos
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mime_type TEXT,
    source TEXT DEFAULT 'google_drive',
    last_modified TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'processed',
    metadata JSONB
);

-- Crear función para búsqueda por similitud
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

-- Crear función para obtener todos los fragmentos de un archivo específico
-- Versión mejorada que maneja tanto el campo metadata->>'file_id' como la columna file_id
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
        documents.metadata->>'file_id' = file_id_param
        OR (documents.file_id = file_id_param AND documents.file_id IS NOT NULL)
    ORDER BY (documents.metadata->>'chunk_index')::INTEGER;
END;
$$;

-- Crear función para eliminar todos los fragmentos de un archivo
-- Versión mejorada para manejar correctamente el conteo y evitar errores
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

-- Crear tabla para el seguimiento de consultas
CREATE TABLE IF NOT EXISTS queries (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    response TEXT,
    sources JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_feedback INTEGER
);

-- Crear tabla para la verificación de salud
CREATE TABLE IF NOT EXISTS healthcheck (
    id SERIAL PRIMARY KEY,
    status TEXT DEFAULT 'ok',
    last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comentario de documentación
COMMENT ON DATABASE postgres IS 'Base de datos para el sistema RAG - Versión unificada que incluye todas las mejoras y correcciones';
COMMENT ON TABLE documents IS 'Almacena los fragmentos de documentos con sus embeddings y metadatos. Incluye columna file_id para optimizar búsquedas';
COMMENT ON TABLE files IS 'Almacena información sobre los archivos procesados';
COMMENT ON TABLE queries IS 'Registra las consultas realizadas y sus respuestas';
COMMENT ON TABLE healthcheck IS 'Utilizada para verificar el estado del sistema'; 