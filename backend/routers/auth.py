from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from schemas.auth import LoginRequest, TokenResponse
from services.audit_service import log_action
from services.auth_service import create_access_token, get_current_user, verify_password

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    log_action(db, user.id, "user.login", "user", user.id, ip_address=request.client.host if request.client else None)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/logout")
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    log_action(db, current_user.id, "user.logout", "user", current_user.id, ip_address=request.client.host if request.client else None)
    return {"message": "Logout registrado exitosamente"}
