"""
Test Configuration and Fixtures
Shared pytest configuration and fixtures for all tests
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import Text, String, JSON as SA_JSON

from httpx import AsyncClient
from app.main import app
from app.database import Base, get_db
from app.models import User, UserRole
from app.utils.security import get_password_hash, create_access_token
from app.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


import sqlite3
import uuid

# Register SQLite adapters so python's sqlite3 can bind uuid.UUID seamlessly
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))
sqlite3.register_converter("uuid", lambda b: uuid.UUID(b.decode()))
sqlite3.register_converter("UUID", lambda b: uuid.UUID(b.decode()))

_sqlite_patch_applied = False


from sqlalchemy.types import TypeDecorator, CHAR

class SQLiteGUID(TypeDecorator):
    """
    Platform-independent GUID type for SQLite test runs.
    Accepts both str and uuid.UUID on bind, returns uuid.UUID on load.
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value)) if not isinstance(value, uuid.UUID) else value


def _patch_pg_columns_for_sqlite():
    """
    Replace PostgreSQL-specific column types with SQLite-compatible equivalents
    in the shared SQLAlchemy metadata so the in-memory test DB can be created.

    Patches applied (idempotent — safe to call multiple times):
    - geoalchemy2.Geography / Geometry  → Text  (nullable=True)
    - dialects.postgresql.UUID          → SQLiteGUID()
    - dialects.postgresql.ARRAY         → JSON  (stores as JSON array)

    Must be called AFTER all models are imported.
    """
    global _sqlite_patch_applied
    if _sqlite_patch_applied:
        return

    # Ensure all models are registered
    import app.models  # noqa: F401

    # ── Geography / Geometry ──────────────────────────────────────────────────
    try:
        from geoalchemy2 import Geography, Geometry
        geo_types = (Geography, Geometry)
    except ImportError:
        geo_types = ()

    # ── PostgreSQL dialect types ──────────────────────────────────────────────
    try:
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY as PG_ARRAY
        uuid_type = PG_UUID
        array_type = PG_ARRAY
    except ImportError:
        uuid_type = None
        array_type = None

    for table in Base.metadata.tables.values():
        for col in table.columns:
            if geo_types and isinstance(col.type, geo_types):
                col.type = Text()
                col.nullable = True
            elif uuid_type and isinstance(col.type, uuid_type):
                # Use SQLiteGUID which accepts both str and uuid.UUID
                col.type = SQLiteGUID()
            elif array_type and isinstance(col.type, array_type):
                # SQLite has no ARRAY; store as JSON array
                col.type = SA_JSON()

    _sqlite_patch_applied = True



@pytest.fixture(autouse=True)
def reset_maintenance_mode():
    """Ensure MAINTENANCE_MODE is always False before and after each test"""
    settings.MAINTENANCE_MODE = False
    yield
    settings.MAINTENANCE_MODE = False


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine with PG-specific columns patched for SQLite"""
    # Override DATABASE_URL so services that check settings.DATABASE_URL
    # correctly detect the test dialect (e.g. hospital_service dialect detection)
    settings.DATABASE_URL = TEST_DATABASE_URL

    _patch_pg_columns_for_sqlite()

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_spatial_functions(dbapi_con, record):
        dbapi_con.create_function("ST_MakePoint", 2, lambda lon, lat: f"POINT({lon} {lat})")
        dbapi_con.create_function("ST_SetSRID", 2, lambda pt, srid: f"SRID={srid};{pt}")
        dbapi_con.create_function("ST_GeomFromText", 2, lambda wkt, srid: f"SRID={srid};{wkt}")
        dbapi_con.create_function("ST_Point", 2, lambda lon, lat: f"POINT({lon} {lat})")
        dbapi_con.create_function("ST_Distance", 2, lambda p1, p2: 0.0)
        dbapi_con.create_function("ST_DWithin", 3, lambda p1, p2, dist: 1)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()



@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override"""
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()



@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user"""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def operator_user(db_session: AsyncSession) -> User:
    """Create an operator user"""
    user = User(
        email="operator@example.com",
        username="operator",
        hashed_password=get_password_hash("operatorpassword123"),
        full_name="Operator User",
        role=UserRole.OPERATOR,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_token(test_user: User) -> str:
    """Generate access token for test user"""
    return create_access_token(
        data={
            "sub": str(test_user.id),
            "username": test_user.username,
            "role": test_user.role.value,
        }
    )


@pytest.fixture
async def admin_token(admin_user: User) -> str:
    """Generate access token for admin user"""
    return create_access_token(
        data={
            "sub": str(admin_user.id),
            "username": admin_user.username,
            "role": admin_user.role.value,
        }
    )


@pytest.fixture
async def operator_token(operator_user: User) -> str:
    """Generate access token for operator user"""
    return create_access_token(
        data={
            "sub": str(operator_user.id),
            "username": operator_user.username,
            "role": operator_user.role.value,
        }
    )


@pytest.fixture
async def auth_headers(user_token: str) -> dict:
    """Create authorization headers with user token"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
async def admin_headers(admin_token: str) -> dict:
    """Create authorization headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
async def operator_headers(operator_token: str) -> dict:
    """Create authorization headers with operator token"""
    return {"Authorization": f"Bearer {operator_token}"}
