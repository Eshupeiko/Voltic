"""
Configuration management for the Telegram bot.
Handles environment variables and settings.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for bot settings."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.telegram_token = self._get_required_env('TELEGRAM_BOT_TOKEN')
        
        # CSV file settings
        self.csv_file_path = os.getenv('CSV_FILE_PATH', 'knowledge_base.csv')
        
        # Optional settings with defaults
        self.max_results = int(os.getenv('MAX_SEARCH_RESULTS', '5'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '60.0'))
        self.cache_duration = int(os.getenv('CACHE_DURATION_MINUTES', '30'))
        
        # Validate configuration
        self._validate_config()
        
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise exception."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if self.similarity_threshold < 0 or self.similarity_threshold > 100:
            raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 100")
            
        if self.max_results < 1:
            raise ValueError("MAX_SEARCH_RESULTS must be at least 1")
            
        logger.info("Configuration validation passed")
