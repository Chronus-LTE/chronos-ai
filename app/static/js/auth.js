const API_URL = '/api/v1/auth';

async function loginWithGoogle() {
    try {
        const response = await fetch(`${API_URL}/google/login`);
        const data = await response.json();

        if (data.authorization_url) {
            window.location.href = data.authorization_url;
        } else {
            console.error('No authorization URL found');
        }
    } catch (error) {
        console.error('Error initiating Google login:', error);
    }
}


async function login(email, password) {
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        // Store token
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));

        return data;
    } catch (error) {
        throw error;
    }
}

async function register(email, password, fullName) {
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                full_name: fullName
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }

        return data;
    } catch (error) {
        throw error;
    }
}

async function getProfile() {
    const token = localStorage.getItem('token');
    if (!token) return null;

    try {
        const response = await fetch(`${API_URL}/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                logout();
            }
            throw new Error('Failed to fetch profile');
        }

        return await response.json();
    } catch (error) {
        return null;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/static/login.html';
}

function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/static/login.html';
    }
}

function redirectIfAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        window.location.href = '/static/dashboard.html';
    }
}
