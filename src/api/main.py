import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from src.api.routes.ask import router as ask_router
from src.api.routes.export import router as export_router
from src.api.routes.ingest import router as ingest_router
from src.api.routes.insights import router as insights_router
from src.api.routes.jobs import router as jobs_router
from src.api.routes.reviews import router as reviews_router
from src.api.routes.search import router as search_router
from src.api.routes.segments import router as segments_router
from src.api.routes.topics import router as topics_router
from src.observability.health import build_health_report
from src.observability.logging_config import configure_logging
from src.observability.middleware import RequestContextMiddleware

settings = get_settings()

configure_logging(level=settings.log_level, log_format=settings.log_format)
logger = logging.getLogger(__name__)

_cors_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Review Discovery Engine API")
    yield
    logger.info("Shutting down Review Discovery Engine API")


app = FastAPI(
    title="Review Discovery Engine",
    description="AI-powered review intelligence platform",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(insights_router)
app.include_router(ask_router)
app.include_router(reviews_router)
app.include_router(topics_router)
app.include_router(segments_router)
app.include_router(export_router)
app.include_router(ingest_router)
app.include_router(jobs_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
        extra={"request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
        headers={"X-Request-ID": request_id or ""},
    )


@app.get("/health")
def health_check(detailed: bool = Query(default=False)) -> dict:
    return build_health_report(detailed=detailed)
