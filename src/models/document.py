"""Document database model."""
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base


class Document(Base):
    """Document model representing a compliance document."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # e.g., "ISO 9001", "Tax Certificate", etc.
    status = Column(String, nullable=False, default="valid")  # valid, expired, missing, pending
    validity_date = Column(Date, nullable=True)  # Expiration/validity date
    certificate_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to supplier
    supplier = relationship("Supplier", back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, type='{self.type}', status='{self.status}', supplier_id={self.supplier_id})>"
