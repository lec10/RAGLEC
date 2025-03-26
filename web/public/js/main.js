document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const queryInput = document.getElementById('query-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-button');
    const chatMessages = document.getElementById('chat-messages');
    const loadingIndicator = document.getElementById('loading');
    const themeToggle = document.getElementById('theme-toggle');
    const menuToggle = document.getElementById('menu-toggle');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const newChatButton = document.getElementById('new-chat');
    const recentChatsList = document.getElementById('recent-chats');
    const userMessageTemplate = document.getElementById('user-message-template');
    const assistantMessageTemplate = document.getElementById('assistant-message-template');
    const thinkingTemplate = document.getElementById('thinking-template');
    const chatHistoryItemTemplate = document.getElementById('chat-history-item-template');
    
    // Estado de la aplicación
    let darkMode = false;
    let conversationHistory = []; // Historial de la conversación actual
    let allChats = []; // Almacena todas las conversaciones
    let currentChatId = null; // ID de la conversación actual
    
    // API Endpoint
    const apiEndpoint = '/api/query';

    // Inicialización
    initApp();
    
    // Funciones de inicialización
    function initApp() {
        // Determinar tema preferido
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            toggleDarkMode();
        }
        
        // Ajustar altura del textarea
        queryInput.addEventListener('input', adjustTextareaHeight);
        
        // Enfocar el input al cargar
        queryInput.focus();
        
        // Comprobar tema guardado
        const savedTheme = localStorage.getItem('raglec-theme');
        if (savedTheme === 'dark' && !darkMode) {
            toggleDarkMode();
        }
        
        // Cargar todas las conversaciones (solo para el menú lateral, no para mostrar)
        loadAllChats();
        
        // Crear una nueva sesión vacía sin cargar mensajes
        createEmptySession();
        
        // Registrar event listeners
        registerEventListeners();
    }
    
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
        
        // Alternar menú lateral
        menuToggle.addEventListener('click', toggleSidebar);
        sidebarOverlay.addEventListener('click', toggleSidebar);
        
        // Nueva conversación
        newChatButton.addEventListener('click', () => {
            createNewChat();
            toggleSidebar();
        });
        
        // Limpiar historial
        clearButton.addEventListener('click', clearConversation);
        
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
            
            // Botones de elemento del historial
            if (e.target.closest('.chat-item-button')) {
                const button = e.target.closest('.chat-item-button');
                const chatItem = button.closest('.chat-item');
                const chatId = chatItem.dataset.chatId;
                
                // Si no es la conversación actual, cargarla
                if (chatId !== currentChatId) {
                    loadChat(chatId);
                    toggleSidebar();
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
                const currentChat = allChats.find(chat => chat.id === currentChatId);
                if (currentChat) {
                    currentChat.messages = [];
                    saveAllChats();
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
    function generateUniqueId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    function createNewChat() {
        // Generar un nuevo ID único para este chat
        const chatId = generateUniqueId();
        
        // Crear un nuevo chat vacío
        const newChat = {
            id: chatId,
            title: 'Nueva conversación',
            messages: [],
            createdAt: new Date().toISOString()
        };
        
        // Añadir al principio de la lista
        allChats.unshift(newChat);
        
        // Limitar a 10 chats recientes
        if (allChats.length > 10) {
            allChats = allChats.slice(0, 10);
        }
        
        // Actualizar el almacenamiento
        saveAllChats();
        
        // Cargar este nuevo chat
        loadChat(chatId);
        
        // Actualizar la interfaz
        updateChatsList();
    }
    
    function loadChat(chatId) {
        // Buscar el chat con ese ID
        const chat = allChats.find(chat => chat.id === chatId);
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
                addAssistantMessageToUI(item.content, item.sources);
            }
        });
        
        // Actualizar el estado activo en la lista
        updateActiveChatInList();
        
        // Scroll al final
        scrollToBottom();
    }
    
    function updateChatTitle(chatId, newTitle) {
        // Encontrar el chat y actualizar su título
        const chatToUpdate = allChats.find(chat => chat.id === chatId);
        if (chatToUpdate) {
            chatToUpdate.title = newTitle;
            saveAllChats();
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
        // Limpiar la lista
        recentChatsList.innerHTML = '';
        
        // Añadir cada chat a la lista
        allChats.forEach(chat => {
            const chatItem = chatHistoryItemTemplate.content.cloneNode(true);
            const li = chatItem.querySelector('.chat-item');
            const titleSpan = chatItem.querySelector('.chat-title');
            
            li.dataset.chatId = chat.id;
            titleSpan.textContent = chat.title;
            
            if (chat.id === currentChatId) {
                li.classList.add('active');
            }
            
            recentChatsList.appendChild(li);
        });
    }
    
    // Funciones para manejar el almacenamiento
    function loadAllChats() {
        const savedChats = localStorage.getItem('raglec-all-chats');
        if (savedChats) {
            try {
                allChats = JSON.parse(savedChats);
                updateChatsList();
                
                // NO cargar automáticamente la última conversación
                // Se comentan las siguientes líneas para evitar cargar conversaciones al inicio
                /*
                const lastActiveChat = localStorage.getItem('raglec-current-chat');
                if (lastActiveChat && allChats.some(chat => chat.id === lastActiveChat)) {
                    loadChat(lastActiveChat);
                } else if (allChats.length > 0) {
                    // Cargar el chat más reciente
                    loadChat(allChats[0].id);
                }
                */
            } catch (e) {
                console.error('Error al cargar chats:', e);
                allChats = [];
                localStorage.removeItem('raglec-all-chats');
            }
        }
    }
    
    function saveAllChats() {
        localStorage.setItem('raglec-all-chats', JSON.stringify(allChats));
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
        addUserMessageToUI(text);
        
        // Guardar en historiales
        const messageObj = {
            role: 'user',
            content: text
        };
        
        conversationHistory.push(messageObj);
        
        // Si es el primer mensaje, actualizar el título de la conversación
        const currentChat = allChats.find(chat => chat.id === currentChatId);
        if (currentChat && (currentChat.messages.length === 0 || (currentChat.title === 'Nueva conversación' && text.length > 0))) {
            // Limitar el título a 30 caracteres
            const newTitle = text.length > 30 ? text.substring(0, 27) + '...' : text;
            updateChatTitle(currentChatId, newTitle);
        }
        
        // Actualizar el chat actual
        if (currentChatId) {
            const chat = allChats.find(chat => chat.id === currentChatId);
            if (chat) {
                chat.messages = [...conversationHistory];
                saveAllChats();
            }
        }
        
        scrollToBottom();
    }
    
    function addUserMessageToUI(text) {
        // Crear elemento de mensaje de usuario
        const userMessageNode = userMessageTemplate.content.cloneNode(true);
        const messageDiv = userMessageNode.querySelector('.message');
        messageDiv.querySelector('.message-content').textContent = text;
        
        // Agregar a la interfaz
        chatMessages.appendChild(messageDiv);
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
            const chat = allChats.find(chat => chat.id === currentChatId);
            if (chat) {
                chat.messages = [...conversationHistory];
                saveAllChats();
            }
        }
    }
    
    function addAssistantMessageToUI(text, sources) {
        // Crear elemento de mensaje del asistente
        const assistantMessageNode = assistantMessageTemplate.content.cloneNode(true);
        const messageDiv = assistantMessageNode.querySelector('.message');
        messageDiv.querySelector('.message-content').textContent = text;
        
        // Formatear y mostrar fuentes si existen
        const sourcesContent = messageDiv.querySelector('.sources-content');
        const sourcesSection = messageDiv.querySelector('.message-sources');
        
        if (sources && sources.length > 0) {
            sourcesContent.innerHTML = formatSources(sources);
            
            // Modificar el toggle de fuentes para hacerlo más visible
            const toggleButton = sourcesSection.querySelector('.toggle-sources');
            toggleButton.classList.add('highlight-sources');
            
            // Mostrar inicialmente las fuentes para que sean evidentes
            sourcesContent.classList.remove('hidden');
            toggleButton.querySelector('.fa-chevron-down').style.transform = 'rotate(180deg)';
        } else {
            sourcesSection.style.display = 'none';
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

        return sources.map((source, index) => {
            const fileName = source.file_name || 'Documento sin nombre';
            const chunkIndex = source.chunk_index !== undefined ? source.chunk_index + 1 : '?';
            const totalChunks = source.total_chunks || '?';
            const similarity = source.similarity ? (source.similarity * 100).toFixed(1) + '%' : '';

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
    
    function scrollToBottom() {
        // Asegurarse de que se ejecuta después de que el DOM se ha actualizado
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 10);
    }
    
    // Nueva función para hacer scroll directamente a un elemento específico
    function scrollToElement(element) {
        if (element) {
            // Usar 'end' en lugar de 'center' para asegurar que se vea todo el elemento
            element.scrollIntoView({ behavior: 'smooth', block: 'end' });
            
            // Añadir scroll adicional para ver completamente el elemento y cualquier contenido que siga
            setTimeout(() => {
                const container = document.getElementById('chat-messages');
                container.scrollTop += 150; // Scroll adicional para ver más contenido
            }, 300);
        }
    }
    
    // Funciones para manejar consultas
    async function handleSendQuery() {
        const query = queryInput.value.trim();
        
        if (!query) {
            queryInput.focus();
            return;
        }
        
        // Limpiar input y resetear altura
        addUserMessage(query);
        queryInput.value = '';
        queryInput.style.height = 'auto';
        
        // Mostrar indicador de carga y asegurar que está visible
        chatMessages.appendChild(loadingIndicator);
        loadingIndicator.classList.remove('hidden');
        
        // Hacer scroll directamente al indicador de carga para asegurarse que sea visible
        scrollToElement(loadingIndicator);
        
        // También forzar el scroll al final por si acaso
        scrollToBottom();
        
        // Desactivar el botón de enviar mientras se procesa
        sendButton.disabled = true;
        
        try {
            const response = await sendQuery(query);
            loadingIndicator.classList.add('hidden');
            // Mover el indicador de carga fuera del flujo de mensajes
            document.querySelector('.chat-container').appendChild(loadingIndicator);
            sendButton.disabled = false;
            
            // Mostrar respuesta
            if (response.error) {
                const errorMessage = addAssistantMessageAndReturn(`Error: ${response.error}`, []);
                // Hacer scroll al mensaje de error
                scrollToElement(errorMessage);
            } else {
                // Crear el mensaje del asistente vacío primero
                const assistantMessageNode = assistantMessageTemplate.content.cloneNode(true);
                const messageDiv = assistantMessageNode.querySelector('.message');
                const messageContent = messageDiv.querySelector('.message-content');
                messageContent.textContent = "";
                
                // Formatear y mostrar fuentes si existen
                const sourcesContent = messageDiv.querySelector('.sources-content');
                if (response.sources && response.sources.length > 0) {
                    sourcesContent.innerHTML = formatSources(response.sources);
                } else {
                    const sourcesSection = messageDiv.querySelector('.message-sources');
                    sourcesSection.style.display = 'none';
                }
                
                // Agregar a la interfaz
                chatMessages.appendChild(messageDiv);
                
                // Hacer scroll para mostrar el mensaje vacío
                scrollToElement(messageDiv);
                
                // Mostrar el texto progresivamente
                await typewriterEffect(messageContent, response.response);
                
                // Guardar en historial una vez que está completo
                const messageObj = {
                    role: 'assistant',
                    content: response.response,
                    sources: response.sources
                };
                
                conversationHistory.push(messageObj);
                
                // Actualizar el chat actual
                if (currentChatId) {
                    const chat = allChats.find(chat => chat.id === currentChatId);
                    if (chat) {
                        chat.messages = [...conversationHistory];
                        saveAllChats();
                    }
                }
            }
        } catch (error) {
            loadingIndicator.classList.add('hidden');
            // Mover el indicador de carga fuera del flujo de mensajes
            document.querySelector('.chat-container').appendChild(loadingIndicator);
            sendButton.disabled = false;
            
            const errorMessage = addAssistantMessageAndReturn(`Error: No se pudo procesar tu consulta. Por favor, intenta nuevamente.`, []);
            // Hacer scroll al mensaje de error
            scrollToElement(errorMessage);
            
            console.error('Error:', error);
        }
        
        // Enfocar el input nuevamente
        queryInput.focus();
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
            
            // Modificar el toggle de fuentes para hacerlo más visible
            const toggleButton = sourcesSection.querySelector('.toggle-sources');
            toggleButton.classList.add('highlight-sources');
            
            // Mostrar inicialmente las fuentes para que sean evidentes
            sourcesContent.classList.remove('hidden');
            toggleButton.querySelector('.fa-chevron-down').style.transform = 'rotate(180deg)';
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
            const chat = allChats.find(chat => chat.id === currentChatId);
            if (chat) {
                chat.messages = [...conversationHistory];
                saveAllChats();
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
        
        return await response.json();
    }

    // Nueva función para crear una sesión vacía al inicio
    function createEmptySession() {
        // Generar un ID para la sesión actual, pero no cargar contenido
        currentChatId = generateUniqueId();
        
        // Asegurarse de que el área de mensajes esté vacía
        chatMessages.innerHTML = '';
        conversationHistory = [];
        
        // Mostrar mensaje de bienvenida (asegurarse de que sea visible)
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'block';
        }
    }
}); 