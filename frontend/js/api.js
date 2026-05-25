const API_BASE = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
    ? 'http://localhost:8000'
    : window.location.origin;

function getToken() {
    return localStorage.getItem('bio_token') || sessionStorage.getItem('bio_token');
}

function setToken(token, remember) {
    if (remember) {
        localStorage.setItem('bio_token', token);
    } else {
        sessionStorage.setItem('bio_token', token);
    }
}

function clearToken() {
    localStorage.removeItem('bio_token');
    sessionStorage.removeItem('bio_token');
}

function getStoredUser() {
    const u = localStorage.getItem('bio_user') || sessionStorage.getItem('bio_user');
    return u ? JSON.parse(u) : null;
}

function setStoredUser(user, remember) {
    const str = JSON.stringify(user);
    if (remember) {
        localStorage.setItem('bio_user', str);
    } else {
        sessionStorage.setItem('bio_user', str);
    }
}

function clearStoredUser() {
    localStorage.removeItem('bio_user');
    sessionStorage.removeItem('bio_user');
}

async function apiRequest(method, path, body, isFormData) {
    const token = getToken();
    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    if (body && !isFormData) {
        headers['Content-Type'] = 'application/json';
    }

    const config = {
        method: method.toUpperCase(),
        headers: headers,
    };

    if (body) {
        config.body = isFormData ? body : JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE}${path}`, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}: Request failed`);
        }

        return data;
    } catch (error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('Cannot connect to server. Make sure the backend is running on port 8000.');
        }
        throw error;
    }
}

async function loginUser(username, password) {
    return apiRequest('POST', '/api/login', { username, password });
}

async function registerUser(userData) {
    return apiRequest('POST', '/api/register', userData);
}

async function loginWithFace(faceImageB64) {
    return apiRequest('POST', '/api/login-face', {
        biometric_type: 'face',
        template_data: faceImageB64,
    });
}

async function loginWithFingerprint(fpCode) {
    return apiRequest('POST', '/api/login-fingerprint', {
        biometric_type: 'fingerprint',
        template_data: fpCode,
    });
}

async function registerBiometric(userId, type, data) {
    return apiRequest('POST', '/api/register-biometric', {
        user_id: userId,
        biometric_type: type,
        template_data: data,
    });
}

async function getProfile() {
    return apiRequest('GET', '/api/profile');
}

async function getMyBiometrics() {
    return apiRequest('GET', '/api/profile/biometrics');
}

async function recordAttendance(userId, method, status) {
    return apiRequest('POST', '/api/attendance/log', {
        user_id: userId,
        method: method,
        status: status || 'present',
    });
}

async function getMyAttendance(limit) {
    return apiRequest('GET', `/api/attendance/my?limit=${limit || 50}`);
}

async function getAttendanceSummary(dateStr) {
    const q = dateStr ? `?date_str=${dateStr}` : '';
    return apiRequest('GET', `/api/attendance/summary${q}`);
}

async function adminGetUsers(search) {
    const q = search ? `?search=${encodeURIComponent(search)}` : '';
    return apiRequest('GET', `/admin/users${q}`);
}

async function adminGetUser(userId) {
    return apiRequest('GET', `/admin/users/${userId}`);
}

async function adminToggleUserStatus(userId) {
    return apiRequest('PUT', `/admin/users/${userId}/toggle-status`);
}

async function adminChangeRole(userId, newRole) {
    const formData = new FormData();
    formData.append('new_role', newRole);
    return apiRequest('PUT', `/admin/users/${userId}/role`, formData, true);
}

async function adminDeleteUser(userId) {
    return apiRequest('DELETE', `/admin/users/${userId}`);
}

async function adminGetAttendance(limit) {
    return apiRequest('GET', `/admin/attendance?limit=${limit || 100}`);
}

async function adminGetActions(limit) {
    return apiRequest('GET', `/admin/actions?limit=${limit || 50}`);
}
