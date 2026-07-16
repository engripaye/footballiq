import logging
import threading
import time

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.league import League
from app.providers.football_data_provider import FootballDataOrgProvider
from app.services.fixture_sync_service import FixtureSyncService


logger = logging.getLogger(__name__)
FREE_TIER_COMPETITIONS = ("CL", "PPL", "PL", "DED", "BL1", "FL1", "SA", "PD", "ELC", "BSA", "WC", "EC")
_bootstrap_lock = threading.Lock()


def sync_provider_data_if_empty() -> None:
    """Populate a new production database without delaying API startup.

    Only one worker may bootstrap at a time, and an existing league prevents
    another provider sweep. Calls are paced for the football-data.org free tier.
    """
    if not _bootstrap_lock.acquire(blocking=False):
        return
    db = SessionLocal()
    provider = None
    try:
        if db.query(League).count() > 0:
            logger.info("Provider bootstrap skipped because league data already exists")
            return
        provider = FootballDataOrgProvider()
        service = FixtureSyncService(db, provider)
        successful = 0
        for index, code in enumerate(FREE_TIER_COMPETITIONS):
            if index:
                time.sleep(settings.SYNC_REQUEST_DELAY_SECONDS)
            try:
                service.sync_competition(code)
                successful += 1
            except Exception:
                db.rollback()
                logger.exception("Unable to bootstrap competition %s", code)
        logger.info("Provider bootstrap completed: %s/%s competitions", successful, len(FREE_TIER_COMPETITIONS))
    except Exception:
        logger.exception("Provider bootstrap failed")
    finally:
        if provider is not None:
            provider.close()
        db.close()
        _bootstrap_lock.release()
