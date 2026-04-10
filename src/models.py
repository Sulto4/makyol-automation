"""Data models for the PDF processing automation pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DocumentType(Enum):
    """Classification of construction material document types."""

    FISA_TEHNICA = "Fișă Tehnică"
    ISO_9001 = "Certificat ISO 9001"
    ISO_14001 = "Certificat ISO 14001"
    ISO_45001 = "Certificat ISO 45001"
    ISO_50001 = "Certificat ISO 50001"
    AVIZ_TEHNIC = "Aviz Tehnic"
    AGREMENT_TEHNIC = "Agrement Tehnic"
    AVIZ_SANITAR = "Aviz Sanitar"
    DECLARATIE_CONFORMITATE = "Declarație de Conformitate"
    CERTIFICAT_CONFORMITATE = "Certificat de Conformitate"
    CERTIFICAT_GARANTIE = "Certificat de Garanție"
    OTHER = "Altul"


@dataclass
class DocumentInfo:
    """Metadata extracted from a single PDF document."""

    file_path: str
    file_name: str
    supplier_folder: str
    document_type: Optional[DocumentType] = None
    material: str = "N/A"
    expiration_date: str = "N/A"
    producer: str = "N/A"
    distributor: str = "N/A"
    extracted_text: str = ""
    confidence: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class SupplierFolder:
    """Represents a supplier's document folder."""

    folder_path: str
    folder_name: str
    producer: str = "N/A"
    distributor: str = "N/A"
    documents: list[DocumentInfo] = field(default_factory=list)


@dataclass
class ProcessingResult:
    """Summary of the entire processing pipeline run."""

    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    supplier_folders: list[SupplierFolder] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Return the percentage of successfully processed files."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100.0
