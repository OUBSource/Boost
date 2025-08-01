import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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

# Templates are now in separate files in the templates/ directory

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
    
    return render_template('login.html')

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
    
    return render_template('register.html')

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
    
    return render_template('chat.html', messages=messages)

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