import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.api.routes import router
from app.core.config import get_settings
from app.seeds.seed_demand_fr import fr_consumer_queries
from app.data.seed_queries import all_queries
from app.data.seed_whatsapp_blitz import blitz_queries
from app.data.seed_b2b import b2b_queries
from app.data.seed_social import social_queries
from app.data.seed_yield import yield_queries
from app.db.migrate import ensure_schema, reclaim_stale_url_jobs
from app.db.session import Base, SessionLocal, engine
from app.models import Contact, ConsumerLead, DiscoveredUrl, Evidence, JobRun, SearchQuery, Supplier, SystemMetric  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("wareach")
settings = get_settings()


def upsert_search_queries() -> int:
    """Insert any new seed queries without wiping existing run history."""
    db = SessionLocal()
    try:
        existing = {q for q in db.scalars(select(SearchQuery.query)).all()}
        added = 0
        for item in (
            list(all_queries())
            + list(blitz_queries())
            + list(b2b_queries())
            + list(social_queries())
            + list(yield_queries())
            + list(fr_consumer_queries())
        ):
            if item["query"] in existing:
                continue
            db.add(
                SearchQuery(
                    query=item["query"],
                    brand=item["brand"],
                    locale=item.get("locale", "zh"),
                    platform_hint=item.get("platform_hint", "web"),
                    category=item.get("category", "general"),
                    priority=item.get("priority", 100),
                    enabled=True,
                )
            )
            added += 1
            existing.add(item["query"])
        db.commit()
        total = db.scalar(select(func.count()).select_from(SearchQuery)) or 0
        if added:
            logger.info("Upserted %s new search queries (total=%s)", added, total)
        return added
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    n = reclaim_stale_url_jobs()
    if n:
        logger.info("Startup reclaimed %s stuck URL jobs", n)
    upsert_search_queries()
    from app.services.autopilot import start_autopilot_thread
    from app.services.demand_autopilot import start_demand_autopilot_thread

    start_autopilot_thread()
    start_demand_autopilot_thread()
    logger.info(
        "%s v2 ready — supply autopilot + demand autopilot ON — brands=%s",
        settings.app_name,
        settings.brand_list,
    )
    yield
    from app.services.autopilot import stop_autopilot_thread
    from app.services.demand_autopilot import stop_demand_autopilot_thread

    stop_autopilot_thread()
    stop_demand_autopilot_thread()


app = FastAPI(
    title="WAREACH",
    description=(
        "Enterprise brand-protection OSINT for LVMH, Richemont and peer maisons. "
        "Detects HQ replicas (god-tier) and China jewelry OEM factories (Cartier, VCA, Tiffany…). "
        "Powered by Agent Reach (Exa + Jina), Firecrawl, Playwright."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "WAREACH",
        "version": "2.0.0",
        "clients": ["LVMH", "Richemont", "peer maisons"],
        "focus": [
            "hq_replica_sellers",
            "jewelry_factories_shuibei_panyu",
            "real_gold_diamond_oem",
        ],
        "docs": "/docs",
        "api": "/api/health",
    }
