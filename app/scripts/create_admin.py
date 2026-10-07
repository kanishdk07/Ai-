"""
Create Admin User Script
Run this script to create the default admin user
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.models import User, UserRole
from app.utils.security import get_password_hash
from app.database import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_admin_user():
    """Create default admin user"""

    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if admin user already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == settings.DEFAULT_ADMIN_EMAIL)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Admin user already exists: {existing_user.username}")
            print(f"Admin user already exists: {existing_user.username}")
            return

        # Create admin user
        admin_user = User(
            email=settings.DEFAULT_ADMIN_EMAIL,
            username="admin",
            hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        session.add(admin_user)
        await session.commit()

        logger.info(f"Admin user created successfully!")
        print("\n" + "="*60)
        print("Admin user created successfully!")
        print("="*60)
        print(f"Username: admin")
        print(f"Email: {settings.DEFAULT_ADMIN_EMAIL}")
        print(f"Password: {settings.DEFAULT_ADMIN_PASSWORD}")
        print("="*60)
        print("\n⚠️  IMPORTANT: Change the default password immediately!")
        print("="*60 + "\n")

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        sys.exit(1)
