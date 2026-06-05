import uuid

from db.database import SessionLocal
from models.requirement import Requirement


PROJECT_ID = "20000000-0000-0000-0000-000000000001"
REQ_ID = "30000000-0000-0000-0000-000000000001"


def test_create_requirement_as_analista(client, analista_token):
    response = client.post(
        "/requirements",
        headers={"Authorization": f"Bearer {analista_token}"},
        json={
            "project_id": PROJECT_ID,
            "title": "Catalogo de productos",
            "raw_input": "Crear catalogo con filtros, busqueda y vista detalle para productos.",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "borrador"


def test_create_requirement_as_revisor(client, revisor_token):
    response = client.post(
        "/requirements",
        headers={"Authorization": f"Bearer {revisor_token}"},
        json={
            "project_id": PROJECT_ID,
            "title": "Catalogo de productos",
            "raw_input": "Crear catalogo con filtros, busqueda y vista detalle para productos.",
        },
    )
    assert response.status_code == 403


def test_get_requirements_list(client, analista_token, sample_requirement):
    response = client.get("/requirements", headers={"Authorization": f"Bearer {analista_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_requirement_detail(client, analista_token, sample_requirement):
    response = client.get(f"/requirements/{REQ_ID}", headers={"Authorization": f"Bearer {analista_token}"})
    assert response.status_code == 200
    assert response.json()["id"] == REQ_ID


def test_update_requirement_borrador(client, analista_token, sample_requirement):
    response = client.put(
        f"/requirements/{REQ_ID}",
        headers={"Authorization": f"Bearer {analista_token}"},
        json={"title": "Requisito actualizado"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Requisito actualizado"


def test_update_requirement_aprobado(client, analista_token, sample_requirement):
    db = SessionLocal()
    req = db.get(Requirement, uuid.UUID(REQ_ID))
    req.status = "aprobado"
    db.commit()
    db.close()
    response = client.put(
        f"/requirements/{REQ_ID}",
        headers={"Authorization": f"Bearer {analista_token}"},
        json={"title": "No editable"},
    )
    assert response.status_code == 409


def test_approve_as_revisor(client, revisor_token, sample_requirement, sample_version):
    db = SessionLocal()
    req = db.get(Requirement, uuid.UUID(REQ_ID))
    req.status = "en_revision"
    db.commit()
    db.close()
    response = client.post(f"/requirements/{REQ_ID}/approve", headers={"Authorization": f"Bearer {revisor_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "aprobado"


def test_approve_as_analista(client, analista_token, sample_requirement, sample_version):
    response = client.post(f"/requirements/{REQ_ID}/approve", headers={"Authorization": f"Bearer {analista_token}"})
    assert response.status_code == 403
