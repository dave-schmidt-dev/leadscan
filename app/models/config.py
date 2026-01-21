import logging
from datetime import datetime

from sqlalchemy import Column, String, text

from app import Base

logger = logging.getLogger(__name__)


class AppConfig(Base):
    """
    Persistent key-value store for application settings and API quota tracking.
    """
    __tablename__ = 'app_config'
    key = Column(String(50), primary_key=True)
    value = Column(String(255))

    @staticmethod
    def get(key, default=None):
        """Retrieve a configuration value by key."""
        from app import db_session
        try:
            item = db_session.get(AppConfig, key)
            return item.value if item else default
        except Exception as e:
            logger.warning(f"Failed to get config key '{key}': {e}")
            return default

    @staticmethod
    def set(key, value):
        """Store or update a configuration value."""
        from app import db_session
        try:
            item = db_session.get(AppConfig, key)
            if not item:
                item = AppConfig(key=key)
                db_session.add(item)
            item.value = str(value)
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to set config key '{key}': {e}")
            db_session.rollback()

    @staticmethod
    def check_monthly_reset():
        """
        Automatically resets API usage counters if we have entered a new billing month.
        """
        current_month = datetime.now().strftime('%Y-%m')
        stored_month = AppConfig.get('last_billing_month')

        if stored_month != current_month:
            # New month detected: Reset counters to 0
            AppConfig.set('last_billing_month', current_month)
            AppConfig.set('google_api_nearby', "0")
            AppConfig.set('google_api_details', "0")
            AppConfig.set('google_api_calls', "0")
            logger.info(f"New billing month detected ({current_month}). Resetting API counters.")

    @staticmethod
    def increment(key, amount=1):
        """
        Atomically increment a numeric configuration value (e.g., API hits).
        Uses SQL UPDATE for thread-safe atomic increment.
        """
        from app import db_session

        # Ensure counters are fresh for the current month
        AppConfig.check_monthly_reset()

        try:
            # Ensure the key exists first
            item = db_session.get(AppConfig, key)
            if not item:
                item = AppConfig(key=key, value="0")
                db_session.add(item)
                db_session.commit()

            # Atomic increment using SQL UPDATE
            db_session.execute(
                text("UPDATE app_config SET value = CAST(COALESCE(value, '0') AS INTEGER) + :amt WHERE key = :key"),
                {"amt": amount, "key": key}
            )
            db_session.commit()

            # Return the new value
            item = db_session.get(AppConfig, key)
            return int(item.value) if item else amount

        except Exception as e:
            logger.error(f"Failed to increment config key '{key}': {e}")
            db_session.rollback()
            return 0
