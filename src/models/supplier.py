"""Supplier model for document management."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from .database import Base


class Supplier(Base):
    """Supplier model for tracking document suppliers and their folder paths.

    Attributes:
        id: Primary key
        name: Supplier name (e.g., Zakprest, TERAPLAST)
        folder_path: Relative folder path for this supplier's documents
        created_at: Timestamp when supplier was created
    """

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    folder_path = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        """String representation of Supplier."""
        return f"<Supplier(id={self.id}, name='{self.name}', folder_path='{self.folder_path}')>"
