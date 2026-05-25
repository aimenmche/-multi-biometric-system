let dashboardFaceStream = null;
let dashboardFaceImage = null;

document.addEventListener('DOMContentLoaded', function() {
});

async function startDashboardCamera() {
    const video = document.getElementById('dashFaceVideo');
    if (!video) return;
    if (dashboardFaceStream) dashboardFaceStream.getTracks().forEach(t => t.stop());
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240, facingMode: 'user' } });
        dashboardFaceStream = stream;
        video.srcObject = stream;
        video.play();
        document.getElementById('dashCaptureBtn').disabled = false;
    } catch (err) {
        showMessage('Camera error: ' + err.message, 'error');
    }
}

function captureDashboardFace() {
    const video = document.getElementById('dashFaceVideo');
    const canvas = document.getElementById('dashFaceCanvas');
    if (!video || !canvas) return;
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    dashboardFaceImage = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
    showMessage('Face captured!', 'success');
    document.getElementById('dashSubmitBtn').disabled = false;
    if (dashboardFaceStream) { dashboardFaceStream.getTracks().forEach(t => t.stop()); dashboardFaceStream = null; }
}

function handleDashboardFaceUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        dashboardFaceImage = e.target.result.split(',')[1];
        showMessage('Face image loaded!', 'success');
        document.getElementById('dashSubmitBtn').disabled = false;
    };
    reader.readAsDataURL(file);
}

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('biometricModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) closeBiometricModal();
        });
    }
});
