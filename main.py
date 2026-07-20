from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from core.config import settings
from core.database import AsyncSessionLocal
from core.rate_limit import close_rate_limiter, get_redis, init_rate_limiter
from routes.ai.ai import ai_router
from routes.categories.categories import category_router
from routes.notes.notes import note_router
from routes.summaries.summaries import summary_router
from routes.users.users import user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_rate_limiter()
    yield
    await close_rate_limiter()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(category_router)
app.include_router(note_router)
app.include_router(summary_router)
app.include_router(ai_router)


@app.get("/health")
async def health():
    checks: dict[str, str] = {}

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        await get_redis().ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    healthy = all(value == "ok" for value in checks.values())
    return {
        "status": "ok" if healthy else "degraded",
        "checks": checks,
    }
