import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# --- Database Shared State ---
db_session = None
Base = declarative_base()

def create_app():
    """
    Application factory for the LeadScan Flask app.
    Initializes database sessions, blueprints, and global context processors.
    """
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///leadscan.db')

    # --- Database Initialization ---
    global db_session
    engine = create_engine(app.config['DATABASE_URI'])
    db_session = scoped_session(sessionmaker(autocommit=False,
                                           autoflush=False,
                                           bind=engine))

    # Allow Lead.query style access
    Base.query = db_session.query_property()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Releases database connections back to the pool after every request."""
        db_session.remove()

    # --- Routes & Blueprints ---
    from .routes import main
    app.register_blueprint(main.bp)

    # --- UI Helpers & Stats ---
    from .models.config import AppConfig
    @app.context_processor
    def inject_stats():
        """Injects API usage statistics into all HTML templates for the top navbar."""
        try:
            nearby = int(AppConfig.get('google_api_nearby', 0))
            details = int(AppConfig.get('google_api_details', 0))
        except (ValueError, TypeError):
            nearby = 0
            details = 0

        # Google Places API Free Tiers (adjust as needed)
        nearby_limit = 5000
        details_limit = 10000

        nearby_pct = round((nearby / nearby_limit) * 100, 1)
        details_pct = round((details / details_limit) * 100, 1)

        return dict(
            api_nearby=nearby,
            api_details=details,
            api_nearby_pct=nearby_pct,
            api_details_pct=details_pct
        )

    return app

def init_db():
    """Bootstraps the database tables from the SQLAlchemy models."""
    from app.models.lead import Base
    engine = create_engine(os.environ.get('DATABASE_URI', 'sqlite:///leadscan.db'))
    Base.metadata.create_all(engine)
