import logging

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.entities import SystemMetric
from app.services.agent_reach import run_doctor
from app.services.pipeline import run_crawl_batch, run_discovery_batch, utcnow

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.task_discovery_batch", bind=True, max_retries=2)
def task_discovery_batch(self, limit: int = 15):
    db = SessionLocal()
    try:
        return run_discovery_batch(db, limit=limit)
    except Exception as exc:
        logger.exception("discovery task failed")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_crawl_batch", bind=True, max_retries=2)
def task_crawl_batch(self, limit: int = 40):
    db = SessionLocal()
    try:
        return run_crawl_batch(db, limit=limit)
    except Exception as exc:
        logger.exception("crawl task failed")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_drain_wa", bind=True, max_retries=1)
def task_drain_wa(self, limit: int = 60):
    from app.services.drain import drain_wa_pending

    db = SessionLocal()
    try:
        return drain_wa_pending(db, limit=limit, fetch_pages=False)
    except Exception as exc:
        logger.exception("drain task failed")
        raise self.retry(exc=exc, countdown=45)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_whatsapp_blitz", bind=True, max_retries=1)
def task_whatsapp_blitz(self, query_limit: int = 18):
    from app.services.whatsapp_harvest import run_whatsapp_blitz

    db = SessionLocal()
    try:
        return run_whatsapp_blitz(db, query_limit=query_limit, workers=3)
    except Exception as exc:
        logger.exception("blitz task failed")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_evaluate_alerts")
def task_evaluate_alerts():
    from app.services.alerts import evaluate_alerts

    db = SessionLocal()
    try:
        return evaluate_alerts(db)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_offline_harvest")
def task_offline_harvest(limit: int = 5000):
    from app.services.offline_harvest import offline_harvest_all

    db = SessionLocal()
    try:
        return offline_harvest_all(db, limit=limit)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_yupoo_expand")
def task_yupoo_expand(seed_limit: int = 35):
    from app.services.yupoo_expand import run_yupoo_expand

    db = SessionLocal()
    try:
        return run_yupoo_expand(db, seed_limit=seed_limit)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_yupoo_raw_crawl")
def task_yupoo_raw_crawl(limit: int = 50):
    from app.services.yupoo_raw import run_yupoo_raw_crawl

    db = SessionLocal()
    try:
        return run_yupoo_raw_crawl(db, limit=limit, workers=6)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_whatsapp_verify")
def task_whatsapp_verify(limit: int = 25):
    from app.services.wa_verify import auth_ready, run_whatsapp_verify

    if not auth_ready():
        return {"ok": False, "skipped": "no_session"}
    db = SessionLocal()
    try:
        return run_whatsapp_verify(db, limit=limit, delay_ms=3500)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_refresh_doctor")
def task_refresh_doctor():
    db = SessionLocal()
    try:
        data = run_doctor()
        from sqlalchemy import select

        row = db.scalar(select(SystemMetric).where(SystemMetric.key == "agent_reach_doctor"))
        if not row:
            row = SystemMetric(key="agent_reach_doctor", value=data)
            db.add(row)
        else:
            row.value = data
            row.updated_at = utcnow()
        db.commit()
        return {"ok": True, "channels": len([k for k in data if not k.startswith("_")])}
    finally:
        db.close()
