// Authentication and navigation handling
let currentUser = null;
let authToken = null;

// API base URL - change this to match your Flask server
const API_BASE_URL = 'http://127.0.0.1:11436';

// Helper function to get auth headers
function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    return headers;
}

// Show login form
function showLogin() {
    document.getElementById('login-form').style.display = 'flex';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('chat-interface').style.display = 'none';
    clearAlerts();
}

// Show register form
function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'flex';
    document.getElementById('chat-interface').style.display = 'none';
    clearAlerts();
}

// Show chat interface
function showChat() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('chat-interface').style.display = 'block';
}

// Clear all alerts
function clearAlerts() {
    document.getElementById('login-alerts').innerHTML = '';
    document.getElementById('register-alerts').innerHTML = '';
}

// Show alert message
function showAlert(containerId, message, type = 'danger') {
    const container = document.getElementById(containerId);
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    container.appendChild(alertDiv);
}

// Handle login form submission
document.getElementById('login-form-element').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    
    if (!username || !password) {
        showAlert('login-alerts', 'Пожалуйста, заполните все поля', 'danger');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
        });
        
        if (response.ok) {
            const data = await response.json();
            // Store the JWT token
            authToken = data.token;
            currentUser = { username: data.username };
            showChat();
            loadMessages(); // Start loading messages
        } else {
            const data = await response.json();
            showAlert('login-alerts', data.message || 'Неверное имя пользователя или пароль', 'danger');
        }
    } catch (error) {
        showAlert('login-alerts', 'Ошибка соединения с сервером', 'danger');
    }
});

// Handle register form submission
document.getElementById('register-form-element').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('register-username').value.trim();
    const password = document.getElementById('register-password').value.trim();
    const confirmPassword = document.getElementById('register-confirm-password').value.trim();
    
    if (!username || !password || !confirmPassword) {
        showAlert('register-alerts', 'Пожалуйста, заполните все поля', 'danger');
        return;
    }
    
    if (password !== confirmPassword) {
        showAlert('register-alerts', 'Пароли не совпадают', 'danger');
        return;
    }
    
    if (username.length < 3 || username.length > 20) {
        showAlert('register-alerts', 'Имя пользователя должно быть от 3 до 20 символов', 'danger');
        return;
    }
    
    if (password.length < 5 || password.length > 50) {
        showAlert('register-alerts', 'Пароль должен быть от 5 до 50 символов', 'danger');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}&confirm_password=${encodeURIComponent(confirmPassword)}`,
            credentials: 'include'
        });
        
        if (response.ok) {
            // Registration successful
            showAlert('register-alerts', 'Регистрация прошла успешно! Теперь вы можете войти.', 'success');
            setTimeout(() => {
                showLogin();
            }, 2000);
        } else {
            const data = await response.json();
            showAlert('register-alerts', data.message || 'Ошибка при регистрации', 'danger');
        }
    } catch (error) {
        showAlert('register-alerts', 'Ошибка соединения с сервером', 'danger');
    }
});

// Handle logout
async function logout() {
    try {
        await fetch(`${API_BASE_URL}/logout`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    currentUser = null;
    authToken = null;
    showLogin();
    clearAlerts();
}

// Load chat interface
function loadChat() {
    showChat();
    loadMessages();
}

// Check authentication status on page load
async function checkAuthStatus() {
    // For JWT, we don't have a persistent token on page load
    // So we'll just show the login form
    showLogin();
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
}); 