import os
import re
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Инициализация приложения
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boost_messenger.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

db = SQLAlchemy(app)

# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='author', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)

# Валидация данных
def is_valid_username(username):
    if len(username) < 3 or len(username) > 20:
        return False
    if re.search(r'[\s\u180E\u200B-\u200D\u2060\uFEFF]', username):
        return False
    return True

def is_valid_password(password):
    if len(password) < 5 or len(password) > 50:
        return False
    if re.search(r'[\s\u180E\u200B-\u200D\u2060\uFEFF]', password):
        return False
    return True

# HTML шаблоны
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boost Messenger</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        :root {
            --primary: #6C63FF;
            --primary-dark: #564FD9;
            --secondary: #FF6584;
            --dark: #2D3748;
            --light: #F7FAFC;
            --gray: #E2E8F0;
            --success: #48BB78;
            --danger: #F56565;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #f8f9fa;
            color: var(--dark);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 15px;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            padding: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            display: flex;
            align-items: center;
        }
        
        .logo i {
            margin-right: 10px;
            color: var(--secondary);
        }
        
        .nav-links {
            display: flex;
            list-style: none;
        }
        
        .nav-links li {
            margin-left: 1.5rem;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            padding: 0.5rem 1rem;
            border-radius: 4px;
        }
        
        .nav-links a:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        /* Chat Interface */
        .chat-container {
            display: flex;
            height: calc(100vh - 70px);
            margin-top: 70px;
        }
        
        .chat-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: #F7FAFC;
        }
        
        .chat-header {
            padding: 1rem;
            background: white;
            border-bottom: 1px solid var(--gray);
            display: flex;
            align-items: center;
        }
        
        .chat-header-avatar {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            object-fit: cover;
            margin-right: 1rem;
        }
        
        .chat-header-info h4 {
            font-size: 1.1rem;
            margin-bottom: 0.2rem;
        }
        
        .chat-header-info p {
            font-size: 0.8rem;
            color: #718096;
        }
        
        .online-status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--success);
            margin-right: 5px;
        }
        
        .chat-messages {
            flex: 1;
            padding: 1rem;
            overflow-y: auto;
        }
        
        .message {
            margin-bottom: 1rem;
            max-width: 70%;
            position: relative;
        }
        
        .message-inner {
            padding: 0.8rem 1rem;
            border-radius: 12px;
            position: relative;
            word-wrap: break-word;
        }
        
        .received .message-inner {
            background: white;
            border-top-left-radius: 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        .sent {
            margin-left: auto;
        }
        
        .sent .message-inner {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border-top-right-radius: 0;
        }
        
        .message-time {
            font-size: 0.7rem;
            color: #A0AEC0;
            margin-top: 0.3rem;
            text-align: right;
        }
        
        .sent .message-time {
            color: rgba(255, 255, 255, 0.7);
        }
        
        .message-username {
            font-weight: 600;
            margin-bottom: 0.3rem;
            font-size: 0.9rem;
        }
        
        .chat-input {
            padding: 1rem;
            background: white;
            border-top: 1px solid var(--gray);
        }
        
        .input-group {
            display: flex;
        }
        
        .message-input {
            flex: 1;
            padding: 0.8rem 1rem;
            border: 1px solid var(--gray);
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .message-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.2);
        }
        
        .send-btn {
            margin-left: 1rem;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        /* Auth Forms */
        .auth-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 2rem;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        .auth-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 450px;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .auth-card:hover {
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
        }
        
        .auth-header {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            padding: 1.5rem;
            text-align: center;
        }
        
        .auth-header h2 {
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
        
        .auth-body {
            padding: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--dark);
        }
        
        .form-control {
            width: 100%;
            padding: 0.8rem 1rem;
            border: 1px solid var(--gray);
            border-radius: 6px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.2);
        }
        
        .btn {
            display: inline-block;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            text-decoration: none;
        }
        
        .btn:hover {
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .btn-block {
            display: block;
            width: 100%;
        }
        
        .text-center {
            text-align: center;
        }
        
        .mt-3 {
            margin-top: 1rem;
        }
        
        .alert {
            padding: 0.8rem 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
        }
        
        .alert-success {
            background-color: #C6F6D5;
            color: #22543D;
        }
        
        .alert-danger {
            background-color: #FED7D7;
            color: #742A2A;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.3s ease forwards;
        }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
    
    <script>
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
    </script>
</body>
</html>
'''

LOGIN_TEMPLATE = BASE_TEMPLATE.replace(
    '{% block content %}{% endblock %}',
    '''
    <div class="auth-container">
        <div class="auth-card fade-in">
            <div class="auth-header">
                <h2><i class="fas fa-sign-in-alt"></i> Вход в Boost</h2>
                <p>Войдите в свой аккаунт</p>
            </div>
            <div class="auth-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label for="username">Имя пользователя</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Пароль</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-block">Войти</button>
                </form>
                
                <div class="text-center mt-3">
                    <p>Ещё нет аккаунта? <a href="/register" style="color: var(--primary); font-weight: 600;">Зарегистрируйтесь</a></p>
                </div>
            </div>
        </div>
    </div>
    '''
)

REGISTER_TEMPLATE = BASE_TEMPLATE.replace(
    '{% block content %}{% endblock %}',
    '''
    <div class="auth-container">
        <div class="auth-card fade-in">
            <div class="auth-header">
                <h2><i class="fas fa-user-plus"></i> Регистрация</h2>
                <p>Создайте новый аккаунт</p>
            </div>
            <div class="auth-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST" action="/register">
                    <div class="form-group">
                        <label for="username">Имя пользователя</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                        <small class="text-muted">От 3 до 20 символов, без пробелов</small>
                    </div>
                    <div class="form-group">
                        <label for="password">Пароль</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                        <small class="text-muted">Минимум 5 символов, без пробелов</small>
                    </div>
                    <div class="form-group">
                        <label for="confirm_password">Подтвердите пароль</label>
                        <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                    </div>
                    <button type="submit" class="btn btn-block">Зарегистрироваться</button>
                </form>
                
                <div class="text-center mt-3">
                    <p>Уже есть аккаунт? <a href="/login" style="color: var(--primary); font-weight: 600;">Войдите</a></p>
                </div>
            </div>
        </div>
    </div>
    '''
)

CHAT_TEMPLATE = BASE_TEMPLATE.replace(
    '{% block content %}{% endblock %}',
    '''
    <div class="header">
        <div class="container header-content">
            <div class="logo">
                <i class="fas fa-bolt"></i>
                <span>Boost Messenger</span>
            </div>
            <ul class="nav-links">
                <li><a href="/chat"><i class="fas fa-comment-alt"></i> Общий чат</a></li>
                <li><a href="/logout"><i class="fas fa-sign-out-alt"></i> Выйти</a></li>
            </ul>
        </div>
    </div>

    <div class="container chat-container">
        <!-- Основное окно чата -->
        <div class="chat-main">
            <div class="chat-header">
                <img src="/static/default-avatar.png" alt="Avatar" class="chat-header-avatar">
                <div class="chat-header-info">
                    <h4>Общий чат</h4>
                    <p><span class="online-status"></span> Онлайн</p>
                </div>
            </div>
            
            <div class="chat-messages">
                {% for message in messages %}
                <div class="message {% if message.user_id == session.user_id %}sent{% else %}received{% endif %}" data-id="{{ message.id }}">
                    <div class="message-inner">
                        {% if message.user_id != session.user_id %}
                        <div class="message-username">{{ message.author.username }}</div>
                        {% endif %}
                        <div>{{ message.content }}</div>
                        <div class="message-time">
                            {{ message.timestamp.strftime('%H:%M') }}
                            {% if message.user_id == session.user_id and message.is_read %}
                            <i class="fas fa-check-double" style="margin-left: 5px; color: #48BB78;"></i>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <div class="chat-input">
                <form class="input-group">
                    <input type="text" class="message-input" placeholder="Напишите сообщение..." autocomplete="off">
                    <button type="submit" class="send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </form>
            </div>
        </div>
    </div>
    '''
)

# Маршруты приложения
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('login'))
        
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        user.online = True
        user.last_seen = datetime.utcnow()
        db.session.commit()
        
        return redirect(url_for('chat'))
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        
        if not is_valid_username(username):
            flash('Имя пользователя должно быть от 3 до 20 символов и не содержать пробелов', 'danger')
            return redirect(url_for('register'))
        
        if not is_valid_password(password):
            flash('Пароль должен быть от 5 до 50 символов и не содержать пробелов', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Это имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            online=True,
            last_seen=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Обновляем статус пользователя
    user = User.query.get(session['user_id'])
    user.online = True
    user.last_seen = datetime.utcnow()
    db.session.commit()
    
    # Получаем сообщения
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    
    return render_template_string(CHAT_TEMPLATE, messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'status': 'error', 'message': 'No content provided'}), 400
    
    new_message = Message(
        content=data['content'],
        user_id=session['user_id'],
        timestamp=datetime.utcnow()
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/get_messages')
def get_messages():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'is_author': msg.user_id == session['user_id'],
        'is_read': msg.is_read,
        'username': msg.author.username
    } for msg in messages]
    
    return jsonify({
        'status': 'success',
        'messages': messages_data
    })

@app.route('/logout')
def logout():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.online = False
            user.last_seen = datetime.utcnow()
            db.session.commit()
        
        session.clear()
    
    return redirect(url_for('login'))

# Создаем папку для статических файлов, если её нет
if not os.path.exists('static'):
    os.makedirs('static')

# Инициализация базы данных
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=11436, debug=True)