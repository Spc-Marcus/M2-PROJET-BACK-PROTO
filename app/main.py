"""FastAPI application for Duobingo."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 400 instead of 422 for validation errors, with 'error' key."""
    return JSONResponse(
        status_code=400,
        content={"error": "Validation error", "detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return error responses with 'error' key for consistency."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(auth.users_router, tags=["Users"])
app.include_router(auth.admin_router, tags=["Admin"])
app.include_router(classrooms.router, prefix="/classrooms", tags=["Classrooms"])
app.include_router(modules.router, tags=["Modules"])
app.include_router(quizzes.router, tags=["Quizzes"])
app.include_router(questions.router, tags=["Questions"])
app.include_router(sessions.router, prefix="/sessions", tags=["Quiz Sessions"])
app.include_router(leitner.router, tags=["Leitner"])
app.include_router(stats.router, prefix="/stats", tags=["Statistics"])
app.include_router(progress.router, prefix="/progress", tags=["Progress"])
app.include_router(media.router, prefix="/media", tags=["Media"])


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
