"""Seed database with test data."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine, Base
from app.models.user import User, Role, Level, StudentProfile, TeacherProfile
from app.core.security import get_password_hash


async def seed_database():
    """Seed the database with test users."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        # Test users as specified in the requirements
        test_users = [
            {
                "email": "admin@univ-rennes.fr",
                "password": "admin123",
                "name": "Admin User",
                "role": Role.ADMIN,
            },
            {
                "email": "house@univ-rennes.fr",
                "password": "prof123",
                "name": "Dr. House",
                "role": Role.TEACHER,
                "department": "Anatomie",
            },
            {
                "email": "wilson@univ-rennes.fr",
                "password": "prof123",
                "name": "Dr. Wilson",
                "role": Role.TEACHER,
                "department": "Anatomie",
            },
            {
                "email": "marie.martin@univ-rennes.fr",
                "password": "student123",
                "name": "Marie Martin",
                "role": Role.STUDENT,
                "level": Level.L1,
            },
            {
                "email": "jean.dupont@univ-rennes.fr",
                "password": "student123",
                "name": "Jean Dupont",
                "role": Role.STUDENT,
                "level": Level.L1,
            },
        ]
        
        for user_data in test_users:
            # Create user
            user = User(
                email=user_data["email"],
                password=get_password_hash(user_data["password"]),
                name=user_data["name"],
                role=user_data["role"],
            )
            db.add(user)
            await db.flush()  # Get the user ID
            
            # Create profile based on role
            if user_data["role"] == Role.STUDENT:
                profile = StudentProfile(
                    user_id=user.id,
                    level=user_data["level"],
                )
                db.add(profile)
            elif user_data["role"] == Role.TEACHER:
                profile = TeacherProfile(
                    user_id=user.id,
                    faculty_department=user_data.get("department"),
                )
                db.add(profile)
        
        await db.commit()
        print("✓ Database seeded successfully with test users:")
        for user_data in test_users:
            print(f"  - {user_data['email']} / {user_data['password']} ({user_data['role'].value})")


if __name__ == "__main__":
    asyncio.run(seed_database())
