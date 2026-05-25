# Multi-Biometric Identity Verification System

A complete production-ready biometric authentication system with face recognition, fingerprint simulation, secure user management, attendance tracking, and an admin dashboard.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python FastAPI |
| Database | SQLite (via SQLAlchemy ORM) |
| Face Recognition | OpenCV + DeepFace (FaceNet model) |
| Fingerprint | Simulated minutiae-based matching |
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |
| Authentication | JWT (python-jose) |
| Password Hashing | bcrypt (via passlib) |
| Biometric Encryption | Fernet (symmetric AES encryption) |

## System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│  FastAPI     │────▶│  SQLite DB  │
│ (HTML/CSS/  │     │  Backend     │     │             │
│  JS)        │◀────│  (REST API)  │◀────│  (SQLAlchemy)│
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    │  AI Modules  │
                    ├──────────────┤
                    │ • OpenCV     │
                    │ • DeepFace   │
                    │ • Fingerprint│
                    └──────────────┘
```

## Project Structure

```
multi-biometric-system/
├── backend/
│   ├── main.py                    # FastAPI application & all API endpoints
│   ├── database.py                # Database connection & session management
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── auth.py                    # JWT, password hashing, auth dependencies
│   ├── encryption.py              # Fernet-based biometric template encryption
│   ├── face_recognition_module.py # Face detection (OpenCV) + embeddings (DeepFace)
│   ├── fingerprint_module.py      # Simulated fingerprint extraction & matching
│   ├── attendance.py              # Attendance tracking logic
│   ├── seed.py                    # Database seeding script
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── index.html                 # Login page (password/face/fingerprint)
│   ├── register.html              # User registration with optional biometrics
│   ├── dashboard.html             # User dashboard with profile & attendance
│   ├── admin.html                 # Admin panel with user management
│   ├── css/
│   │   └── style.css              # Complete dark-themed UI styles
│   └── js/
│       ├── api.js                 # API client with JWT handling
│       ├── auth.js                # Login/registration/dashboard logic
│       ├── admin.js               # Admin panel functionality
│       └── face.js                # Face capture utilities
├── tests/
│   └── test_api.py                # Automated API tests
├── data/                          # SQLite database storage
├── schema.sql                     # Database schema reference
├── run.py                         # Cross-platform startup script
├── run.bat                        # Windows startup script
└── README.md                      # This file
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Webcam (optional, for face recognition)

### Step 1: Clone and navigate

```bash
cd multi-biometric-system
```

### Step 2: Run the startup script

**Windows:**
```bash
run.bat
```

**macOS/Linux or cross-platform:**
```bash
python run.py
```

### Step 3: Access the system

Open your browser to: **http://localhost:8000/static/index.html**

### Manual Setup (alternative)

```bash
cd backend
pip install -r requirements.txt
python seed.py
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Student | student1 | student123 |
| Student | student2 | student123 |

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login with username/password
- `POST /api/login-face` - Login with face recognition
- `POST /api/login-fingerprint` - Login with fingerprint

### Biometrics
- `POST /api/register-biometric` - Register face or fingerprint data
- `GET /api/profile/biometrics` - Get user's registered biometrics

### Profile
- `GET /api/profile` - Get current user profile

### Attendance
- `POST /api/attendance/log` - Record attendance check-in
- `GET /api/attendance/my` - Get user's attendance records
- `GET /api/attendance/summary` - Get attendance summary

### Admin (requires admin role)
- `GET /admin/users` - List all users
- `GET /admin/users/{id}` - Get user details
- `PUT /admin/users/{id}/toggle-status` - Activate/deactivate user
- `PUT /admin/users/{id}/role` - Change user role
- `DELETE /admin/users/{id}` - Delete user
- `GET /admin/attendance` - View all attendance records
- `GET /admin/actions` - View admin action log

## Features

### 1. Face Recognition
- Uses OpenCV Haar cascades for face detection
- DeepFace with FaceNet model for generating 128-dimensional face embeddings
- Cosine similarity matching with configurable threshold
- Webcam capture or image upload

### 2. Fingerprint Authentication
- Simulated minutiae extraction based on input data
- Hash-based similarity matching
- No hardware fingerprint scanner required

### 3. User Management
- Registration with optional biometric enrollment
- Role-based access control (admin/student)
- Account activation/deactivation
- User deletion with cascading data cleanup

### 4. Attendance Tracking
- Daily check-in with duplicate prevention
- Multiple authentication methods tracked
- Attendance summary and history

### 5. Security
- Passwords hashed with bcrypt
- JWT tokens for session management
- All biometric templates encrypted with Fernet (AES) before storage
- Raw biometric images never stored in database
- Admin action audit logging

## Testing

```bash
# Ensure the server is running, then:
cd tests
python -m pytest test_api.py -v
```

Or install pytest and run from project root:
```bash
pip install pytest requests
python -m pytest tests/ -v
```

## System Modules

### Backend API (`backend/main.py`)
The central FastAPI application that exposes all REST endpoints. Handles request validation, authentication, authorization, and coordinates between modules.

### Face Recognition Module (`backend/face_recognition_module.py`)
Implements face detection using OpenCV's pre-trained Haar cascade classifier and face embedding generation using DeepFace with the FaceNet model. Face matching uses cosine similarity on embedding vectors.

### Fingerprint Module (`backend/fingerprint_module.py`)
Simulates fingerprint recognition by generating a deterministic minutiae pattern from input data. Matching uses a hash-based similarity score. Designed as a drop-in replacement for real fingerprint hardware integration.

### Encryption Module (`backend/encryption.py`)
Uses the `cryptography` library's Fernet implementation (AES-128-CBC with HMAC-SHA256) to encrypt all biometric templates before storage. Encryption keys are derived using PBKDF2 with 100,000 iterations.

### Attendance Module (`backend/attendance.py`)
Manages attendance records with daily duplicate check prevention, per-user history, and summary statistics.

## Known Limitations

1. **Face Recognition**: DeepFace downloads the FaceNet model (~100MB) on first use. Initial face recognition may be slow.
2. **Fingerprint**: The fingerprint module is simulated. For production use, integration with a real fingerprint SDK (e.g., Neurotechnology, SecuGen) would be required.
3. **Concurrent Users**: The system uses SQLite, which has limited concurrent write capacity. For production, migrate to PostgreSQL.
4. **Face Spoofing**: No liveness detection is implemented. The system cannot distinguish between a real face and a photograph.
5. **Camera Access**: HTTPS is required for camera access on many modern browsers. The demo uses HTTP, which works on localhost.
6. **Browser Compatibility**: Camera features require Chrome, Firefox, or Edge. Safari has limited support.
7. **Scalability**: This is a single-server application. For production, add load balancing, database replication, and containerization.

## License

This project is developed for educational and demonstration purposes as a master's degree project.
