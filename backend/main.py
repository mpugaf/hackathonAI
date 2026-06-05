import logging
from contextlib import asynccontextmanager

import urllib3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.database import Base, SessionLocal, engine
from db.seed import run_seed_if_empty
from middleware.logging_middleware import LoggingMiddleware
from models import AuditLog, Project, Requirement, RequirementVersion, Review, User
from routers.auth import router as auth_router
from routers.projects import router as projects_router
from routers.requirements import router as requirements_router

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

_loaded_models = (AuditLog, Project, Requirement, RequirementVersion, Review, User)


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    if settings.ENVIRONMENT in {"development", "test"}:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            run_seed_if_empty(db)
        finally:
            db.close()
    logger.info("ReqFlow AI API started")
    yield
    logger.info("ReqFlow AI API stopped")


app = FastAPI(
    title="ReqFlow AI API",
    version="1.0.0",
    description="Herramienta de requisitos asistida por IA - TCS AI Fridays 2026",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
        "http://192.168.83.104:3000",  # acceso desde la red local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(requirements_router, prefix="/requirements", tags=["Requirements"])
app.include_router(projects_router, prefix="/projects", tags=["Projects"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}
