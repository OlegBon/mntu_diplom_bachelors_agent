from collections.abc import Generator
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend import main, models
from backend.database import Base
from backend.security import get_password_hash


@pytest.fixture(scope="session")
def test_engine():
    """In-memory SQLite engine isolated from local MariaDB/XAMPP data."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(
        schema_translate_map={
            "diamond_oltp": None,
            "diamond_market": None,
            "diamond_analytics": None,
        }
    )
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(test_engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    main.app.dependency_overrides[main.get_db] = override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


def create_expert(
    db_session: Session,
    *,
    username: str,
    password: str = "test-password",
    role: str = "gemologist",
) -> models.Expert:
    expert = models.Expert(
        username=username,
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash(password),
        role=role,
    )
    db_session.add(expert)
    db_session.commit()
    db_session.refresh(expert)
    return expert


@pytest.fixture
def experts(db_session: Session) -> dict[str, models.Expert]:
    return {
        "admin": create_expert(db_session, username="test-admin", role="admin"),
        "owner": create_expert(db_session, username="test-owner"),
        "other": create_expert(db_session, username="test-other"),
    }


def auth_headers(client: TestClient, username: str, password: str = "test-password") -> dict[str, str]:
    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def report(db_session: Session, experts: dict[str, models.Expert]) -> models.DiamondReport:
    created_report = models.DiamondReport(
        report_id="DR-TEST-00001",
        report_date=datetime(2026, 1, 1, 12, 0),
        shape="Round",
        carat_weight=Decimal("1.00"),
        color_grade=1,
        clarity_grade=1,
        cut_grade=0,
        polish_grade=0,
        symmetry_grade=0,
        proportions_grade=0,
        fluorescence_grade=0,
        stone_origin=0,
        expert_id=experts["owner"].expert_id,
        evaluation_time_sec=600,
        price=Decimal("1000.00"),
        is_sold=False,
    )
    db_session.add(created_report)
    db_session.commit()
    db_session.refresh(created_report)
    return created_report
