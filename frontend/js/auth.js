let currentLoginMethod = 'password';
let capturedFaceImage = null;
let regCapturedFaceImage = null;
let regBiometricTypes = [];
let faceStream = null;
let regFaceStream = null;

function showMessage(msg, type, containerId) {
    const el = document.getElementById(containerId || 'message');
    if (!el) return;
    el.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
    setTimeout(() => { el.innerHTML = ''; }, 5000);
}

function selectLoginOption(method) {
    currentLoginMethod = method;
    document.querySelectorAll('.biometric-option').forEach(el => el.classList.remove('selected'));
    event.target.closest('.biometric-option').classList.add('selected');
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.getElementById(`${method}-login`).classList.add('active');
}

async function handlePasswordLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
        showMessage('Please fill in all fields', 'error');
        return;
    }

    try {
        const result = await loginUser(username, password);
        setToken(result.access_token, true);
        setStoredUser(result.user, true);
        window.location.href = 'dashboard.html';
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const fullName = document.getElementById('fullName').value.trim();
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    if (!fullName || !username || !email || !password) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    if (password.length < 6) {
        showMessage('Password must be at least 6 characters', 'error');
        return;
    }

    try {
        const result = await registerUser({ username, email, password, full_name: fullName, role });
        setToken(result.access_token, true);
        setStoredUser(result.user, true);

        const userId = result.user.id;

        if (regCapturedFaceImage && regBiometricTypes.includes('face')) {
            try {
                await registerBiometric(userId, 'face', regCapturedFaceImage);
            } catch (e) {
                console.warn('Face registration during signup:', e.message);
            }
        }

        if (regBiometricTypes.includes('fingerprint')) {
            const fpCode = document.getElementById('regFingerprintCode').value.trim();
            if (fpCode) {
                try {
                    await registerBiometric(userId, 'fingerprint', fpCode);
                } catch (e) {
                    console.warn('Fingerprint registration during signup:', e.message);
                }
            }
        }

        showMessage('Account created successfully! Redirecting...', 'success');
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 1000);
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

function toggleRegBiometric(type) {
    const option = document.getElementById(`reg-${type}-option`);
    const section = document.getElementById(`reg-${type}-section`);

    if (regBiometricTypes.includes(type)) {
        regBiometricTypes = regBiometricTypes.filter(t => t !== type);
        option.classList.remove('selected');
        section.classList.add('hidden');
    } else {
        regBiometricTypes.push(type);
        option.classList.add('selected');
        section.classList.remove('hidden');
    }
}

function startCamera() {
    const video = document.getElementById('faceVideo');
    if (!video) return;

    if (faceStream) {
        faceStream.getTracks().forEach(t => t.stop());
    }

    navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240, facingMode: 'user' } })
        .then(stream => {
            faceStream = stream;
            video.srcObject = stream;
            video.play();
            document.getElementById('captureBtn').disabled = false;
        })
        .catch(err => {
            showMessage('Camera access denied: ' + err.message, 'error');
        });
}

function captureFace() {
    const video = document.getElementById('faceVideo');
    const canvas = document.getElementById('faceCanvas');
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    capturedFaceImage = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
    showMessage('Face captured successfully!', 'success');
    document.getElementById('faceLoginBtn').disabled = false;

    if (faceStream) {
        faceStream.getTracks().forEach(t => t.stop());
        faceStream = null;
    }
}

function handleFaceUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        capturedFaceImage = e.target.result.split(',')[1];
        showMessage('Face image loaded!', 'success');
        document.getElementById('faceLoginBtn').disabled = false;
    };
    reader.readAsDataURL(file);
}

async function loginWithFace() {
    if (!capturedFaceImage) {
        showMessage('Please capture or upload a face image first', 'error');
        return;
    }

    try {
        const result = await loginWithFace(capturedFaceImage);
        setToken(result.access_token, true);
        setStoredUser(result.user, true);
        window.location.href = 'dashboard.html';
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

async function loginWithFingerprint() {
    const code = document.getElementById('fingerprintCode').value.trim();
    if (!code) {
        showMessage('Please enter a fingerprint code', 'error');
        return;
    }

    try {
        const result = await loginWithFingerprint(code);
        setToken(result.access_token, true);
        setStoredUser(result.user, true);
        window.location.href = 'dashboard.html';
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

function startRegCamera() {
    const video = document.getElementById('regFaceVideo');
    if (!video) return;

    if (regFaceStream) {
        regFaceStream.getTracks().forEach(t => t.stop());
    }

    navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240, facingMode: 'user' } })
        .then(stream => {
            regFaceStream = stream;
            video.srcObject = stream;
            video.play();
            document.getElementById('regCaptureBtn').disabled = false;
        })
        .catch(err => {
            showMessage('Camera access denied: ' + err.message, 'error');
        });
}

function captureRegFace() {
    const video = document.getElementById('regFaceVideo');
    const canvas = document.getElementById('regFaceCanvas');
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    regCapturedFaceImage = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
    showMessage('Face captured for registration!', 'success');

    if (regFaceStream) {
        regFaceStream.getTracks().forEach(t => t.stop());
        regFaceStream = null;
    }
}

function handleRegFaceUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        regCapturedFaceImage = e.target.result.split(',')[1];
        showMessage('Face image loaded for registration!', 'success');
    };
    reader.readAsDataURL(file);
}

function logout() {
    if (faceStream) {
        faceStream.getTracks().forEach(t => t.stop());
    }
    if (regFaceStream) {
        regFaceStream.getTracks().forEach(t => t.stop());
    }
    clearToken();
    clearStoredUser();
    window.location.href = 'index.html';
}

document.addEventListener('DOMContentLoaded', function() {
    const token = getToken();
    const currentPage = window.location.pathname.split('/').pop();

    if (currentPage === 'dashboard.html' || currentPage === 'admin.html') {
        if (!token) {
            window.location.href = 'index.html';
            return;
        }

        loadDashboard();
    }
});

async function loadDashboard() {
    try {
        const user = getStoredUser();
        if (!user) {
            const profile = await getProfile();
            setStoredUser(profile, !!localStorage.getItem('bio_token'));
            renderProfile(profile);
        } else {
            renderProfile(user);
        }

        loadAttendanceRecords();
        loadBiometricList();
    } catch (err) {
        if (err.message.includes('401') || err.message.includes('token')) {
            logout();
        } else {
            showMessage(err.message, 'error');
        }
    }
}

function renderProfile(user) {
    const info = document.getElementById('profileInfo');
    if (!info) return;

    const badge = document.getElementById('roleBadge');
    if (badge) {
        badge.innerHTML = `<span class="badge ${user.role === 'admin' ? 'badge-admin' : 'badge-student'}">${user.role}</span>`;
    }

    const userEl = document.getElementById('userInfo');
    if (userEl) {
        userEl.textContent = `${user.full_name} (${user.role})`;
    }

    info.innerHTML = `
        <div style="margin-bottom:12px"><strong style="color:#aaa">Full Name:</strong> <span style="color:#fff">${user.full_name}</span></div>
        <div style="margin-bottom:12px"><strong style="color:#aaa">Username:</strong> <span style="color:#fff">${user.username}</span></div>
        <div style="margin-bottom:12px"><strong style="color:#aaa">Email:</strong> <span style="color:#fff">${user.email}</span></div>
        <div style="margin-bottom:12px"><strong style="color:#aaa">Role:</strong> <span style="color:#fff;text-transform:capitalize">${user.role}</span></div>
        <div><strong style="color:#aaa">Status:</strong> <span class="badge ${user.is_active ? 'badge-active' : 'badge-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></div>
    `;
}

async function loadAttendanceRecords() {
    const container = document.getElementById('attendanceList');
    if (!container) return;

    try {
        const result = await getMyAttendance(10);
        const today = new Date().toDateString();
        let checkedInToday = false;

        let html = '<h3 style="margin-bottom:12px">Recent Attendance</h3>';
        if (result.records && result.records.length > 0) {
            html += '<table><thead><tr><th>Date</th><th>Time</th><th>Method</th><th>Status</th></tr></thead><tbody>';
            result.records.forEach(r => {
                const dt = new Date(r.timestamp);
                if (dt.toDateString() === today) checkedInToday = true;
                html += `<tr>
                    <td>${dt.toLocaleDateString()}</td>
                    <td>${dt.toLocaleTimeString()}</td>
                    <td><span class="badge badge-student">${r.method}</span></td>
                    <td><span class="badge badge-active">${r.status}</span></td>
                </tr>`;
            });
            html += '</tbody></table>';
        } else {
            html += '<p style="color:#888">No attendance records yet.</p>';
        }

        container.innerHTML = html;

        const todayEl = document.getElementById('todayStatus');
        const checkInBtn = document.getElementById('checkInBtn');
        if (todayEl) {
            todayEl.textContent = checkedInToday ? '✅ Checked in today' : '❌ Not checked in';
        }
        if (checkInBtn) {
            checkInBtn.disabled = checkedInToday;
            checkInBtn.textContent = checkedInToday ? 'Already Checked In' : 'Check In Now';
        }
    } catch (err) {
        container.innerHTML = `<p style="color:#e74c3c">Error loading attendance: ${err.message}</p>`;
    }
}

async function checkIn() {
    const user = getStoredUser();
    if (!user) return;

    try {
        const result = await recordAttendance(user.id, 'web_manual', 'present');
        showMessage(result.message, 'success');
        loadAttendanceRecords();
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

async function loadBiometricList() {
    const container = document.getElementById('biometricList');
    if (!container) return;

    try {
        const biometrics = await getMyBiometrics();
        if (biometrics && biometrics.length > 0) {
            let html = '<table><thead><tr><th>Type</th><th>Registered On</th></tr></thead><tbody>';
            biometrics.forEach(b => {
                const dt = b.created_at ? new Date(b.created_at).toLocaleDateString() : 'Unknown';
                const icon = b.biometric_type === 'face' ? '👤' : '🖐️';
                html += `<tr>
                    <td>${icon} ${b.biometric_type.charAt(0).toUpperCase() + b.biometric_type.slice(1)}</td>
                    <td>${dt}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color:#888">No biometric data registered. Click "Add" to register.</p>';
        }
    } catch (err) {
        container.innerHTML = `<p style="color:#e74c3c">Error: ${err.message}</p>`;
    }
}

function registerBiometric() {
    const modal = document.getElementById('biometricModal');
    const body = document.getElementById('biometricModalBody');
    if (!modal || !body) return;

    const user = getStoredUser();
    if (!user) return;

    body.innerHTML = `
        <p style="color:#aaa;margin-bottom:15px">Choose a biometric type to register:</p>
        <div class="biometric-options" style="margin-bottom:20px">
            <div class="biometric-option" onclick="addFaceBiometric()">
                <div class="icon">👤</div>
                <div class="label">Face</div>
            </div>
            <div class="biometric-option" onclick="addFingerprintBiometric()">
                <div class="icon">🖐️</div>
                <div class="label">Fingerprint</div>
            </div>
        </div>
        <div id="biometricActionArea"></div>
    `;
    modal.classList.remove('hidden');
}

function closeBiometricModal() {
    const modal = document.getElementById('biometricModal');
    if (modal) modal.classList.add('hidden');
}

async function addFaceBiometric() {
    const area = document.getElementById('biometricActionArea');
    if (!area) return;

    area.innerHTML = `
        <p style="color:#aaa;margin-bottom:10px">Take a selfie or upload a face photo:</p>
        <div class="camera-container">
            <video id="modalFaceVideo" autoplay muted playsinline style="width:100%;border-radius:8px"></video>
            <canvas id="modalFaceCanvas"></canvas>
        </div>
        <div style="display:flex;gap:10px;margin-top:10px">
            <button onclick="startModalCamera()" class="btn btn-secondary" style="flex:1">📷 Start Camera</button>
            <button onclick="captureModalFace()" class="btn btn-primary" style="flex:1" id="modalCaptureBtn" disabled>Capture</button>
        </div>
        <input type="file" id="modalFaceUpload" accept="image/*" style="display:none" onchange="handleModalFaceUpload(event)">
        <button onclick="document.getElementById('modalFaceUpload').click()" class="btn btn-secondary" style="width:100%;margin-top:10px">📁 Upload</button>
        <button onclick="submitFaceBiometric()" class="btn btn-success" style="width:100%;margin-top:15px" id="submitFaceBtn" disabled>Register Face</button>
    `;
}

let modalFaceImage = null;
let modalFaceStream = null;

function startModalCamera() {
    const video = document.getElementById('modalFaceVideo');
    if (!video) return;
    if (modalFaceStream) modalFaceStream.getTracks().forEach(t => t.stop());
    navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240, facingMode: 'user' } })
        .then(stream => {
            modalFaceStream = stream;
            video.srcObject = stream;
            video.play();
            document.getElementById('modalCaptureBtn').disabled = false;
        })
        .catch(err => showMessage('Camera error: ' + err.message, 'error'));
}

function captureModalFace() {
    const video = document.getElementById('modalFaceVideo');
    const canvas = document.getElementById('modalFaceCanvas');
    if (!video || !canvas) return;
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    modalFaceImage = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
    showMessage('Face captured!', 'success');
    document.getElementById('submitFaceBtn').disabled = false;
    if (modalFaceStream) { modalFaceStream.getTracks().forEach(t => t.stop()); modalFaceStream = null; }
}

function handleModalFaceUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        modalFaceImage = e.target.result.split(',')[1];
        showMessage('Face image loaded!', 'success');
        document.getElementById('submitFaceBtn').disabled = false;
    };
    reader.readAsDataURL(file);
}

async function submitFaceBiometric() {
    if (!modalFaceImage) return;
    const user = getStoredUser();
    try {
        await registerBiometric(user.id, 'face', modalFaceImage);
        showMessage('Face biometric registered successfully!', 'success');
        closeBiometricModal();
        loadBiometricList();
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

function addFingerprintBiometric() {
    const area = document.getElementById('biometricActionArea');
    if (!area) return;
    area.innerHTML = `
        <p style="color:#aaa;margin-bottom:10px">Enter a fingerprint code to simulate fingerprint registration:</p>
        <div class="form-group">
            <input type="text" id="modalFingerprintCode" placeholder="Enter fingerprint code">
        </div>
        <button onclick="submitFingerprintBiometric()" class="btn btn-success" style="width:100%">Register Fingerprint</button>
    `;
}

async function submitFingerprintBiometric() {
    const code = document.getElementById('modalFingerprintCode').value.trim();
    if (!code) { showMessage('Please enter a fingerprint code', 'error'); return; }
    const user = getStoredUser();
    try {
        await registerBiometric(user.id, 'fingerprint', code);
        showMessage('Fingerprint biometric registered successfully!', 'success');
        closeBiometricModal();
        loadBiometricList();
    } catch (err) {
        showMessage(err.message, 'error');
    }
}
