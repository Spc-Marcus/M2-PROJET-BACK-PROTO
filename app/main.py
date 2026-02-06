"""FastAPI application for Duobingo."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine, Base
from app.api.routes import (
    auth,
    classrooms,
    modules,
    quizzes,
    questions,
    sessions,
    leitner,
    stats,
    progress,
    media,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown: Clean up resources
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["Classrooms"])
app.include_router(modules.router, prefix="/api/modules", tags=["Modules"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["Quizzes"])
app.include_router(questions.router, prefix="/api/quizzes", tags=["Questions"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Quiz Sessions"])
app.include_router(leitner.router, prefix="/api", tags=["Leitner"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(media.router, prefix="/api/media", tags=["Media"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
