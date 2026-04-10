"""Document model for tracking scanned files."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Document(Base):
    """Document model for tracking scanned files with classification and deduplication.

    Attributes:
        id: Primary key
        supplier_id: Foreign key to supplier who owns this document
        file_path: Full path to the document file
        filename: Original filename
        document_type: Classified document type (e.g., 'ISO 9001', 'AVS')
        classification_confidence: Confidence score for classification (0.0-1.0)
        file_hash: SHA256 hash of file content for deduplication
        needs_review: Whether document needs manual review (unclassified or low confidence)
        created_at: Timestamp when document was imported
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    file_path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    classification_confidence = Column(Float, nullable=True)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    needs_review = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to supplier
    supplier = relationship("Supplier", backref="documents")

    def __repr__(self):
        """String representation of Document."""
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}', needs_review={self.needs_review})>"
