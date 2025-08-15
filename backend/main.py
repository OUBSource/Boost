import os
import re
import jwt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Инициализация приложения
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boost_messenger.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'boost-messenger-jwt-secret-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

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

# JWT Helper Functions
def create_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Invalid or expired token'}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated

# API Routes
@app.route('/check_auth')
@token_required
def check_auth():
    return jsonify({
        'authenticated': True,
        'username': request.current_user['username']
    })

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'status': 'error', 'message': 'Неверное имя пользователя или пароль'}), 401
    
    user.online = True
    user.last_seen = datetime.now()
    db.session.commit()
    
    token = create_token(user.id, user.username)
    
    return jsonify({
        'status': 'success', 
        'message': 'Login successful',
        'token': token,
        'username': user.username
    })

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    confirm_password = request.form['confirm_password'].strip()
    
    if not is_valid_username(username):
        return jsonify({'status': 'error', 'message': 'Имя пользователя должно быть от 3 до 20 символов и не содержать пробелов'}), 400
    
    if not is_valid_password(password):
        return jsonify({'status': 'error', 'message': 'Пароль должен быть от 5 до 50 символов и не содержать пробелов'}), 400
    
    if password != confirm_password:
        return jsonify({'status': 'error', 'message': 'Пароли не совпадают'}), 400
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'status': 'error', 'message': 'Это имя пользователя уже занято'}), 400
    
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        online=True,
        last_seen=datetime.now()
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Регистрация прошла успешно! Теперь вы можете войти.'})

@app.route('/send_message', methods=['POST'])
@token_required
def send_message():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'status': 'error', 'message': 'No content provided'}), 400
    
    new_message = Message(
        content=data['content'],
        user_id=request.current_user['user_id'],
        timestamp=datetime.utcnow()
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/get_messages')
@token_required
def get_messages():
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'is_author': msg.user_id == request.current_user['user_id'],
        'is_read': msg.is_read,
        'username': msg.author.username
    } for msg in messages]
    
    return jsonify({
        'status': 'success',
        'messages': messages_data
    })

@app.route('/logout')
@token_required
def logout():
    user = User.query.get(request.current_user['user_id'])
    if user:
        user.online = False
        user.last_seen = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Logged out successfully'})

# Serve static files from Flask
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)

# Создаем папку для статических файлов, если её нет
if not os.path.exists('static'):
    os.makedirs('static')

# Инициализация базы данных
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8300, debug=True)