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