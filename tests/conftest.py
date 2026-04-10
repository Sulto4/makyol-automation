"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.models.database import Base, SessionLocal
from src.models.supplier import Supplier
from src.config.settings import Settings


@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary test database for each test.

    Yields:
        str: Database URL for temporary database
    """
    # Create a temporary file for the database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"

    # Create engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    yield db_url

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def db_session(temp_db):
    """Create a database session for testing.

    Args:
        temp_db: Temporary database URL from temp_db fixture

    Yields:
        Session: SQLAlchemy session for testing
    """
    engine = create_engine(temp_db)
    Base.metadata.create_all(engine)

    # Create session
    from sqlalchemy.orm import sessionmaker
    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    yield session

    # Cleanup - close session and dispose engine properly
    session.close()
    # Remove all connections before disposing
    engine.dispose()
    # Give Windows time to release the file handle
    import time
    time.sleep(0.1)


@pytest.fixture(scope="function")
def test_supplier(db_session):
    """Create a test supplier in the database.

    Args:
        db_session: Database session from db_session fixture

    Returns:
        Supplier: Test supplier object
    """
    supplier = Supplier(
        name="TestSupplier",
        folder_path="tests/fixtures/sample_docs/Documente Zakprest"
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)

    return supplier


@pytest.fixture(scope="function")
def test_fixtures_path():
    """Get path to test fixtures directory.

    Returns:
        Path: Path to test fixtures directory
    """
    return Path(__file__).parent / "fixtures" / "sample_docs"


@pytest.fixture(scope="function")
def test_settings(test_fixtures_path):
    """Create test settings with fixtures path.

    Args:
        test_fixtures_path: Path to test fixtures

    Returns:
        Settings: Settings object configured for testing
    """
    settings = Settings()
    settings.base_document_path = test_fixtures_path
    settings.db_path = Path("test_scanner.db")
    settings.database_url = f"sqlite:///{settings.db_path}"

    return settings
