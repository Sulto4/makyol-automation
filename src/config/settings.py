"""Application settings and configuration."""

import os
from pathlib import Path


class Settings:
    """Application settings."""

    def __init__(self):
        # Database configuration
        self.db_path = Path("scanner.db")
        self.database_url = f"sqlite:///{self.db_path}"

        # Base document folder path
        self.base_document_path = Path("Documente")

        # Supplier folder mappings
        self.supplier_folders = {
            "Zakprest": "Documente Zakprest",
            "TERAPLAST": "PEHD Apa - TERAPLAST",
            "VALROM": "PEHD Apa - VALROM",
            "Tehnoworld": "Teava apa PEHD - Tehnoworld"
        }

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")


# Global settings instance
settings = Settings()
