"""
CSV file manager for the knowledge base.
Handles CSV file reading and data processing.
"""

import pandas as pd
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CSVManager:
    """Manages CSV file integration for knowledge base."""
    
    def __init__(self, config):
        """Initialize CSV manager."""
        self.config = config
        self.csv_file_path = config.csv_file_path
        self.data_cache = None
        self.cache_time = None
        self.last_modified = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.data_cache or not self.cache_time:
            return False
        
        # Check if file has been modified
        if not os.path.exists(self.csv_file_path):
            return False
        
        file_modified = datetime.fromtimestamp(os.path.getmtime(self.csv_file_path))
        
        # If file was modified after cache, invalidate cache
        if self.last_modified and file_modified > self.last_modified:
            return False
        
        # Check cache expiry
        cache_expiry = self.cache_time + timedelta(minutes=self.config.cache_duration)
        return datetime.now() < cache_expiry
    
    def get_knowledge_base(self) -> pd.DataFrame:
        """Get knowledge base data from CSV file."""
        try:
            # Return cached data if valid
            if self._is_cache_valid():
                logger.debug("Using cached knowledge base data")
                return self.data_cache
            
            logger.info(f"Loading knowledge base from {self.csv_file_path}")
            
            # Check if file exists
            if not os.path.exists(self.csv_file_path):
                logger.error(f"CSV file not found: {self.csv_file_path}")
                return pd.DataFrame()
            
            # Read CSV file
            df = pd.read_csv(self.csv_file_path)
            
            if df.empty:
                logger.warning("CSV file is empty")
                return pd.DataFrame()
            
            # Expected columns: Category, Question, Answer, Priority, Last Updated
            required_columns = ['Category', 'Question', 'Answer']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns in CSV: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clean and validate data
            df = self._clean_data(df)
            
            # Cache the data
            self.data_cache = df
            self.cache_time = datetime.now()
            self.last_modified = datetime.fromtimestamp(os.path.getmtime(self.csv_file_path))
            
            logger.info(f"Successfully loaded {len(df)} records from knowledge base")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get knowledge base: {str(e)}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the knowledge base data."""
        # Remove empty rows
        df = df.dropna(subset=['Question', 'Answer'])
        
        # Remove rows with empty questions or answers
        df = df[df['Question'].str.strip() != '']
        df = df[df['Answer'].str.strip() != '']
        
        # Convert Priority to numeric if it exists
        if 'Priority' in df.columns:
            df['Priority'] = pd.to_numeric(df['Priority'], errors='coerce')
            df['Priority'] = df['Priority'].fillna(5)  # Default priority
        else:
            df['Priority'] = 5  # Default priority for all
        
        # Convert Last Updated to datetime if it exists
        if 'Last Updated' in df.columns:
            df['Last Updated'] = pd.to_datetime(df['Last Updated'], errors='coerce')
        
        # Strip whitespace from text columns
        text_columns = ['Category', 'Question', 'Answer']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def refresh_cache(self) -> None:
        """Force refresh of cached data."""
        logger.info("Forcing cache refresh")
        self.data_cache = None
        self.cache_time = None
        self.last_modified = None
        self.get_knowledge_base()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        try:
            df = self.get_knowledge_base()
            
            if df.empty:
                return {"total_questions": 0, "categories": 0}
            
            stats = {
                "total_questions": len(df),
                "categories": df['Category'].nunique() if 'Category' in df.columns else 0,
                "last_updated": self.cache_time.isoformat() if self.cache_time else None,
                "file_path": self.csv_file_path
            }
            
            # Add category breakdown
            if 'Category' in df.columns:
                category_counts = df['Category'].value_counts().to_dict()
                stats["category_breakdown"] = category_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {str(e)}")
            return {"error": str(e)}
