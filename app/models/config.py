from sqlalchemy import Column, Integer, String
from app import Base
from datetime import datetime

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
        item = db_session.get(AppConfig, key)
        return item.value if item else default

    @staticmethod
    def set(key, value):
        """Store or update a configuration value."""
        from app import db_session
        item = db_session.get(AppConfig, key)
        if not item:
            item = AppConfig(key=key)
            db_session.add(item)
        item.value = str(value)
        db_session.commit()

    @staticmethod
    def check_monthly_reset():
        """
        Automatically resets API usage counters if we have entered a new billing month.
        """
        from app import db_session
        current_month = datetime.now().strftime('%Y-%m')
        stored_month = AppConfig.get('last_billing_month')
        
        if stored_month != current_month:
            # New month detected: Reset counters to 0
            AppConfig.set('last_billing_month', current_month)
            AppConfig.set('google_api_nearby', "0")
            AppConfig.set('google_api_details', "0")
            AppConfig.set('google_api_calls', "0")
            print(f"🔄 New billing month detected ({current_month}). Resetting API counters.")

    @staticmethod
    def increment(key, amount=1):
        """Atomically increment a numeric configuration value (e.g., API hits)."""
        from app import db_session
        
        # Ensure counters are fresh for the current month
        AppConfig.check_monthly_reset()
        
        item = db_session.get(AppConfig, key)
        if not item:
            item = AppConfig(key=key, value="0")
            db_session.add(item)
        
        try:
            current = int(item.value)
        except (ValueError, TypeError):
            current = 0
            
        item.value = str(current + amount)
        db_session.commit()
        return current + amount
