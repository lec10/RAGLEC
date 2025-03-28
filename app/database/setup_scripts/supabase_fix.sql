-- Corregir la función de eliminación de fragmentos que tiene un error
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
    WHERE metadata->>'file_id' = file_id;
    
    -- Luego eliminar sin usar RETURNING
    DELETE FROM documents
    WHERE metadata->>'file_id' = file_id;

    RETURN deleted_count;
END;
$$;

-- Corregir la función get_chunks_by_file_id para resolver ambigüedad de nombres
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