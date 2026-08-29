from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.session import Base, engine
from app import models  # noqa: F401
from app.api.auth import router as auth_router
from app.api.scans import router as scans_router

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DevGuard AI API",
    version="1.0.0",
    description="AI-assisted secure code review and debugging platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:8080", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(scans_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "devguard-api", "environment": settings.app_env}
