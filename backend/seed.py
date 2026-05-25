from database import SessionLocal, engine, Base
from models import User, UserRole
from auth import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        if existing:
            logger.info("Admin user already exists, skipping seed")
            return

        admin = User(
            username="admin",
            email="admin@biometric-system.com",
            hashed_password=hash_password("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN.value,
            is_active=1,
        )
        db.add(admin)

        student = User(
            username="student1",
            email="student1@example.com",
            hashed_password=hash_password("student123"),
            full_name="Test Student",
            role=UserRole.STUDENT.value,
            is_active=1,
        )
        db.add(student)

        student2 = User(
            username="student2",
            email="student2@example.com",
            hashed_password=hash_password("student123"),
            full_name="Another Student",
            role=UserRole.STUDENT.value,
            is_active=1,
        )
        db.add(student2)

        db.commit()
        logger.info("Database seeded successfully!")
        logger.info("Admin user: admin / admin123")
        logger.info("Student users: student1 / student123, student2 / student123")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
