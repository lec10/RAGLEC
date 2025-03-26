document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const queryInput = document.getElementById('query-input');
    const sendButton = document.getElementById('send-button');
    const responseContent = document.getElementById('response-content');
    const sourcesContent = document.getElementById('sources-content');
    const loadingIndicator = document.getElementById('loading');

    // API Endpoint - ajusta esto a tu configuración
    const apiEndpoint = '/api/query';

    // Formatear las fuentes para mostrarlas de forma legible
    function formatSources(sources) {
        if (!sources || sources.length === 0) {
            return '<div class="no-sources">No se encontraron fuentes relevantes.</div>';
        }

        return sources.map((source, index) => {
            // Obtener información del fragmento
            const fileName = source.file_name || 'Documento sin nombre';
            const chunkIndex = source.chunk_index !== undefined ? source.chunk_index + 1 : '?';
            const totalChunks = source.total_chunks || '?';
            const similarity = source.similarity ? (source.similarity * 100).toFixed(1) + '%' : '';

            // Crear elemento de fuente
            return `
                <div class="source-item">
                    <div class="source-title">
                        Documento ${index + 1}: ${fileName} 
                        (Fragmento ${chunkIndex} de ${totalChunks}) 
                        ${similarity ? `- Similitud: ${similarity}` : ''}
                    </div>
                    <div class="source-content">${source.content || 'No hay contenido disponible'}</div>
                </div>
            `;
        }).join('');
    }

    // Manejar la respuesta de la API
    function handleResponse(data) {
        // Ocultar el indicador de carga
        loadingIndicator.classList.add('hidden');
        
        if (data.error) {
            responseContent.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            return;
        }

        // Mostrar la respuesta
        responseContent.innerHTML = data.response || 'No se pudo generar una respuesta.';
        responseContent.classList.remove('response-placeholder');
        
        // Mostrar las fuentes
        if (data.sources) {
            sourcesContent.innerHTML = formatSources(data.sources);
            sourcesContent.classList.remove('sources-placeholder');
        } else {
            sourcesContent.innerHTML = '<div class="no-sources">No se encontraron fuentes relevantes.</div>';
        }
    }

    // Manejar errores
    function handleError(error) {
        console.error('Error:', error);
        loadingIndicator.classList.add('hidden');
        responseContent.innerHTML = `<div class="error">Error: No se pudo procesar la consulta. Por favor, intenta nuevamente.</div>`;
        sourcesContent.innerHTML = '<div class="no-sources">No hay fuentes disponibles debido a un error.</div>';
    }

    // Enviar consulta a la API
    async function sendQuery() {
        const query = queryInput.value.trim();
        
        if (!query) {
            alert('Por favor, ingresa una consulta.');
            return;
        }
        
        // Mostrar indicador de carga
        responseContent.innerHTML = '';
        sourcesContent.innerHTML = '';
        responseContent.classList.add('response-placeholder');
        sourcesContent.classList.add('sources-placeholder');
        loadingIndicator.classList.remove('hidden');
        
        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });
            
            if (!response.ok) {
                throw new Error(`Error de API: ${response.status}`);
            }
            
            const data = await response.json();
            handleResponse(data);
            
        } catch (error) {
            handleError(error);
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendQuery);
    
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            sendQuery();
        }
    });

    // Mensaje de bienvenida
    responseContent.innerHTML = 'Bienvenido a RAGLEC. Escribe tu consulta y presiona "Enviar" para obtener información de la base de conocimiento.';
}); 