from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WAREACH"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Default: SQLite for Mac zero-deps. Set postgres URL when Docker/Colima is up.
    database_url: str = f"sqlite:///{ROOT / 'data' / 'wareach.db'}"
    use_sqlite: bool = True
    redis_url: str = "redis://127.0.0.1:6379/0"
    celery_broker_url: str = "redis://127.0.0.1:6379/0"
    celery_result_backend: str = "redis://127.0.0.1:6379/1"

    agent_reach_bin: str = "agent-reach"
    mcporter_bin: str = "mcporter"
    jina_reader_prefix: str = "https://r.jina.ai/"
    exa_num_results: int = 15
    discovery_concurrency: int = 8
    crawl_concurrency: int = 8
    whatsapp_target: int = 10000
    blitz_workers: int = 8
    blitz_query_batch: int = 40
    request_timeout_sec: int = 45
    rate_limit_per_host: float = 2.0

    continuous_mode: bool = True
    discovery_interval_sec: int = 300
    crawl_interval_sec: int = 120
    max_queue_depth: int = 5000

    target_brands: str = (
        "louis_vuitton,dior,fendi,celine,tiffany,bulgari,"
        "cartier,van_cleef_arpels,piaget,chaumet,"
        "hermes,chanel,gucci,saint_laurent,bottega_veneta,rolex"
    )
    evidence_dir: str = str(ROOT / "data" / "evidence")

    # LuxFind FR façade (Phase 2 demand capture)
    facade_brand_name: str = "LuxFind FR"
    facade_telegram_url: str = "https://t.me/luxfindfr"
    facade_tagline: str = "Guide discret pour acheteurs exigeants"
    telegram_bot_token: str = ""

    # LuxMatch marketplace
    openai_api_key: str = ""
    luxmatch_public_url: str = "http://localhost:3001"
    luxmatch_upload_dir: str = str(ROOT / "data" / "luxmatch" / "uploads")
    luxmatch_blast_limit: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        for extra in ("http://localhost:3001", "http://127.0.0.1:3001"):
            if extra not in origins:
                origins.append(extra)
        return origins

    @property
    def brand_list(self) -> list[str]:
        return [b.strip() for b in self.target_brands.split(",") if b.strip()]

    @property
    def resolved_database_url(self) -> str:
        # Explicit sqlite URL wins; only default to local file when unset / placeholder
        url = (self.database_url or "").strip()
        if not self.use_sqlite and url and not url.startswith("sqlite"):
            return url
        if url.startswith("sqlite"):
            # Prefer new name; fall back to legacy luxguard.db if present
            if "wareach.db" in url:
                legacy = ROOT / "data" / "luxguard.db"
                new = ROOT / "data" / "wareach.db"
                if not new.exists() and legacy.exists():
                    return f"sqlite:///{legacy}"
            return url
        path = ROOT / "data" / "wareach.db"
        legacy = ROOT / "data" / "luxguard.db"
        if not path.exists() and legacy.exists():
            path = legacy
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
