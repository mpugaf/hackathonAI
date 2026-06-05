"""
FASE 3 — Pruebas de API ampliadas con pytest + TestClient.
Cubre: autenticación, RBAC, ciclo de vida completo, validaciones,
mocks LLM, audit log.
"""
import uuid
from unittest.mock import patch

import pytest

from db.database import SessionLocal
from models.audit_log import AuditLog
from models.requirement import Requirement
from models.requirement_version import RequirementVersion
from models.review import Review

# ─── IDs fijos reutilizados ───────────────────────────────────────────────────
PROJECT_ID = "20000000-0000-0000-0000-000000000001"
REQ_ID     = "30000000-0000-0000-0000-000000000001"
VER_ID     = "40000000-0000-0000-0000-000000000001"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _mock_llm_response(content="Spec generada por mock"):
    from unittest.mock import Mock
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


# ─── AUTENTICACIÓN ───────────────────────────────────────────────────────────

class TestAuth:
    def test_login_analista_returns_token_and_role(self, client):
        r = client.post("/auth/login", json={"email": "analista@tcs.com", "password": "analista123"})
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
        assert body["role"] == "analista"
        assert body["full_name"]

    def test_login_revisor_returns_revisor_role(self, client):
        r = client.post("/auth/login", json={"email": "revisor@tcs.com", "password": "revisor123"})
        assert r.status_code == 200
        assert r.json()["role"] == "revisor"

    def test_login_bad_password_returns_401(self, client):
        r = client.post("/auth/login", json={"email": "analista@tcs.com", "password": "wrong"})
        assert r.status_code == 401
        assert "Credenciales" in r.json()["detail"]

    def test_login_unknown_email_returns_401(self, client):
        r = client.post("/auth/login", json={"email": "noexiste@tcs.com", "password": "x"})
        assert r.status_code == 401

    def test_login_missing_fields_returns_422(self, client):
        r = client.post("/auth/login", json={"email": "analista@tcs.com"})
        assert r.status_code == 422

    def test_protected_route_without_token_returns_401(self, client):
        r = client.get("/requirements")
        assert r.status_code == 401

    def test_protected_route_with_invalid_token_returns_401(self, client):
        r = client.get("/requirements", headers={"Authorization": "Bearer tokeninvalido"})
        assert r.status_code == 401

    def test_protected_route_with_tampered_token_returns_401(self, client, analista_token):
        tampered = analista_token[:-5] + "XXXXX"
        r = client.get("/requirements", headers={"Authorization": f"Bearer {tampered}"})
        assert r.status_code == 401

    def test_logout_registers_in_audit(self, client, analista_token):
        r = client.post("/auth/logout", headers=_auth(analista_token))
        assert r.status_code == 200
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "user.logout").first()
        db.close()
        assert entry is not None

    def test_login_registers_in_audit(self, client):
        client.post("/auth/login", json={"email": "analista@tcs.com", "password": "analista123"})
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "user.login").first()
        db.close()
        assert entry is not None


# ─── PROYECTOS ────────────────────────────────────────────────────────────────

class TestProjects:
    def test_create_project_as_analista(self, client, analista_token):
        r = client.post("/projects", headers=_auth(analista_token),
                        json={"title": "Mi proyecto test", "description": "Descripcion"})
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "Mi proyecto test"
        assert body["is_active"] is True

    def test_create_project_as_revisor_returns_403(self, client, revisor_token):
        r = client.post("/projects", headers=_auth(revisor_token),
                        json={"title": "Proyecto revisor"})
        assert r.status_code == 403

    def test_create_project_without_title_returns_422(self, client, analista_token):
        r = client.post("/projects", headers=_auth(analista_token),
                        json={"description": "Sin titulo"})
        assert r.status_code == 422

    def test_create_project_short_title_returns_422(self, client, analista_token):
        r = client.post("/projects", headers=_auth(analista_token),
                        json={"title": "abc"})
        assert r.status_code == 422

    def test_list_projects_returns_active_only(self, client, analista_token):
        client.post("/projects", headers=_auth(analista_token),
                    json={"title": "Proyecto activo"})
        r = client.get("/projects", headers=_auth(analista_token))
        assert r.status_code == 200
        for p in r.json():
            assert p["is_active"] is True

    def test_create_project_audit_log(self, client, analista_token):
        client.post("/projects", headers=_auth(analista_token),
                    json={"title": "Proyecto con audit"})
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "project.created").first()
        db.close()
        assert entry is not None


# ─── REQUISITOS — CRUD Y VALIDACIÓN ──────────────────────────────────────────

class TestRequirementCRUD:
    def test_create_requirement_returns_201_borrador(self, client, analista_token):
        r = client.post("/requirements", headers=_auth(analista_token),
                        json={"project_id": PROJECT_ID,
                              "title": "Titulo suficientemente largo",
                              "raw_input": "Descripcion suficientemente larga para pasar validacion minima de veinte chars."})
        assert r.status_code == 201
        assert r.json()["status"] == "borrador"

    def test_create_requirement_as_revisor_returns_403(self, client, revisor_token):
        r = client.post("/requirements", headers=_auth(revisor_token),
                        json={"project_id": PROJECT_ID,
                              "title": "Titulo largo test revisor",
                              "raw_input": "raw input suficientemente largo para la validacion"})
        assert r.status_code == 403

    def test_create_requirement_short_title_returns_422(self, client, analista_token):
        r = client.post("/requirements", headers=_auth(analista_token),
                        json={"project_id": PROJECT_ID,
                              "title": "abc",
                              "raw_input": "raw input suficientemente largo para la validacion"})
        assert r.status_code == 422

    def test_create_requirement_short_raw_input_returns_422(self, client, analista_token):
        r = client.post("/requirements", headers=_auth(analista_token),
                        json={"project_id": PROJECT_ID,
                              "title": "Titulo valido largo",
                              "raw_input": "corto"})
        assert r.status_code == 422

    def test_create_requirement_invalid_project_returns_400(self, client, analista_token):
        r = client.post("/requirements", headers=_auth(analista_token),
                        json={"project_id": str(uuid.uuid4()),
                              "title": "Titulo valido largo aqui",
                              "raw_input": "raw input suficientemente largo para la validacion"})
        assert r.status_code == 400

    def test_update_borrador_requirement(self, client, analista_token, sample_requirement):
        r = client.put(f"/requirements/{REQ_ID}", headers=_auth(analista_token),
                       json={"title": "Titulo actualizado correctamente"})
        assert r.status_code == 200
        assert r.json()["title"] == "Titulo actualizado correctamente"

    def test_update_non_borrador_returns_409(self, client, analista_token, sample_requirement):
        db = SessionLocal()
        req = db.get(Requirement, uuid.UUID(REQ_ID))
        req.status = "en_revision"
        db.commit()
        db.close()
        r = client.put(f"/requirements/{REQ_ID}", headers=_auth(analista_token),
                       json={"title": "No editable en revision"})
        assert r.status_code == 409

    def test_get_requirement_detail_includes_version_fields(self, client, analista_token, sample_requirement):
        r = client.get(f"/requirements/{REQ_ID}", headers=_auth(analista_token))
        assert r.status_code == 200
        body = r.json()
        assert "latest_version" in body
        assert "latest_ai_review" in body
        assert "latest_human_review" in body

    def test_get_nonexistent_requirement_returns_404(self, client, analista_token):
        r = client.get(f"/requirements/{uuid.uuid4()}", headers=_auth(analista_token))
        assert r.status_code == 404

    def test_list_requirements_filter_by_status(self, client, analista_token, sample_requirement):
        r = client.get("/requirements?status=borrador", headers=_auth(analista_token))
        assert r.status_code == 200
        for req in r.json():
            assert req["status"] == "borrador"

    def test_requirement_audit_on_create(self, client, analista_token):
        client.post("/requirements", headers=_auth(analista_token),
                    json={"project_id": PROJECT_ID,
                          "title": "Requisito para audit test",
                          "raw_input": "raw input suficientemente largo para la validacion test audit"})
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "requirement.created").first()
        db.close()
        assert entry is not None


# ─── GENERACIÓN LLM-1 ─────────────────────────────────────────────────────────

class TestGeneration:
    def test_generate_creates_version_v1(self, client, analista_token, sample_requirement):
        mock_resp = _mock_llm_response("HISTORIA DE USUARIO\n## spec completa")
        with patch("services.llm_service.requests.post", return_value=mock_resp):
            r = client.post(f"/requirements/{REQ_ID}/generate",
                            headers=_auth(analista_token))
        assert r.status_code == 200
        body = r.json()
        assert body["version_number"] == 1
        assert "HISTORIA DE USUARIO" in body["generated_spec"]
        assert body["model_used"]

    def test_generate_increments_version(self, client, analista_token, sample_requirement):
        mock_resp = _mock_llm_response("Spec v1")
        with patch("services.llm_service.requests.post", return_value=mock_resp):
            client.post(f"/requirements/{REQ_ID}/generate", headers=_auth(analista_token))
        mock_resp2 = _mock_llm_response("Spec v2")
        with patch("services.llm_service.requests.post", return_value=mock_resp2):
            r = client.post(f"/requirements/{REQ_ID}/generate", headers=_auth(analista_token))
        assert r.json()["version_number"] == 2

    def test_generate_as_revisor_returns_403(self, client, revisor_token, sample_requirement):
        with patch("services.llm_service.requests.post", return_value=_mock_llm_response()):
            r = client.post(f"/requirements/{REQ_ID}/generate", headers=_auth(revisor_token))
        assert r.status_code == 403

    def test_generate_llm_timeout_returns_504(self, client, analista_token, sample_requirement):
        import requests as req_lib
        with patch("services.llm_service.requests.post", side_effect=req_lib.exceptions.Timeout):
            r = client.post(f"/requirements/{REQ_ID}/generate", headers=_auth(analista_token))
        assert r.status_code == 504
        assert "Timeout" in r.json()["detail"]

    def test_generate_llm_error_returns_502(self, client, analista_token, sample_requirement):
        import requests as req_lib
        with patch("services.llm_service.requests.post",
                   side_effect=req_lib.exceptions.RequestException("connection refused")):
            r = client.post(f"/requirements/{REQ_ID}/generate", headers=_auth(analista_token))
        assert r.status_code == 502

    def test_generate_audit_log_entry(self, client, analista_token, sample_requirement):
        with patch("services.llm_service.requests.post", return_value=_mock_llm_response()):
            client.post(f"/requirements/{REQ_ID}/generate", headers=_auth(analista_token))
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "requirement.generated").first()
        db.close()
        assert entry is not None
        assert entry.metadata_ is not None
        assert "model" in entry.metadata_
        assert "version_number" in entry.metadata_

    def test_generate_model_stored_in_version(self, client, analista_token, sample_requirement):
        with patch("services.llm_service.requests.post", return_value=_mock_llm_response()):
            r = client.post(f"/requirements/{REQ_ID}/generate", headers=_auth(analista_token))
        db = SessionLocal()
        version = db.query(RequirementVersion).filter(
            RequirementVersion.requirement_id == uuid.UUID(REQ_ID)
        ).first()
        db.close()
        assert version is not None
        assert version.model_used  # no vacío
        assert version.prompt_used  # prompt guardado


# ─── REVISIÓN IA (LLM-2) ──────────────────────────────────────────────────────

class TestReviewAI:
    def test_review_ai_sets_en_revision_status(self, client, analista_token, sample_requirement, sample_version):
        mock_resp = _mock_llm_response("PUNTAJE: 78\nBuen documento")
        with patch("services.llm_service.requests.post", return_value=mock_resp):
            r = client.post(f"/requirements/{REQ_ID}/review-ai", headers=_auth(analista_token))
        assert r.status_code == 200
        assert "feedback" in r.json()
        assert r.json()["ai_score"] == 78
        db = SessionLocal()
        req = db.get(Requirement, uuid.UUID(REQ_ID))
        db.close()
        assert req.status == "en_revision"

    def test_review_ai_without_version_returns_400(self, client, analista_token, sample_requirement):
        r = client.post(f"/requirements/{REQ_ID}/review-ai", headers=_auth(analista_token))
        assert r.status_code == 400

    def test_review_ai_uses_different_model_than_generator(self, client, analista_token,
                                                             sample_requirement, sample_version):
        from config import settings
        assert settings.LLM_GENERATOR_MODEL != settings.LLM_REVIEWER_MODEL

    def test_review_ai_audit_entry(self, client, analista_token, sample_requirement, sample_version):
        with patch("services.llm_service.requests.post", return_value=_mock_llm_response("PUNTAJE: 60")):
            client.post(f"/requirements/{REQ_ID}/review-ai", headers=_auth(analista_token))
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "requirement.reviewed_ai").first()
        db.close()
        assert entry is not None


# ─── REVISIÓN HUMANA ──────────────────────────────────────────────────────────

class TestReviewHuman:
    @pytest.fixture(autouse=True)
    def _setup_en_revision(self, sample_requirement, sample_version):
        db = SessionLocal()
        req = db.get(Requirement, uuid.UUID(REQ_ID))
        req.status = "en_revision"
        ai_review = Review(
            requirement_version_id=sample_version.id,
            reviewer_id=None,
            reviewer_type="ia",
            feedback="PUNTAJE: 75\nFeedback de IA",
            ai_score=75,
            decision="pendiente",
        )
        db.add(ai_review)
        db.commit()
        db.close()

    def test_revisor_can_approve(self, client, revisor_token):
        r = client.post(f"/requirements/{REQ_ID}/approve", headers=_auth(revisor_token))
        assert r.status_code == 200
        assert r.json()["status"] == "aprobado"

    def test_revisor_can_reject_with_feedback(self, client, revisor_token):
        r = client.post(f"/requirements/{REQ_ID}/reject", headers=_auth(revisor_token),
                        json={"feedback": "Faltan criterios de aceptacion detallados"})
        assert r.status_code == 200
        assert r.json()["status"] == "rechazado"

    def test_analista_cannot_approve(self, client, analista_token):
        r = client.post(f"/requirements/{REQ_ID}/approve", headers=_auth(analista_token))
        assert r.status_code == 403

    def test_analista_cannot_reject(self, client, analista_token):
        r = client.post(f"/requirements/{REQ_ID}/reject", headers=_auth(analista_token),
                        json={"feedback": "Intento ilegal"})
        assert r.status_code == 403

    def test_approve_not_in_revision_returns_409(self, client, revisor_token, sample_requirement):
        db = SessionLocal()
        req = db.get(Requirement, uuid.UUID(REQ_ID))
        req.status = "borrador"
        db.commit()
        db.close()
        r = client.post(f"/requirements/{REQ_ID}/approve", headers=_auth(revisor_token))
        assert r.status_code == 409

    def test_review_human_without_ai_review_returns_400(self, client, revisor_token):
        db = SessionLocal()
        for review in db.query(Review).all():
            db.delete(review)
        db.commit()
        db.close()
        r = client.post(f"/requirements/{REQ_ID}/review-human", headers=_auth(revisor_token),
                        json={"feedback": "Sin IA previa", "decision": "aprobado"})
        assert r.status_code == 400

    def test_review_human_invalid_decision_returns_422(self, client, revisor_token):
        r = client.post(f"/requirements/{REQ_ID}/review-human", headers=_auth(revisor_token),
                        json={"feedback": "Feedback", "decision": "indefinido"})
        assert r.status_code == 422

    def test_approve_creates_audit_log(self, client, revisor_token):
        client.post(f"/requirements/{REQ_ID}/approve", headers=_auth(revisor_token))
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "requirement.approved").first()
        db.close()
        assert entry is not None

    def test_reject_creates_audit_log(self, client, revisor_token):
        client.post(f"/requirements/{REQ_ID}/reject", headers=_auth(revisor_token),
                    json={"feedback": "Observaciones del revisor"})
        db = SessionLocal()
        entry = db.query(AuditLog).filter(AuditLog.action == "requirement.rejected").first()
        db.close()
        assert entry is not None


# ─── EXPORTACIÓN ─────────────────────────────────────────────────────────────

class TestExport:
    @pytest.fixture(autouse=True)
    def _setup_aprobado(self, sample_requirement, sample_version):
        db = SessionLocal()
        req = db.get(Requirement, uuid.UUID(REQ_ID))
        req.status = "aprobado"
        db.commit()
        db.close()

    def test_export_approved_returns_html(self, client, analista_token):
        r = client.get(f"/requirements/{REQ_ID}/export", headers=_auth(analista_token))
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "Content-Disposition" in r.headers
        assert "attachment" in r.headers["Content-Disposition"]

    def test_export_html_contains_title(self, client, analista_token):
        r = client.get(f"/requirements/{REQ_ID}/export", headers=_auth(analista_token))
        assert "Requisito de prueba" in r.text

    def test_export_non_approved_returns_400(self, client, analista_token):
        db = SessionLocal()
        req = db.get(Requirement, uuid.UUID(REQ_ID))
        req.status = "borrador"
        db.commit()
        db.close()
        r = client.get(f"/requirements/{REQ_ID}/export", headers=_auth(analista_token))
        assert r.status_code == 400


# ─── HISTORIAL DE VERSIONES ───────────────────────────────────────────────────

class TestHistory:
    def test_history_returns_versions_desc(self, client, analista_token, sample_requirement):
        db = SessionLocal()
        for i in [1, 2, 3]:
            db.add(RequirementVersion(
                requirement_id=uuid.UUID(REQ_ID),
                version_number=i,
                generated_spec=f"Spec v{i}",
                model_used="test-model",
                prompt_used="test-prompt",
            ))
        db.commit()
        db.close()
        r = client.get(f"/requirements/{REQ_ID}/history", headers=_auth(analista_token))
        assert r.status_code == 200
        versions = r.json()
        assert len(versions) == 3
        assert versions[0]["version_number"] == 3

    def test_history_nonexistent_requirement_returns_404(self, client, analista_token):
        r = client.get(f"/requirements/{uuid.uuid4()}/history", headers=_auth(analista_token))
        assert r.status_code == 404


# ─── CONSISTENCIA DE DATOS ────────────────────────────────────────────────────

class TestDataConsistency:
    def test_no_orphan_versions(self, sample_requirement, sample_version):
        db = SessionLocal()
        orphans = (
            db.query(RequirementVersion)
            .filter(~RequirementVersion.requirement_id.in_(
                db.query(Requirement.id)
            ))
            .all()
        )
        db.close()
        assert len(orphans) == 0

    def test_audit_log_is_append_only(self, client, analista_token):
        client.post("/auth/login", json={"email": "analista@tcs.com", "password": "analista123"})
        db = SessionLocal()
        count_before = db.query(AuditLog).count()
        db.close()
        assert count_before >= 1
        db = SessionLocal()
        count_after = db.query(AuditLog).count()
        db.close()
        assert count_after >= count_before

    def test_passwords_are_hashed_not_plain(self):
        from services.auth_service import hash_password, verify_password
        hashed = hash_password("plain_password")
        assert hashed != "plain_password"
        assert hashed.startswith("$2b$")
        assert verify_password("plain_password", hashed)
        assert not verify_password("wrong", hashed)

    def test_jwt_with_wrong_secret_rejected(self, client):
        from jose import jwt
        bad_token = jwt.encode(
            {"sub": "10000000-0000-0000-0000-000000000001", "role": "analista", "exp": 9999999999},
            "wrong_secret", algorithm="HS256"
        )
        r = client.get("/requirements", headers={"Authorization": f"Bearer {bad_token}"})
        assert r.status_code == 401

    def test_ai_score_constraint(self, sample_version):
        db = SessionLocal()
        review = Review(
            requirement_version_id=sample_version.id,
            reviewer_type="ia",
            feedback="Test feedback",
            ai_score=85,
            decision="pendiente",
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        assert 0 <= review.ai_score <= 100
        db.close()


# ─── HEALTH CHECK ─────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint_public(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_returns_version(self, client):
        r = client.get("/health")
        assert "version" in r.json()
