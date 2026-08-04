from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "wareach",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "offline-harvest-loop": {
            "task": "app.workers.tasks.task_offline_harvest",
            "schedule": 90.0,
            "kwargs": {"limit": 5000},
        },
        "yupoo-expand-loop": {
            "task": "app.workers.tasks.task_yupoo_expand",
            "schedule": 200.0,
            "kwargs": {"seed_limit": 30},
        },
        "yupoo-raw-loop": {
            "task": "app.workers.tasks.task_yupoo_raw_crawl",
            "schedule": 100.0,
            "kwargs": {"limit": 45},
        },
        "drain-wa-loop": {
            "task": "app.workers.tasks.task_drain_wa",
            "schedule": 150.0,
            "kwargs": {"limit": 40},
        },
        "blitz-loop": {
            "task": "app.workers.tasks.task_whatsapp_blitz",
            "schedule": 160.0,
            "kwargs": {"query_limit": 18},
        },
        "discovery-loop": {
            "task": "app.workers.tasks.task_discovery_batch",
            "schedule": float(settings.discovery_interval_sec),
        },
        "crawl-loop": {
            "task": "app.workers.tasks.task_crawl_batch",
            "schedule": max(float(settings.crawl_interval_sec), 240.0),
            "kwargs": {"limit": 20},
        },
        "alerts-loop": {
            "task": "app.workers.tasks.task_evaluate_alerts",
            "schedule": 120.0,
        },
        "doctor-refresh": {
            "task": "app.workers.tasks.task_refresh_doctor",
            "schedule": 600.0,
        },
        "wa-verify-loop": {
            "task": "app.workers.tasks.task_whatsapp_verify",
            "schedule": 420.0,
            "kwargs": {"limit": 20},
        },
    },
)
