"""
FastAPI Application Factory.

Creates and configures the FastAPI app with:
- CORS middleware
- Request logging
- API routes
- OpenAPI documentation
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Application factory."""
    
    app = FastAPI(
        title="USMLE Agentic AI System",
        description="""
## Multi-Agent USMLE Study Planning System
        
An adaptive, multi-agent AI system that personalizes USMLE study schedules 
based on student performance using LangGraph orchestration.

### Architecture
- **Diagnostician Agent**: Parses NBME/UWorld reports using Groq/Llama-3
- **Knowledge Manager**: Maintains persistent knowledge vectors in Supabase
- **Adaptive Scheduler**: Generates interleaved study plans with spaced repetition

### Key Features
- Stateful agentic graph (LangGraph)
- Human-in-the-loop review capability
- Evidence-based learning strategies
- Persistent progress tracking
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router)
    
    @app.get("/")
    async def root():
        return {
            "name": "USMLE Agentic AI System",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "running"
        }
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("USMLE Agentic AI System starting up")
        logger.info(f"Environment: Development")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("USMLE Agentic AI System shutting down")
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
