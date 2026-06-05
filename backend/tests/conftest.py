import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test_secret"
os.environ["TCS_API_KEY"] = "test_key"

from db.database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402
from models.project import Project  # noqa: E402
from models.requirement import Requirement  # noqa: E402
from models.requirement_version import RequirementVersion  # noqa: E402
from models.user import User  # noqa: E402
from services.auth_service import create_access_token, hash_password  # noqa: E402


@pytest.fixture(autouse=True)
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    analista = User(
        id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
        email="analista@tcs.com",
        password_hash=hash_password("analista123"),
        full_name="Ana Test",
        role="analista",
    )
    revisor = User(
        id=uuid.UUID("10000000-0000-0000-0000-000000000002"),
        email="revisor@tcs.com",
        password_hash=hash_password("revisor123"),
        full_name="Roberto Test",
        role="revisor",
    )
    project = Project(
        id=uuid.UUID("20000000-0000-0000-0000-000000000001"),
        title="Proyecto Test",
        description="Demo",
        created_by=analista.id,
    )
    db.add_all([analista, revisor, project])
    db.commit()
    db.close()
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def analista_token():
    return create_access_token({"sub": "10000000-0000-0000-0000-000000000001", "role": "analista", "email": "analista@tcs.com"})


@pytest.fixture()
def revisor_token():
    return create_access_token({"sub": "10000000-0000-0000-0000-000000000002", "role": "revisor", "email": "revisor@tcs.com"})


@pytest.fixture()
def auth_headers(analista_token):
    return {"Authorization": f"Bearer {analista_token}"}


@pytest.fixture()
def sample_requirement():
    db = SessionLocal()
    req = Requirement(
        id=uuid.UUID("30000000-0000-0000-0000-000000000001"),
        project_id=uuid.UUID("20000000-0000-0000-0000-000000000001"),
        title="Requisito de prueba",
        raw_input="Crear una funcion de prueba con texto suficiente para validar el flujo completo.",
        created_by=uuid.UUID("10000000-0000-0000-0000-000000000001"),
        status="borrador",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    db.close()
    return req


@pytest.fixture()
def sample_version(sample_requirement):
    db = SessionLocal()
    version = RequirementVersion(
        requirement_id=sample_requirement.id,
        version_number=1,
        generated_spec="Spec generada",
        model_used="test-model",
        prompt_used="test-prompt",
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    db.close()
    return version
