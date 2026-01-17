"""
FastAPI Main Application
Optimized for production with proper error handling, monitoring, and rate limiting
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from prometheus_client import generate_latest
from starlette.responses import Response

from app.api import chat, workflows, executions, auth, webhooks
from app.db.session import engine
from app.db.base import Base # Import Base from db.base to ensure all models are registered
from app.config import settings
from app.metrics import REQUEST_COUNT, REQUEST_DURATION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    # Startup
    logger.info("🚀 Starting AI Workflow Platform...")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
    except Exception as e:
        logger.warning(f"⚠️ Could not create tables on startup: {e}")

    # Initialize Redis connection
    try:
        from app.services.cache import init_redis
        await init_redis()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")

    # Load workflow templates
    from app.services.template_matcher import load_templates
    templates = await load_templates()
    logger.info(f"✅ Loaded {len(templates)} workflow templates")

    # Verify n8n connectivity
    try:
        from app.services.n8n_client import N8nClient
        n8n = N8nClient()
        if await n8n.health_check():
            logger.info("✅ n8n instance connected")
        else:
            logger.error("❌ n8n instance not reachable")
    except Exception as e:
        logger.warning(f"⚠️ n8n health check failed: {e}")

    yield

    # Shutdown
    logger.info("🛑 Shutting down gracefully...")
    from app.services.cache import close_redis
    await close_redis()


app = FastAPI(
    title="AI Workflow Platform API",
    description="Algerian Business Automation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request timing and metrics"""
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Process-Time"] = str(process_time)

        # Metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_DURATION.observe(process_time)

        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", exc_info=True)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with detailed logging"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Our team has been notified.",
            "request_id": request.headers.get("X-Request-ID")
        }
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    from app.services.cache import redis_client
    from app.db.session import SessionLocal

    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "n8n": "unknown"
    }

    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"

    # Check n8n
    try:
        from app.services.n8n_client import N8nClient
        n8n = N8nClient()
        if await n8n.health_check():
            checks["n8n"] = "healthy"
        else:
            checks["n8n"] = "unhealthy"
    except Exception as e:
        checks["n8n"] = f"unhealthy: {str(e)}"

    overall_healthy = all(v == "healthy" for v in checks.values())

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "checks": checks,
        "version": "1.0.0"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


# API Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Agent Chat"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(executions.router, prefix="/api/executions", tags=["Executions"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Workflow Platform",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4 if not settings.DEBUG else 1,
        log_level="info"
    )
