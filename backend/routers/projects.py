import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.project import Project
from models.requirement import Requirement
from models.user import User
from schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from services.audit_service import log_action
from services.auth_service import get_current_user, require_role

router = APIRouter()


def _get_project(db: Session, project_id: uuid.UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.is_active.is_(True)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProjectOut]:
    del current_user
    return db.query(Project).filter(Project.is_active.is_(True)).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    request: Request,
    current_user: User = Depends(require_role(["analista", "revisor"])),
    db: Session = Depends(get_db),
) -> Project:
    project = Project(title=payload.title, description=payload.description, created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    log_action(db, current_user.id, "project.created", "project", project.id, ip_address=request.client.host if request.client else None)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    del current_user
    return _get_project(db, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    request: Request,
    current_user: User = Depends(require_role(["revisor"])),
    db: Session = Depends(get_db),
) -> Project:
    project = _get_project(db, project_id)
    if payload.title is not None:
        project.title = payload.title
    if payload.description is not None:
        project.description = payload.description
    db.commit()
    db.refresh(project)
    log_action(db, current_user.id, "project.updated", "project", project.id, ip_address=request.client.host if request.client else None)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_role(["revisor"])),
    db: Session = Depends(get_db),
) -> None:
    project = _get_project(db, project_id)
    has_requirements = db.query(Requirement).filter(Requirement.project_id == project_id).first()
    if has_requirements:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un proyecto con requisitos asociados",
        )
    project.is_active = False
    db.commit()
    log_action(db, current_user.id, "project.deleted", "project", project.id, ip_address=request.client.host if request.client else None)
