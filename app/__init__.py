from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

db_session = None
Base = declarative_base()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///leadscan.db')

    # Database setup
    global db_session
    engine = create_engine(app.config['DATABASE_URI'])
    db_session = scoped_session(sessionmaker(autocommit=False,
                                           autoflush=False,
                                           bind=engine))
    
    Base.query = db_session.query_property()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Register blueprints (will add later)
    from .routes import main
    app.register_blueprint(main.bp)

    # Context processors
    from .models.config import AppConfig
    @app.context_processor
    def inject_stats():
        try:
            nearby = int(AppConfig.get('google_api_nearby', 0))
            details = int(AppConfig.get('google_api_details', 0))
        except:
            nearby = 0
            details = 0
            
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
    from app.models.lead import Base
    engine = create_engine(os.environ.get('DATABASE_URI', 'sqlite:///leadscan.db'))
    Base.metadata.create_all(engine)
