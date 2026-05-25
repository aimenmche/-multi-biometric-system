import logging
import os
from datetime import date
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import User, BiometricData, AttendanceLog, AdminAction, UserRole
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    BiometricRegister, BiometricLogin,
    AttendanceRecord, AttendanceResponse,
    AttendanceListResponse, UserListResponse,
    AdminActionCreate,
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin,
)
from encryption import encrypt_biometric_template, decrypt_biometric_template
from face_recognition_module import (
    detect_face, generate_face_embedding, compare_face_embeddings,
)
from fingerprint_module import (
    extract_fingerprint_features, match_fingerprint_templates,
)
from attendance import (
    log_attendance, get_user_attendance, get_all_attendance,
    get_attendance_summary, has_checked_in_today,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Biometric Identity Verification System",
    description="A complete biometric authentication system with face and fingerprint recognition",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend")


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "system": "Multi-Biometric Identity Verification System"}


@app.post("/api/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    if user_data.role not in [UserRole.ADMIN.value, UserRole.STUDENT.value]:
        user_data.role = UserRole.STUDENT.value

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=_user_to_response(user),
    )


@app.post("/api/login", response_model=Token)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=_user_to_response(user),
    )


@app.post("/api/register-biometric")
def register_biometric(
    biometric: BiometricRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != biometric.user_id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == biometric.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if biometric.biometric_type == "face":
        face_detected, msg = detect_face(biometric.template_data)
        if not face_detected:
            raise HTTPException(status_code=400, detail=f"Face detection failed: {msg}")
        embedding, error = generate_face_embedding(biometric.template_data)
        if error:
            raise HTTPException(status_code=400, detail=f"Embedding failed: {error}")
        template_to_store = embedding
        template_hash = str(hash(embedding))
    elif biometric.biometric_type == "fingerprint":
        features, error = extract_fingerprint_features(biometric.template_data)
        if error:
            raise HTTPException(status_code=400, detail=f"Fingerprint extraction failed: {error}")
        template_to_store = features
        template_hash = str(hash(features))
    else:
        raise HTTPException(status_code=400, detail="Invalid biometric type. Use 'face' or 'fingerprint'")

    encrypted = encrypt_biometric_template(template_to_store)

    existing = db.query(BiometricData).filter(
        BiometricData.user_id == biometric.user_id,
        BiometricData.biometric_type == biometric.biometric_type,
    ).first()

    if existing:
        existing.encrypted_template = encrypted
        existing.template_hash = template_hash
    else:
        bio_entry = BiometricData(
            user_id=biometric.user_id,
            biometric_type=biometric.biometric_type,
            encrypted_template=encrypted,
            template_hash=template_hash,
        )
        db.add(bio_entry)

    db.commit()
    return {
        "message": f"{biometric.biometric_type} biometric data registered successfully",
        "biometric_type": biometric.biometric_type,
    }


@app.post("/api/login-face", response_model=Token)
def login_with_face(
    face_data: BiometricLogin,
    db: Session = Depends(get_db),
):
    face_detected, msg = detect_face(face_data.template_data)
    if not face_detected:
        raise HTTPException(status_code=400, detail=f"Face detection failed: {msg}")

    new_embedding, error = generate_face_embedding(face_data.template_data)
    if error:
        raise HTTPException(status_code=400, detail=f"Embedding failed: {error}")

    stored_templates = db.query(BiometricData).filter(
        BiometricData.biometric_type == "face",
    ).all()

    best_match = None
    best_distance = float("inf")

    for stored in stored_templates:
        try:
            stored_embedding = decrypt_biometric_template(stored.encrypted_template)
            is_match, distance = compare_face_embeddings(new_embedding, stored_embedding)
            if is_match and distance < best_distance:
                best_distance = distance
                best_match = stored
        except Exception as e:
            logger.warning(f"Error comparing face with user {stored.user_id}: {e}")
            continue

    if best_match is None:
        raise HTTPException(status_code=401, detail="Face not recognized")

    user = db.query(User).filter(User.id == best_match.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User account inactive")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=_user_to_response(user),
    )


@app.post("/api/login-fingerprint", response_model=Token)
def login_with_fingerprint(
    fp_data: BiometricLogin,
    db: Session = Depends(get_db),
):
    new_features, error = extract_fingerprint_features(fp_data.template_data)
    if error:
        raise HTTPException(status_code=400, detail=f"Fingerprint extraction failed: {error}")

    stored_templates = db.query(BiometricData).filter(
        BiometricData.biometric_type == "fingerprint",
    ).all()

    best_match = None
    best_score = 0.0

    for stored in stored_templates:
        try:
            stored_features = decrypt_biometric_template(stored.encrypted_template)
            is_match, score = match_fingerprint_templates(stored_features, new_features)
            if is_match and score > best_score:
                best_score = score
                best_match = stored
        except Exception as e:
            logger.warning(f"Error comparing fingerprint with user {stored.user_id}: {e}")
            continue

    if best_match is None:
        raise HTTPException(status_code=401, detail="Fingerprint not recognized")

    user = db.query(User).filter(User.id == best_match.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User account inactive")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=_user_to_response(user),
    )


@app.get("/api/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return _user_to_response(current_user)


@app.get("/api/profile/biometrics")
def get_biometrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biometrics = db.query(BiometricData).filter(
        BiometricData.user_id == current_user.id
    ).all()
    return [
        {
            "id": b.id,
            "biometric_type": b.biometric_type,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in biometrics
    ]


@app.post("/api/attendance/log")
def record_attendance(
    record: AttendanceRecord,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = record.user_id
    if current_user.role != UserRole.ADMIN.value:
        user_id = current_user.id

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if has_checked_in_today(db, user_id):
        raise HTTPException(status_code=400, detail="Already checked in today")

    attendance = log_attendance(
        db=db,
        user_id=user_id,
        method=record.method,
        status=record.status,
        ip_address=None,
    )
    return {
        "message": "Attendance recorded successfully",
        "attendance_id": attendance.id,
        "timestamp": attendance.timestamp.isoformat() if attendance.timestamp else None,
    }


@app.get("/api/attendance/my", response_model=AttendanceListResponse)
def my_attendance(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = get_user_attendance(db, current_user.id, limit)
    return AttendanceListResponse(
        records=[
            AttendanceResponse(
                id=r.id,
                user_id=r.user_id,
                timestamp=r.timestamp,
                method=r.method,
                status=r.status,
            )
            for r in records
        ],
        total=len(records),
    )


@app.get("/api/attendance/summary")
def attendance_summary(
    date_str: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filter_date = None
    if date_str:
        try:
            filter_date = date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    summary = get_attendance_summary(db, filter_date)
    return summary


@app.get("/admin/users", response_model=UserListResponse)
def admin_list_users(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(User)
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    users = query.order_by(User.created_at.desc()).all()
    return UserListResponse(
        users=[_user_to_response(u) for u in users],
        total=len(users),
    )


@app.get("/admin/users/{user_id}", response_model=UserResponse)
def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@app.put("/admin/users/{user_id}/toggle-status")
def admin_toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = 0 if user.is_active else 1
    db.commit()

    action = AdminAction(
        admin_id=current_user.id,
        action="toggle_user_status",
        target_user_id=user_id,
        details=f"User {'activated' if user.is_active else 'deactivated'}: {user.username}",
    )
    db.add(action)
    db.commit()

    return {
        "message": f"User {'activated' if user.is_active else 'deactivated'}",
        "user_id": user_id,
        "is_active": user.is_active,
    }


@app.get("/admin/attendance", response_model=AttendanceListResponse)
def admin_attendance(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    records = get_all_attendance(db, limit)
    return AttendanceListResponse(
        records=[
            AttendanceResponse(
                id=r.id,
                user_id=r.user_id,
                timestamp=r.timestamp,
                method=r.method,
                status=r.status,
            )
            for r in records
        ],
        total=len(records),
    )


@app.get("/admin/actions")
def admin_get_actions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    actions = (
        db.query(AdminAction)
        .order_by(AdminAction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "admin_id": a.admin_id,
            "action": a.action,
            "target_user_id": a.target_user_id,
            "details": a.details,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in actions
    ]


@app.put("/admin/users/{user_id}/role")
def admin_change_role(
    user_id: int,
    new_role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    if new_role not in [UserRole.ADMIN.value, UserRole.STUDENT.value]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = new_role
    db.commit()

    action = AdminAction(
        admin_id=current_user.id,
        action="change_role",
        target_user_id=user_id,
        details=f"Role changed from {old_role} to {new_role} for user: {user.username}",
    )
    db.add(action)
    db.commit()

    return {"message": f"Role updated to {new_role}", "user_id": user_id, "new_role": new_role}


@app.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(BiometricData).filter(BiometricData.user_id == user_id).delete()
    db.query(AttendanceLog).filter(AttendanceLog.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    action = AdminAction(
        admin_id=current_user.id,
        action="delete_user",
        target_user_id=user_id,
        details=f"Deleted user: {user.username}",
    )
    db.add(action)
    db.commit()

    return {"message": "User deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
