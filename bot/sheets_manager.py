"""
CSV file manager for the knowledge base.
Handles CSV file reading and data processing.
"""

import pandas as pd
import logging
import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CSVManager:
    """Manages CSV file integration for knowledge base."""
    
    def __init__(self, config):
        """Initialize CSV manager."""
        self.config = config
        self.csv_file_path = config.csv_file_path
        self.google_sheets_csv_url = config.google_sheets_csv_url
        self.data_cache = None
        self.cache_time = None
        self.last_modified = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if self.data_cache is None or not self.cache_time:
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
    
    def _is_cache_valid_for_google_sheets(self) -> bool:
        """Check if cached data is still valid for Google Sheets (no file modification check)."""
        if self.data_cache is None or not self.cache_time:
            return False
        
        # Only check cache expiry for Google Sheets
        cache_expiry = self.cache_time + timedelta(minutes=self.config.cache_duration)
        return datetime.now() < cache_expiry
    
    def get_knowledge_base(self) -> pd.DataFrame:
        """Get knowledge base data from CSV file or Google Sheets."""
        try:
            # Try to load from Google Sheets first if URL is provided
            if self.google_sheets_csv_url:
                # Check if cached data is valid for Google Sheets
                if self._is_cache_valid_for_google_sheets():
                    logger.debug("Using cached knowledge base data from Google Sheets")
                    return self.data_cache
                
                logger.info("Loading knowledge base from Google Sheets CSV URL")
                try:
                    df = self._load_from_google_sheets()
                    # Cache the data
                    self.data_cache = df
                    self.cache_time = datetime.now()
                    logger.info(f"Successfully loaded {len(df)} records from Google Sheets")
                    return df
                except Exception as e:
                    logger.warning(f"Failed to load from Google Sheets: {str(e)}")
                    logger.info("Falling back to local CSV file")
            
            # Return cached data if valid for local file
            if self._is_cache_valid():
                logger.debug("Using cached knowledge base data")
                return self.data_cache
            
            # Fall back to local CSV file
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

    def log_unanswered_question(self, user_question: str, user_id=None, username=None):
        """Записывает вопросы без ответа в CSV."""
        words = user_question.split()
        if len(words) < 3:
            return  # Не записываем короткие вопросы

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open("unanswered_questions.csv", "a", encoding="utf-8") as f:
                f.write(f'"{timestamp}","{user_id}","{username or "Unknown"}","{user_question}"\n')
            logger.info(f"Вопрос записан: '{user_question}'")
        except Exception as e:
            logger.error(f"Не удалось записать вопрос в CSV: {str(e)}")
    
    def _load_from_google_sheets(self) -> pd.DataFrame:
        """Load knowledge base data from Google Sheets CSV URL."""
        # Set proper encoding for the request
        response = requests.get(self.google_sheets_csv_url, timeout=30)
        response.raise_for_status()
        
        # Try to detect and fix encoding issues
        content = response.content
        
        # Try different encodings
        text_content = None
        for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'latin1']:
            try:
                text_content = content.decode(encoding)
                logger.info(f"Successfully decoded with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if text_content is None:
            text_content = content.decode('utf-8', errors='replace')
            logger.warning("Used utf-8 with error replacement")
        
        # Debug: Log the raw response
        logger.info(f"Raw response content (first 500 chars): {text_content[:500]}")
        
        # Parse CSV from response content with error handling
        from io import StringIO
        try:
            # Try with different parameters to handle CSV formatting issues
            df = pd.read_csv(StringIO(text_content), 
                           on_bad_lines='skip',  # Skip problematic lines
                           quoting=1)  # Handle quoted fields
        except Exception as e:
            logger.warning(f"Failed to parse CSV with standard settings: {e}")
            # Try with more relaxed settings
            df = pd.read_csv(StringIO(text_content), 
                           on_bad_lines='skip',
                           sep=',',
                           quotechar='"',
                           skipinitialspace=True)
        
        # Debug: Log dataframe info
        logger.info(f"Loaded DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {list(df.columns)}")
        if not df.empty:
            logger.info(f"First few rows:\n{df.head()}")
        
        if df.empty:
            logger.warning("Google Sheets CSV is empty")
            return pd.DataFrame()
        
        # Expected columns: Category, Question, Answer, Priority, Last Updated
        required_columns = ['Category', 'Question', 'Answer']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns in Google Sheets: {missing_columns}")
            logger.error(f"Available columns: {list(df.columns)}")
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean and validate data
        df = self._clean_data(df)
        
        return df
    
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
