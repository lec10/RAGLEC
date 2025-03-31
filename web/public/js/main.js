document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const queryInput = document.getElementById('query-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const loadingIndicator = document.getElementById('loading');
    const newChatButton = document.getElementById('new-chat-button');
    const themeToggle = document.getElementById('theme-toggle');
    const userMessageTemplate = document.getElementById('user-message-template');
    const assistantMessageTemplate = document.getElementById('assistant-message-template');
    const thinkingTemplate = document.getElementById('thinking-template');
    
    // Variables globales
    let darkMode = localStorage.getItem('raglec-theme') === 'dark';
    let currentChatId = localStorage.getItem('raglec-current-chat-id') || generateUUID();
    let currentMessageId = 0;
    let chats = JSON.parse(localStorage.getItem('raglec-chats') || '{}');
    let conversationHistory = [];
    
    // API Endpoints
    const API_ENDPOINTS = {
        query: '/api/query',
        feedback: '/api/feedback'
    };
    
    // Inicialización
    // Iniciar tema según preferencia guardada
    document.body.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    themeToggle.innerHTML = darkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    
    // Registrar event listeners
    registerEventListeners();
    
    // Ajustar la altura del textarea
    queryInput.addEventListener('input', adjustTextareaHeight);
    
    // Funciones de inicialización
    function initApp() {
        try {
            // Inicializar las variables globales
            darkMode = localStorage.getItem('raglec-theme') === 'dark';
            currentChatId = localStorage.getItem('raglec-current-chat-id') || generateUUID();
            currentMessageId = 0;
            
            try {
                chats = JSON.parse(localStorage.getItem('raglec-chats') || '{}');
            } catch (e) {
                console.error('Error al cargar chats:', e);
                chats = {};
            }
            
            conversationHistory = [];
            
            // Aplicar tema
            document.body.setAttribute('data-theme', darkMode ? 'dark' : 'light');
            themeToggle.innerHTML = darkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
            
            // Ajustar altura del textarea
            queryInput.addEventListener('input', adjustTextareaHeight);
            
            // Enfocar el input al cargar
            queryInput.focus();
            
            // Registrar event listeners
            registerEventListeners();
            
            console.log('Aplicación inicializada correctamente');
        } catch (e) {
            console.error('Error al inicializar la aplicación:', e);
        }
    }
    
    // Inicializar la aplicación
    initApp();
    
    function registerEventListeners() {
        // Enviar consulta
        sendButton.addEventListener('click', handleSendQuery);
        
        // Enviar al presionar Enter (pero agregar nueva línea con Shift+Enter)
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendQuery();
            }
        });
        
        // Alternar tema oscuro/claro
        themeToggle.addEventListener('click', toggleDarkMode);
        
        // Nueva conversación
        newChatButton.addEventListener('click', createNewChat);
        
        // Delegación de eventos para mostrar/ocultar fuentes y thinking
        document.addEventListener('click', (e) => {
            // Botón para mostrar/ocultar fuentes
            if (e.target.closest('.toggle-sources')) {
                const button = e.target.closest('.toggle-sources');
                const sourcesContent = button.closest('.message-sources').querySelector('.sources-content');
                const icon = button.querySelector('.fa-chevron-down');
                
                sourcesContent.classList.toggle('hidden');
                if (sourcesContent.classList.contains('hidden')) {
                    icon.style.transform = 'rotate(0deg)';
                } else {
                    icon.style.transform = 'rotate(180deg)';
                }
            }
            
            // Botón para mostrar/ocultar thinking
            if (e.target.closest('.toggle-thinking')) {
                const button = e.target.closest('.toggle-thinking');
                const thinkingContent = button.closest('.thinking-section').querySelector('.thinking-content');
                const icon = button.querySelector('.fa-chevron-down');
                
                thinkingContent.classList.toggle('hidden');
                if (thinkingContent.classList.contains('hidden')) {
                    icon.style.transform = 'rotate(0deg)';
                } else {
                    icon.style.transform = 'rotate(180deg)';
                }
            }
            
            // Botones de acción de mensajes
            if (e.target.closest('.action-button')) {
                const button = e.target.closest('.action-button');
                const action = button.getAttribute('title');
                const message = button.closest('.message');
                
                switch (action) {
                    case 'Copiar':
                        copyToClipboard(message.querySelector('.message-content').textContent);
                        button.querySelector('i').className = 'fas fa-check';
                        setTimeout(() => {
                            button.querySelector('i').className = 'far fa-copy';
                        }, 2000);
                        break;
                    // Implementar más acciones según sea necesario
                }
            }
        });
    }
    
    // Funciones para manejar la interfaz
    function adjustTextareaHeight() {
        queryInput.style.height = 'auto';
        queryInput.style.height = (queryInput.scrollHeight) + 'px';
    }
    
    function toggleDarkMode() {
        darkMode = !darkMode;
        document.body.setAttribute('data-theme', darkMode ? 'dark' : 'light');
        themeToggle.innerHTML = darkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        localStorage.setItem('raglec-theme', darkMode ? 'dark' : 'light');
    }
    
    function toggleSidebar() {
        document.body.classList.toggle('sidebar-open');
    }
    
    function clearConversation() {
        if (confirm('¿Estás seguro de que deseas limpiar esta conversación?')) {
            chatMessages.innerHTML = '';
            
            // Limpiar la conversación actual
            if (currentChatId) {
                const currentChat = chats[currentChatId];
                if (currentChat) {
                    currentChat.messages = [];
                    saveChats();
                    updateChatTitle(currentChatId, 'Nueva conversación');
                }
            }
            
            conversationHistory = [];
        }
    }
    
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).catch(err => {
            console.error('Error al copiar texto: ', err);
        });
    }
    
    // Funciones para manejar las conversaciones
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, 
                v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    function createNewChat() {
        currentChatId = generateUUID();
        
        // Limpiar los mensajes actuales
        chatMessages.innerHTML = '';
        
        // Mostrar el mensaje de bienvenida
        document.querySelector('.welcome-message').classList.remove('hidden');
        
        // Limpiar el input
        queryInput.value = '';
        
        // Resetear currentMessageId
        currentMessageId = 0;
        
        // IMPORTANTE: Limpiar el historial de conversación
        conversationHistory = [];
        
        // Guardar chat en localStorage
        localStorage.setItem('raglec-current-chat-id', currentChatId);
        
        // Crear un nuevo chat vacío
        const newChat = {
            id: currentChatId,
            title: 'Nueva conversación',
            messages: [],
            created_at: new Date().toISOString()
        };
        
        // Guardar en chats
        chats[currentChatId] = newChat;
        saveChats();
    }
    
    function loadChat(chatId) {
        // Buscar el chat con ese ID
        const chat = chats[chatId];
        if (!chat) return;
        
        // Actualizar chat actual
        currentChatId = chatId;
        
        // Limpiar la interfaz
        chatMessages.innerHTML = '';
        
        // Ocultar el mensaje de bienvenida al cargar un chat
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        // Cargar mensajes
        conversationHistory = [...chat.messages];
        conversationHistory.forEach(item => {
            if (item.role === 'user') {
                addUserMessageToUI(item.content);
            } else if (item.role === 'assistant') {
                addAssistantMessageToUI(item.content, item.sources, item.queryId);
            }
        });
        
        // Actualizar el estado activo en la lista
        updateActiveChatInList();
        
        // Scroll al final
        scrollToBottom();
    }
    
    function updateChatTitle(chatId, newTitle) {
        // Encontrar el chat y actualizar su título
        const chatToUpdate = chats[chatId];
        if (chatToUpdate) {
            chatToUpdate.title = newTitle;
            saveChats();
            updateChatsList();
        }
    }
    
    function updateActiveChatInList() {
        // Quitar la clase active de todos los items
        const allItems = document.querySelectorAll('.chat-item');
        allItems.forEach(item => item.classList.remove('active'));
        
        // Añadir la clase active al item actual
        if (currentChatId) {
            const activeItem = document.querySelector(`.chat-item[data-chat-id="${currentChatId}"]`);
            if (activeItem) {
                activeItem.classList.add('active');
            }
        }
    }
    
    function updateChatsList() {
        // Verificar si el elemento existe
        const recentChats = document.getElementById('recent-chats');
        if (!recentChats) {
            console.error("Elemento #recent-chats no encontrado");
            return;
        }
        
        // Verificar si la plantilla existe
        const chatHistoryItemTemplate = document.getElementById('chat-history-item-template');
        if (!chatHistoryItemTemplate) {
            console.error("Plantilla #chat-history-item-template no encontrada");
            return;
        }
        
        // Limpiar la lista
        recentChats.innerHTML = '';
        
        // Añadir cada chat a la lista
        Object.values(chats).forEach(chat => {
            const chatItem = chatHistoryItemTemplate.content.cloneNode(true);
            const li = chatItem.querySelector('.chat-item');
            const titleSpan = chatItem.querySelector('.chat-title');
            
            li.dataset.chatId = chat.id;
            titleSpan.textContent = chat.title;
            
            if (chat.id === currentChatId) {
                li.classList.add('active');
            }
            
            recentChats.appendChild(li);
        });
    }
    
    // Funciones para manejar el almacenamiento
    function loadAllChats() {
        const savedChats = localStorage.getItem('raglec-all-chats');
        if (savedChats) {
            try {
                chats = JSON.parse(savedChats);
                updateChatsList();
                
                // NO cargar automáticamente la última conversación
                // Se comentan las siguientes líneas para evitar cargar conversaciones al inicio
                /*
                const lastActiveChat = localStorage.getItem('raglec-current-chat');
                if (lastActiveChat && Object.keys(chats).some(chatId => chatId === lastActiveChat)) {
                    loadChat(lastActiveChat);
                } else if (Object.keys(chats).length > 0) {
                    // Cargar el chat más reciente
                    loadChat(Object.keys(chats)[0]);
                }
                */
            } catch (e) {
                console.error('Error al cargar chats:', e);
                chats = {};
                localStorage.removeItem('raglec-all-chats');
            }
        }
    }
    
    function saveAllChats() {
        localStorage.setItem('raglec-all-chats', JSON.stringify(chats));
        localStorage.setItem('raglec-current-chat', currentChatId);
    }
    
    // Funciones para manejar mensajes
    function addUserMessage(text) {
        // Ocultar mensaje de bienvenida cuando se envía una pregunta
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        // Añadir a la interfaz
        const messageDiv = addUserMessageToUI(text);
        
        // Guardar en historiales
        const messageObj = {
            role: 'user',
            content: text
        };
        
        conversationHistory.push(messageObj);
        
        // Si es el primer mensaje, actualizar el título de la conversación
        const currentChat = chats[currentChatId];
        if (currentChat && (currentChat.messages.length === 0 || (currentChat.title === 'Nueva conversación' && text.length > 0))) {
            // Limitar el título a 30 caracteres
            const newTitle = text.length > 30 ? text.substring(0, 27) + '...' : text;
            updateChatTitle(currentChatId, newTitle);
        }
        
        // Actualizar el chat actual
        if (currentChatId) {
            const chat = chats[currentChatId];
            if (chat) {
                chat.messages = [...conversationHistory];
                saveChats();
            }
        }
        
        // Hacer scroll asegurando que el mensaje sea visible
        setTimeout(() => {
            if (messageDiv) {
                scrollToElement(messageDiv);
            } else {
                scrollToBottom();
            }
        }, 50);
        
        return messageDiv;
    }
    
    function addUserMessageToUI(text) {
        // Crear elemento de mensaje de usuario
        const userMessageNode = userMessageTemplate.content.cloneNode(true);
        const messageDiv = userMessageNode.querySelector('.message');
        messageDiv.querySelector('.message-content').textContent = text;
        
        // Agregar a la interfaz
        chatMessages.appendChild(messageDiv);
        
        return messageDiv;
    }
    
    function addAssistantMessage(text, sources) {
        // Añadir a la interfaz
        addAssistantMessageToUI(text, sources);
        
        // Guardar en el historial
        const messageObj = {
            role: 'assistant',
            content: text,
            sources: sources
        };
        
        conversationHistory.push(messageObj);
        
        // Actualizar el chat actual
        if (currentChatId) {
            const chat = chats[currentChatId];
            if (chat) {
                chat.messages = [...conversationHistory];
                saveChats();
            }
        }
    }
    
    function addAssistantMessageToUI(text, sources, queryId) {
        // Crear elemento de mensaje del asistente
        const assistantMessageNode = assistantMessageTemplate.content.cloneNode(true);
        const messageDiv = assistantMessageNode.querySelector('.message');
        messageDiv.querySelector('.message-content').textContent = text;
        
        // Formatear y mostrar fuentes si existen
        const sourcesContent = messageDiv.querySelector('.sources-content');
        const sourcesSection = messageDiv.querySelector('.message-sources');
        
        if (sources && sources.length > 0) {
            sourcesContent.innerHTML = formatSources(sources);
            
            // Modificar el toggle de fuentes
            const toggleButton = sourcesSection.querySelector('.toggle-sources');
            if (toggleButton) {
                // Estilo minimalista - no highlight por defecto
                
                // Asegurar que el evento click funcione directamente
                toggleButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log("Clic directo en toggle de fuentes");
                    
                    if (sourcesContent.classList.contains('hidden')) {
                        sourcesContent.classList.remove('hidden');
                        const icon = toggleButton.querySelector('.fa-chevron-down');
                        if (icon) icon.style.transform = 'rotate(180deg)';
                    } else {
                        sourcesContent.classList.add('hidden');
                        const icon = toggleButton.querySelector('.fa-chevron-down');
                        if (icon) icon.style.transform = 'rotate(0deg)';
                    }
                });
                
                // Mantener las fuentes ocultas inicialmente
                sourcesContent.classList.add('hidden');
                const icon = toggleButton.querySelector('.fa-chevron-down');
                if (icon) icon.style.transform = 'rotate(0deg)';
            }
        } else {
            sourcesSection.style.display = 'none';
        }
        
        // Configurar botones de feedback si hay un queryId
        if (queryId) {
            const thumbsUpButton = messageDiv.querySelector('.action-button[title="Me gusta"]');
            const thumbsDownButton = messageDiv.querySelector('.action-button[title="No me gusta"]');
            
            // Almacenar el ID de la consulta en el mensaje
            messageDiv.dataset.queryId = queryId;
            
            // Agregar listeners para los botones de feedback
            thumbsUpButton.addEventListener('click', function() {
                sendFeedback(queryId, 1);
                // Efecto visual para indicar la selección
                thumbsUpButton.classList.add('selected');
                thumbsDownButton.classList.remove('selected');
                
                // Cambiar la clase del icono de outline a solid
                thumbsUpButton.querySelector('i').classList.remove('far');
                thumbsUpButton.querySelector('i').classList.add('fas');
                
                // Asegurarse de que el otro botón tenga el icono outline
                thumbsDownButton.querySelector('i').classList.remove('fas');
                thumbsDownButton.querySelector('i').classList.add('far');
            });
            
            thumbsDownButton.addEventListener('click', function() {
                sendFeedback(queryId, -1);
                // Efecto visual para indicar la selección
                thumbsDownButton.classList.add('selected');
                thumbsUpButton.classList.remove('selected');
                
                // Cambiar la clase del icono de outline a solid
                thumbsDownButton.querySelector('i').classList.remove('far');
                thumbsDownButton.querySelector('i').classList.add('fas');
                
                // Asegurarse de que el otro botón tenga el icono outline
                thumbsUpButton.querySelector('i').classList.remove('fas');
                thumbsUpButton.querySelector('i').classList.add('far');
            });
        }
        
        // Agregar a la interfaz
        chatMessages.appendChild(messageDiv);
        
        // Asegurar scroll para ver todo el contenido
        setTimeout(() => {
            scrollToElement(messageDiv);
        }, 100);
    }
    
    function formatSources(sources) {
        if (!sources || sources.length === 0) {
            return '<div class="no-sources">No se encontraron fuentes relevantes.</div>';
        }
        
        console.log("Formateando fuentes:", sources);
        
        // Función para escapar HTML
        function escapeHTML(text) {
            if (!text) return '';
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
        
        // Formato HTML para mostrar las fuentes
        let sourcesHTML = '';
        
        sources.forEach((source, index) => {
            try {
                // Usar contenido completo sin cortar
                let content = source.content || '';
                
                // Escapar HTML para prevenir inyección de código
                const fileName = source.file_name ? escapeHTML(source.file_name) : 'Documento sin nombre';
                const chunkIndex = source.chunk_index !== undefined ? source.chunk_index + 1 : '?';
                const totalChunks = source.total_chunks || '?';
                content = escapeHTML(content);
                
                sourcesHTML += `
                    <div class="source-item" id="source-${index}">
                        <div class="source-title">
                            Documento ${index + 1}: ${fileName} 
                            (Fragmento ${chunkIndex} de ${totalChunks})
                        </div>
                        <div class="source-content">${content}</div>
                    </div>
                `;
            } catch (error) {
                console.error("Error al formatear fuente:", error, source);
                sourcesHTML += `
                    <div class="source-item error">
                        <div class="source-title">Error al mostrar esta fuente</div>
                    </div>
                `;
            }
        });
        
        console.log("HTML de fuentes generado para " + sources.length + " fuentes");
        
        return sourcesHTML;
    }
    
    function scrollToBottom() {
        // Obtener el contenedor de mensajes
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        // Scroll al final con un pequeño retraso para asegurar que el DOM se ha actualizado
        setTimeout(() => {
            try {
                // Primero intentar el método más compatible
                chatContainer.scrollTop = chatContainer.scrollHeight;
                
                // En algunos navegadores, puede ser útil este método alternativo
                if (chatContainer.scrollTop < chatContainer.scrollHeight - chatContainer.clientHeight) {
                    chatContainer.scrollTo({
                        top: chatContainer.scrollHeight,
                        behavior: 'auto'
                    });
                }
                
                console.log("scrollToBottom ejecutado");
            } catch (error) {
                console.error("Error en scrollToBottom:", error);
            }
        }, 50);
    }
    
    // Función mejorada para hacer scroll a un elemento específico
    function scrollToElement(element) {
        if (!element) return;
        
        try {
            // Hacer scroll inmediato para posicionar el elemento
            element.scrollIntoView({ block: 'end', behavior: 'auto' });
            
            // Obtener el contenedor de mensajes
            const container = document.getElementById('chat-messages');
            if (!container) return;
            
            // Calcular un espacio adicional para mejorar la visibilidad
            // Esto asegura que haya espacio para ver los elementos siguientes
            const additionalScroll = Math.min(150, container.clientHeight * 0.2);
            
            // Aplicar scroll adicional para mejorar la visibilidad
            setTimeout(() => {
                container.scrollTop = container.scrollTop + additionalScroll;
                console.log("Scroll aplicado a elemento:", element);
            }, 50);
        } catch (error) {
            console.error("Error al hacer scroll:", error);
            // Fallback a scroll básico en caso de error
            scrollToBottom();
        }
    }
    
    // Funciones para manejar consultas
    async function handleSendQuery() {
        const query = queryInput.value.trim();
        
        if (!query) {
            return;
        }
        
        // Limpiar el input y ajustar su altura
        queryInput.value = '';
        adjustTextareaHeight();
        
        // Añadir mensaje del usuario
        addUserMessage(query);
        
        // Hacer scroll explícito para mostrar el mensaje del usuario
        scrollToBottom();
        
        // Mostrar indicador de carga
        loadingIndicator.classList.remove('hidden');
        
        // Asegurar que el indicador de carga sea visible con scroll adicional
        setTimeout(() => {
            loadingIndicator.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 100);
        
        try {
            console.log("Enviando consulta:", query);
            // Enviar consulta a la API
            const response = await sendQuery(query);
            
            // Ocultar indicador de carga
            loadingIndicator.classList.add('hidden');
            
            console.log("Respuesta completa recibida:", response);
            
            // Depurar fuentes
            if (response.sources && response.sources.length > 0) {
                console.log("DEBUG DE FUENTES:");
                response.sources.forEach((src, idx) => {
                    console.log(`Fuente ${idx+1}:`, src);
                    console.log(` - Nombre archivo:`, src.file_name);
                    console.log(` - Índice de chunk:`, src.chunk_index);
                    console.log(` - Total de chunks:`, src.total_chunks);
                });
            }
            
            // Comprobar si hay error en la respuesta
            if (response.error) {
                console.error("Error recibido del API:", response.error);
                addSystemAlert(`Error: ${response.error}`);
                return;
            }
            
            // Comprobar si hay respuesta (lo que en el backend se llama "response")
            if (response.response) {
                // Crear elemento de mensaje del asistente
                const assistantMessageNode = assistantMessageTemplate.content.cloneNode(true);
                const messageDiv = assistantMessageNode.querySelector('.message');
                
                // Agregar a la interfaz ahora para poder hacer scroll y efectos de typing
                chatMessages.appendChild(messageDiv);
                
                // Efecto de typing para la respuesta
                await typewriterEffect(messageDiv.querySelector('.message-content'), response.response);
                
                // Guardar en el historial
                const messageObj = {
                    role: 'assistant',
                    content: response.response,
                    sources: response.sources,
                    query_id: response.query_id
                };
                
                conversationHistory.push(messageObj);
                
                // Formatear y mostrar fuentes si existen
                const sourcesContent = messageDiv.querySelector('.sources-content');
                if (response.sources && response.sources.length > 0) {
                    console.log("Mostrando fuentes:", response.sources);
                    sourcesContent.innerHTML = formatSources(response.sources);
                    // Encontrar section y toggle
                    const sourcesSection = messageDiv.querySelector('.message-sources');
                    const toggleButton = sourcesSection.querySelector('.toggle-sources');
                    
                    // Asegurar visibilidad
                    if (toggleButton) {
                        // Estilo minimalista - no highlight por defecto
                        
                        // Configurar evento click directamente
                        toggleButton.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log("Clic directo en toggle de fuentes (respuesta API)");
                            
                            if (sourcesContent.classList.contains('hidden')) {
                                sourcesContent.classList.remove('hidden');
                                const icon = toggleButton.querySelector('.fa-chevron-down');
                                if (icon) icon.style.transform = 'rotate(180deg)';
                            } else {
                                sourcesContent.classList.add('hidden');
                                const icon = toggleButton.querySelector('.fa-chevron-down');
                                if (icon) icon.style.transform = 'rotate(0deg)';
                            }
                        });
                        
                        // Mantener las fuentes ocultas inicialmente
                        sourcesContent.classList.add('hidden');
                        const icon = toggleButton.querySelector('.fa-chevron-down');
                        if (icon) icon.style.transform = 'rotate(0deg)';
                    }
                } else {
                    const sourcesSection = messageDiv.querySelector('.message-sources');
                    if (sourcesSection) sourcesSection.style.display = 'none';
                }
                
                // Configurar botones de feedback si hay un query_id
                if (response.query_id) {
                    const queryId = response.query_id;
                    const thumbsUpButton = messageDiv.querySelector('.action-button[title="Me gusta"]');
                    const thumbsDownButton = messageDiv.querySelector('.action-button[title="No me gusta"]');
                    
                    // Almacenar el ID de la consulta en el mensaje
                    messageDiv.dataset.queryId = queryId;
                    
                    console.log("Configurando feedback con query_id:", queryId);
                    
                    // Agregar listeners para los botones de feedback
                    thumbsUpButton.addEventListener('click', function() {
                        console.log("Enviando feedback positivo para queryId:", queryId);
                        sendFeedback(queryId, 1);
                        // Efecto visual para indicar la selección
                        thumbsUpButton.classList.add('selected');
                        thumbsDownButton.classList.remove('selected');
                        
                        // Cambiar la clase del icono de outline a solid
                        thumbsUpButton.querySelector('i').classList.remove('far');
                        thumbsUpButton.querySelector('i').classList.add('fas');
                        
                        // Asegurarse de que el otro botón tenga el icono outline
                        thumbsDownButton.querySelector('i').classList.remove('fas');
                        thumbsDownButton.querySelector('i').classList.add('far');
                    });
                    
                    thumbsDownButton.addEventListener('click', function() {
                        console.log("Enviando feedback negativo para queryId:", queryId);
                        sendFeedback(queryId, -1);
                        // Efecto visual para indicar la selección
                        thumbsDownButton.classList.add('selected');
                        thumbsUpButton.classList.remove('selected');
                        
                        // Cambiar la clase del icono de outline a solid
                        thumbsDownButton.querySelector('i').classList.remove('far');
                        thumbsDownButton.querySelector('i').classList.add('fas');
                        
                        // Asegurarse de que el otro botón tenga el icono outline
                        thumbsUpButton.querySelector('i').classList.remove('fas');
                        thumbsUpButton.querySelector('i').classList.add('far');
                    });
                } else {
                    console.warn("No se recibió query_id para configurar feedback");
                }
                
                // Actualizar el chat actual
                if (currentChatId) {
                    const chat = chats[currentChatId];
                    if (chat) {
                        chat.messages = [...conversationHistory];
                        saveChats();
                    }
                }
            } else {
                console.error('No se recibió respuesta válida:', response);
                addSystemAlert('No se pudo obtener una respuesta. Por favor, intenta nuevamente.');
            }
        } catch (error) {
            console.error('Error al enviar consulta:', error);
            loadingIndicator.classList.add('hidden');
            addSystemAlert(`Error al procesar la consulta: ${error.message}`);
        }
    }
    
    // Nueva función que añade un mensaje del asistente y devuelve el elemento DOM creado
    function addAssistantMessageAndReturn(text, sources) {
        const assistantMessageNode = assistantMessageTemplate.content.cloneNode(true);
        const messageDiv = assistantMessageNode.querySelector('.message');
        messageDiv.querySelector('.message-content').textContent = text;
        
        // Formatear y mostrar fuentes si existen
        const sourcesContent = messageDiv.querySelector('.sources-content');
        const sourcesSection = messageDiv.querySelector('.message-sources');
        
        if (sources && sources.length > 0) {
            sourcesContent.innerHTML = formatSources(sources);
            
            // Modificar el toggle de fuentes
            const toggleButton = sourcesSection.querySelector('.toggle-sources');
            if (toggleButton) {
                // Estilo minimalista - no highlight por defecto
                
                // Asegurar que el evento click funcione directamente
                toggleButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log("Clic directo en toggle de fuentes");
                    
                    if (sourcesContent.classList.contains('hidden')) {
                        sourcesContent.classList.remove('hidden');
                        const icon = toggleButton.querySelector('.fa-chevron-down');
                        if (icon) icon.style.transform = 'rotate(180deg)';
                    } else {
                        sourcesContent.classList.add('hidden');
                        const icon = toggleButton.querySelector('.fa-chevron-down');
                        if (icon) icon.style.transform = 'rotate(0deg)';
                    }
                });
                
                // Mantener las fuentes ocultas inicialmente
                sourcesContent.classList.add('hidden');
                const icon = toggleButton.querySelector('.fa-chevron-down');
                if (icon) icon.style.transform = 'rotate(0deg)';
            }
        } else {
            sourcesSection.style.display = 'none';
        }
        
        // Agregar a la interfaz
        chatMessages.appendChild(messageDiv);
        
        // También guardar en el historial
        const messageObj = {
            role: 'assistant',
            content: text,
            sources: sources
        };
        
        conversationHistory.push(messageObj);
        
        // Actualizar el chat actual
        if (currentChatId) {
            const chat = chats[currentChatId];
            if (chat) {
                chat.messages = [...conversationHistory];
                saveChats();
            }
        }
        
        return messageDiv;
    }
    
    // Efecto de escritura progresiva como Gemini
    async function typewriterEffect(element, text) {
        const minDelay = 10;  // Milisegundos mínimos entre caracteres
        const maxDelay = 30;  // Milisegundos máximos entre caracteres
        
        // Dividimos el texto por espacios para trabajar palabra por palabra
        const words = text.split(' ');
        let currentText = '';
        
        for (let i = 0; i < words.length; i++) {
            const word = words[i];
            currentText += (i > 0 ? ' ' : '') + word;
            element.textContent = currentText;
            
            // Hacer scroll si es necesario - cada 5 palabras para mayor fluidez
            if (i % 5 === 0) {
                const messageDiv = element.closest('.message');
                if (messageDiv) {
                    scrollToElement(messageDiv);
                }
            }
            
            // Pausa basada en la longitud de la palabra y signos de puntuación
            const delay = Math.max(
                minDelay,
                Math.min(maxDelay, word.length * 5)
            );
            
            // Pausa más larga después de puntuación
            if (word.match(/[.,;:?!]$/)) {
                await new Promise(r => setTimeout(r, delay * 3));
            } else {
                await new Promise(r => setTimeout(r, delay));
            }
        }
        
        // Scroll final para asegurar que se ve el mensaje completo
        const messageDiv = element.closest('.message');
        if (messageDiv) {
            scrollToElement(messageDiv);
            
            // Scroll adicional después de que se complete la respuesta para mostrar las fuentes
            setTimeout(() => {
                const sourcesSection = messageDiv.querySelector('.message-sources');
                if (sourcesSection && !sourcesSection.classList.contains('hidden')) {
                    const container = document.getElementById('chat-messages');
                    container.scrollTop += 200; // Scroll adicional para ver las fuentes
                }
            }, 500);
        }
    }
    
    async function sendQuery(query) {
        // Incluir el historial de conversación en la solicitud
        // Limitamos a los últimos 10 mensajes para no sobrecargar el contexto
        const recentHistory = conversationHistory.slice(-10);
        
        const response = await fetch(API_ENDPOINTS.query, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                query,
                conversation_history: recentHistory 
            }),
        });
        
        if (!response.ok) {
            throw new Error(`Error de API: ${response.status}`);
        }
        
        return await response.json();
    }

    // Función para manejar el feedback del usuario (thumbs up/down)
    async function sendFeedback(queryId, feedbackValue) {
        if (!queryId) {
            console.error("No se puede enviar feedback: queryId no disponible");
            showToast("No se puede enviar feedback: ID de consulta no disponible", "error");
            return;
        }
        
        console.log(`Enviando feedback ${feedbackValue} para consulta ${queryId}`);
        
        try {
            const response = await fetch(API_ENDPOINTS.feedback, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query_id: queryId,
                    feedback: feedbackValue // 1 para positivo, -1 para negativo
                })
            });
            
            // Verificar si la respuesta HTTP fue exitosa
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Respuesta de feedback:", data);
            
            if (data.success) {
                console.log("Feedback enviado correctamente");
                // Mostrar confirmación visual al usuario
                const feedbackMessage = feedbackValue === 1 ? 
                    "¡Gracias por tu feedback positivo!" : 
                    "Gracias por tu feedback. Trabajaremos para mejorar.";
                    
                // Mostrar un toast o notificación pequeña
                showToast(feedbackMessage, feedbackValue === 1 ? "success" : "warning");
            } else {
                console.error("Error al enviar feedback:", data.error);
                showToast(`No se pudo registrar tu feedback: ${data.error}`, "error");
            }
        } catch (error) {
            console.error("Error al enviar feedback:", error);
            showToast(`Error al enviar feedback: ${error.message}`, "error");
        }
    }

    // Función para mostrar un toast/notificación
    function showToast(message, type = "info") {
        // Verificar si ya existe un toast y eliminarlo
        const existingToast = document.querySelector('.feedback-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Crear el elemento toast
        const toast = document.createElement('div');
        toast.className = `feedback-toast ${type}`;
        toast.textContent = message;
        
        // Añadir al DOM
        document.body.appendChild(toast);
        
        // Mostrar con animación
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Ocultar después de 3 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            // Eliminar del DOM después de la animación
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }

    // Guardar chats en localStorage
    function saveChats() {
        localStorage.setItem('raglec-chats', JSON.stringify(chats));
    }

    // Función para mostrar una alerta del sistema
    function addSystemAlert(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'system-alert';
        alertDiv.textContent = message;
        chatMessages.appendChild(alertDiv);
        scrollToBottom();
        
        // Auto-remover después de un tiempo
        setTimeout(() => {
            alertDiv.classList.add('fade-out');
            setTimeout(() => alertDiv.remove(), 500);
        }, 5000);
    }
}); 