"""
Pytest configuration and shared fixtures for LeadScan tests.
"""
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import Base


@pytest.fixture(scope='function')
def test_db():
    """Creates an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.query = session.query_property()

    yield session

    session.remove()
    Base.metadata.drop_all(engine)


@pytest.fixture
def app():
    """Create application for testing."""
    os.environ['DATABASE_URI'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key'

    from app import create_app
    app = create_app()
    app.config['TESTING'] = True

    yield app


@pytest.fixture
def client(app):
    """Test client for Flask app."""
    return app.test_client()
