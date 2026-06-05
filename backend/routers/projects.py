from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.project import Project
from models.user import User
from schemas.project import ProjectCreate, ProjectOut
from services.audit_service import log_action
from services.auth_service import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=list[ProjectOut])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProjectOut]:
    del current_user
    return db.query(Project).filter(Project.is_active.is_(True)).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    request: Request,
    current_user: User = Depends(require_role(["analista"])),
    db: Session = Depends(get_db),
) -> Project:
    project = Project(title=payload.title, description=payload.description, created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    log_action(db, current_user.id, "project.created", "project", project.id, ip_address=request.client.host if request.client else None)
    return project
