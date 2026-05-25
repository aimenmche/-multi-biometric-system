document.addEventListener('DOMContentLoaded', function() {
    const token = getToken();
    const user = getStoredUser();
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    if (!user || user.role !== 'admin') {
        window.location.href = 'dashboard.html';
        return;
    }

    const userEl = document.getElementById('userInfo');
    if (userEl) userEl.textContent = `${user.full_name} (Admin)`;

    loadAdminDashboard();
});

async function loadAdminDashboard() {
    try {
        const [usersRes, attendanceRes] = await Promise.all([
            adminGetUsers(),
            adminGetAttendance(1000),
        ]);

        const totalUsers = usersRes.total || 0;
        document.getElementById('totalUsers').textContent = totalUsers;

        const today = new Date().toISOString().split('T')[0];
        let todayCount = 0;
        if (attendanceRes.records) {
            attendanceRes.records.forEach(r => {
                if (r.timestamp && r.timestamp.startsWith(today)) todayCount++;
            });
        }
        document.getElementById('todayAttendance').textContent = todayCount;

        const summary = await getAttendanceSummary(today);
        document.getElementById('biometricCount').textContent = summary.total || 0;

        loadUsers();
    } catch (err) {
        showMessage('Error loading dashboard: ' + err.message, 'error');
    }
}

async function loadUsers() {
    const container = document.getElementById('usersTable');
    if (!container) return;

    const search = document.getElementById('userSearch')?.value.trim();
    container.innerHTML = '<div class="loading"></div>';

    try {
        const result = await adminGetUsers(search);

        if (!result.users || result.users.length === 0) {
            container.innerHTML = '<p style="color:#888;text-align:center;padding:20px">No users found.</p>';
            return;
        }

        let html = '<table><thead><tr><th>ID</th><th>Username</th><th>Full Name</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
        result.users.forEach(u => {
            html += `<tr>
                <td>${u.id}</td>
                <td>${u.username}</td>
                <td>${u.full_name}</td>
                <td>${u.email}</td>
                <td><span class="badge ${u.role === 'admin' ? 'badge-admin' : 'badge-student'}">${u.role}</span></td>
                <td><span class="badge ${u.is_active ? 'badge-active' : 'badge-inactive'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>
                    <button onclick="viewUser(${u.id})" class="btn btn-secondary" style="padding:6px 12px;font-size:0.8rem">View</button>
                    <button onclick="toggleUserStatus(${u.id})" class="btn ${u.is_active ? 'btn-danger' : 'btn-success'}" style="padding:6px 12px;font-size:0.8rem">${u.is_active ? 'Deactivate' : 'Activate'}</button>
                    <button onclick="deleteUser(${u.id})" class="btn btn-danger" style="padding:6px 12px;font-size:0.8rem">Delete</button>
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<p style="color:#e74c3c">Error: ${err.message}</p>`;
    }
}

function searchUsers() {
    loadUsers();
}

async function viewUser(userId) {
    const modal = document.getElementById('userModal');
    const title = document.getElementById('userModalTitle');
    const body = document.getElementById('userModalBody');
    if (!modal || !body) return;

    title.textContent = 'Loading...';
    body.innerHTML = '<div class="loading"></div>';
    modal.classList.remove('hidden');

    try {
        const user = await adminGetUser(userId);
        title.textContent = `User: ${user.full_name}`;
        body.innerHTML = `
            <div style="margin-bottom:15px"><strong style="color:#aaa">ID:</strong> <span style="color:#fff">${user.id}</span></div>
            <div style="margin-bottom:15px"><strong style="color:#aaa">Username:</strong> <span style="color:#fff">${user.username}</span></div>
            <div style="margin-bottom:15px"><strong style="color:#aaa">Email:</strong> <span style="color:#fff">${user.email}</span></div>
            <div style="margin-bottom:15px"><strong style="color:#aaa">Full Name:</strong> <span style="color:#fff">${user.full_name}</span></div>
            <div style="margin-bottom:15px"><strong style="color:#aaa">Role:</strong> <span class="badge ${user.role === 'admin' ? 'badge-admin' : 'badge-student'}">${user.role}</span></div>
            <div style="margin-bottom:15px"><strong style="color:#aaa">Status:</strong> <span class="badge ${user.is_active ? 'badge-active' : 'badge-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></div>
            <div style="margin-bottom:15px"><strong style="color:#aaa">Created:</strong> <span style="color:#fff">${user.created_at ? new Date(user.created_at).toLocaleString() : 'Unknown'}</span></div>
            <hr style="border-color:rgba(255,255,255,0.1);margin:20px 0">
            <h3 style="margin-bottom:15px">Change Role</h3>
            <div style="display:flex;gap:10px">
                <select id="roleSelect" style="flex:1;padding:10px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:8px;color:#fff">
                    <option value="student" ${user.role === 'student' ? 'selected' : ''}>Student</option>
                    <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                </select>
                <button onclick="changeUserRole(${user.id})" class="btn btn-primary">Update Role</button>
            </div>
        `;
    } catch (err) {
        body.innerHTML = `<p style="color:#e74c3c">Error: ${err.message}</p>`;
    }
}

function closeUserModal() {
    const modal = document.getElementById('userModal');
    if (modal) modal.classList.add('hidden');
}

async function toggleUserStatus(userId) {
    if (!confirm('Are you sure you want to toggle this user\'s status?')) return;
    try {
        const result = await adminToggleUserStatus(userId);
        showMessage(result.message, 'success');
        loadUsers();
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

async function changeUserRole(userId) {
    const select = document.getElementById('roleSelect');
    if (!select) return;
    const newRole = select.value;
    try {
        const result = await adminChangeRole(userId, newRole);
        showMessage(result.message, 'success');
        closeUserModal();
        loadUsers();
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to permanently delete this user? This action cannot be undone.')) return;
    try {
        const result = await adminDeleteUser(userId);
        showMessage(result.message, 'success');
        loadUsers();
        loadAdminDashboard();
    } catch (err) {
        showMessage(err.message, 'error');
    }
}

function switchAdminTab(tab, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`admin-${tab}`).classList.add('active');

    if (tab === 'attendance') loadAdminAttendance();
    if (tab === 'actions') loadAdminActions();
}

async function loadAdminAttendance() {
    const container = document.getElementById('attendanceTable');
    if (!container) return;
    container.innerHTML = '<div class="loading"></div>';

    try {
        const result = await adminGetAttendance(200);
        if (!result.records || result.records.length === 0) {
            container.innerHTML = '<p style="color:#888;text-align:center;padding:20px">No attendance records.</p>';
            return;
        }

        let html = '<table><thead><tr><th>ID</th><th>User ID</th><th>Date/Time</th><th>Method</th><th>Status</th></tr></thead><tbody>';
        result.records.forEach(r => {
            const dt = r.timestamp ? new Date(r.timestamp).toLocaleString() : 'Unknown';
            const methodIcons = { face: '👤', fingerprint: '🖐️', web_manual: '🌐' };
            const icon = methodIcons[r.method] || '📋';
            html += `<tr>
                <td>${r.id}</td>
                <td>${r.user_id}</td>
                <td>${dt}</td>
                <td>${icon} ${r.method}</td>
                <td><span class="badge badge-active">${r.status}</span></td>
            </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<p style="color:#e74c3c">Error: ${err.message}</p>`;
    }
}

async function loadAdminActions() {
    const container = document.getElementById('actionsTable');
    if (!container) return;
    container.innerHTML = '<div class="loading"></div>';

    try {
        const actions = await adminGetActions(100);
        if (!actions || actions.length === 0) {
            container.innerHTML = '<p style="color:#888;text-align:center;padding:20px">No admin actions recorded.</p>';
            return;
        }

        let html = '<table><thead><tr><th>ID</th><th>Admin ID</th><th>Action</th><th>Target User</th><th>Details</th><th>Date</th></tr></thead><tbody>';
        actions.forEach(a => {
            const dt = a.created_at ? new Date(a.created_at).toLocaleString() : 'Unknown';
            html += `<tr>
                <td>${a.id}</td>
                <td>${a.admin_id}</td>
                <td><span class="badge badge-student">${a.action}</span></td>
                <td>${a.target_user_id || '-'}</td>
                <td>${a.details || '-'}</td>
                <td>${dt}</td>
            </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<p style="color:#e74c3c">Error: ${err.message}</p>`;
    }
}

function saveSettings() {
    const faceVal = document.getElementById('faceThreshold').value;
    const fpVal = document.getElementById('fpThreshold').value;

    localStorage.setItem('bio_face_threshold', faceVal);
    localStorage.setItem('bio_fp_threshold', fpVal);

    document.getElementById('faceThresholdVal').textContent = parseFloat(faceVal).toFixed(2);
    document.getElementById('fpThresholdVal').textContent = parseFloat(fpVal).toFixed(2);

    showMessage('Settings saved locally', 'success');
}

document.addEventListener('DOMContentLoaded', function() {
    const faceSlider = document.getElementById('faceThreshold');
    const fpSlider = document.getElementById('fpThreshold');
    if (faceSlider) {
        const saved = localStorage.getItem('bio_face_threshold');
        if (saved) faceSlider.value = saved;
        document.getElementById('faceThresholdVal').textContent = parseFloat(faceSlider.value).toFixed(2);
        faceSlider.addEventListener('input', function() {
            document.getElementById('faceThresholdVal').textContent = parseFloat(this.value).toFixed(2);
        });
    }
    if (fpSlider) {
        const saved = localStorage.getItem('bio_fp_threshold');
        if (saved) fpSlider.value = saved;
        document.getElementById('fpThresholdVal').textContent = parseFloat(fpSlider.value).toFixed(2);
        fpSlider.addEventListener('input', function() {
            document.getElementById('fpThresholdVal').textContent = parseFloat(this.value).toFixed(2);
        });
    }
});
