from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import AttendanceLog, User
from schemas import AttendanceResponse


def log_attendance(
    db: Session,
    user_id: int,
    method: str,
    status: str = "present",
    ip_address: str = None,
) -> AttendanceLog:
    record = AttendanceLog(
        user_id=user_id,
        method=method,
        status=status,
        ip_address=ip_address,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_attendance(db: Session, user_id: int, limit: int = 50) -> list:
    return (
        db.query(AttendanceLog)
        .filter(AttendanceLog.user_id == user_id)
        .order_by(AttendanceLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_all_attendance(db: Session, limit: int = 100) -> list:
    return (
        db.query(AttendanceLog)
        .order_by(AttendanceLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_attendance_summary(db: Session, date_filter: date = None) -> dict:
    query = db.query(
        AttendanceLog.status,
        func.count(AttendanceLog.id).label("count"),
    )
    if date_filter:
        query = query.filter(func.date(AttendanceLog.timestamp) == date_filter)

    summary = query.group_by(AttendanceLog.status).all()
    result = {row.status: row.count for row in summary}
    result["total"] = sum(result.values())
    return result


def has_checked_in_today(db: Session, user_id: int) -> bool:
    today = date.today()
    record = (
        db.query(AttendanceLog)
        .filter(
            AttendanceLog.user_id == user_id,
            func.date(AttendanceLog.timestamp) == today,
        )
        .first()
    )
    return record is not None
