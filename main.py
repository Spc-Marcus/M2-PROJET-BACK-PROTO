"""
Main FastAPI application - Duobingo Backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
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
    media
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth.router)
    app.include_router(classrooms.router)
    app.include_router(modules.router)
    app.include_router(quizzes.router)
    app.include_router(questions.router)
    app.include_router(sessions.router)
    app.include_router(leitner.router)
    app.include_router(stats.router)
    app.include_router(progress.router)
    app.include_router(media.router)
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to Duobingo API",
            "version": settings.APP_VERSION,
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


app = create_app()
