// Функция для форматирования времени
function formatTime(dateString) {
    const date = new Date(dateString);
    let hours = date.getHours();
    let minutes = date.getMinutes();
    hours = hours < 10 ? '0' + hours : hours;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return hours + ':' + minutes;
}

// Добавление нового сообщения в чат
function addMessage(message, isAuthor) {
    const messagesContainer = document.querySelector('.chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isAuthor ? 'sent' : 'received'}`;
    messageDiv.dataset.id = message.id;
    
    const messageInner = document.createElement('div');
    messageInner.className = 'message-inner';
    
    if (!isAuthor) {
        const usernameDiv = document.createElement('div');
        usernameDiv.className = 'message-username';
        usernameDiv.textContent = message.username;
        messageInner.appendChild(usernameDiv);
    }
    
    const contentDiv = document.createElement('div');
    contentDiv.textContent = message.content;
    messageInner.appendChild(contentDiv);
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(message.timestamp);
    
    if (isAuthor && message.is_read) {
        const checkIcon = document.createElement('i');
        checkIcon.className = 'fas fa-check-double';
        checkIcon.style = 'margin-left: 5px; color: #48BB78;';
        timeDiv.appendChild(checkIcon);
    }
    
    messageInner.appendChild(timeDiv);
    messageDiv.appendChild(messageInner);
    messagesContainer.appendChild(messageDiv);
    
    // Прокрутка к новому сообщению
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Загрузка сообщений
function loadMessages() {
    fetch('/get_messages')
        .then(response => response.json())
        .then(data => {
            if (data.messages && data.messages.length > 0) {
                const messagesContainer = document.querySelector('.chat-messages');
                const lastMessageId = messagesContainer.lastChild?.dataset?.id || 0;
                
                // Добавляем только новые сообщения
                data.messages.forEach(msg => {
                    if (msg.id > lastMessageId) {
                        addMessage(msg, msg.is_author);
                    }
                });
            }
        });
}

// Отправка сообщения
function sendMessage() {
    const input = document.querySelector('.message-input');
    const message = input.value.trim();
    
    if (message) {
        fetch('/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: message }),
            credentials: 'include'
        }).then(response => {
            if (response.ok) {
                input.value = '';
            }
        });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Загружаем сообщения при открытии страницы
    loadMessages();
    
    // Настройка отправки сообщений
    const messageForm = document.querySelector('.input-group');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });
        
        // Также отправка по нажатию Enter
        const messageInput = document.querySelector('.message-input');
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Проверка новых сообщений каждые 2 секунды
    setInterval(loadMessages, 2000);
}); 