import logging
import uuid

from sqlalchemy.orm import Session

from models.project import Project
from models.requirement import Requirement
from models.user import User
from services.auth_service import hash_password

logger = logging.getLogger(__name__)


def run_seed_if_empty(db: Session) -> None:
    if db.query(User).first():
        return

    analista = User(
        id=uuid.UUID("a0000000-0000-0000-0000-000000000001"),
        email="analista@tcs.com",
        password_hash=hash_password("analista123"),
        full_name="Ana Gonzalez (Demo Analista)",
        role="analista",
    )
    revisor = User(
        id=uuid.UUID("a0000000-0000-0000-0000-000000000002"),
        email="revisor@tcs.com",
        password_hash=hash_password("revisor123"),
        full_name="Roberto Campos (Demo Revisor)",
        role="revisor",
    )
    project = Project(
        id=uuid.UUID("b0000000-0000-0000-0000-000000000001"),
        title="Portal E-Commerce TCS Demo",
        description="Proyecto de demostracion: sitio web B2C de productos cosmeticos.",
        created_by=analista.id,
    )
    requirement = Requirement(
        title="Modulo de Catalogo de Productos",
        raw_input=(
            "Crear un modulo que permita a los clientes explorar el catalogo de productos "
            "cosmeticos con filtros por categoria, precio y marca. Debe incluir busqueda, "
            "vista detalle del producto y agregar al carrito."
        ),
        project_id=project.id,
        created_by=analista.id,
        status="borrador",
    )
    db.add_all([analista, revisor, project, requirement])
    db.commit()
    logger.info("Seed completado: 2 usuarios, 1 proyecto, 1 requisito demo")
