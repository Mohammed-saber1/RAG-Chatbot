"""FastAPI application entry point with security middleware."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, documents
from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService


# Configure logging — no sensitive data in logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    settings = get_settings()

    # Initialize services
    logger.info("Starting RAG Chatbot backend...")

    # Document processor
    doc_processor = DocumentProcessor(settings)
    app.state.doc_processor = doc_processor

    # RAG service (embeddings + vector store + LLM)
    rag_service = RAGService(settings)
    await rag_service.initialize()
    app.state.rag_service = rag_service

    logger.info("Backend initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down RAG Chatbot backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="RAG Chatbot API",
        description="AI chatbot that answers questions from uploaded documents using Retrieval-Augmented Generation.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware — restricted to allowed origins only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins_list(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next) -> Response:
        """Add security headers to all responses."""
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        # CSP — restrictive policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'"
        )
        return response

    # Register routers
    app.include_router(chat.router)
    app.include_router(documents.router)

    # Health check endpoint
    @app.get("/api/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()
