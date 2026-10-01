import pytest
from fakeredis import FakeRedis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.runtime import get_redis
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def test_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture
def fake_redis():
    return FakeRedis(decode_responses=False)


@pytest.fixture
def client(test_session_factory, fake_redis):
    def override_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = lambda: fake_redis
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
