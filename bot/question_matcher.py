"""
Question matching logic using fuzzy string matching.
Finds the most relevant answers based on user questions.
"""

import pandas as pd
import logging
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz, process
import re

logger = logging.getLogger(__name__)

class QuestionMatcher:
    """Handles fuzzy matching of user questions to knowledge base."""
    
    def __init__(self, config):
        """Initialize question matcher."""
        self.config = config
        self.similarity_threshold = config.similarity_threshold
        self.max_results = config.max_results
    
    def find_matches(self, user_question: str, knowledge_base: pd.DataFrame) -> List[Dict]:
        """Find matching questions in the knowledge base."""
        try:
            if knowledge_base.empty:
                logger.warning("Knowledge base is empty")
                return []
            
            # Clean user question
            cleaned_question = self._clean_question(user_question)
            
            if not cleaned_question:
                logger.warning("User question is empty after cleaning")
                return []
            
            # Get all questions from knowledge base
            questions = knowledge_base['Question'].tolist()
            
            # Find matches using fuzzy string matching
            matches = process.extract(
                cleaned_question,
                questions,
                scorer=fuzz.token_sort_ratio,
                limit=self.max_results * 2  # Get more candidates for filtering
            )
            
            # Filter matches above threshold and format results
            results = []
            for match_text, score in matches:
                if score >= self.similarity_threshold:
                    # Find the corresponding row in the dataframe
                    row = knowledge_base[knowledge_base['Question'] == match_text].iloc[0]
                    
                    result = {
                        'question': row['Question'],
                        'answer': row['Answer'],
                        'category': row.get('Category', 'General'),
                        'priority': row.get('Priority', 5),
                        'score': score,
                        'last_updated': row.get('Last Updated', None)
                    }
                    results.append(result)
            
            # Sort by score (descending) and priority (ascending - lower is higher priority)
            results.sort(key=lambda x: (-x['score'], x['priority']))
            
            # Limit to max results
            results = results[:self.max_results]
            
            logger.info(f"Found {len(results)} matches for question: '{user_question}'")
            return results
            
        except Exception as e:
            logger.error(f"Error finding matches: {str(e)}")
            return []
    
    def _clean_question(self, question: str) -> str:
        """Clean and normalize the user question."""
        if not question:
            return ""
        
        # Convert to lowercase
        cleaned = question.lower().strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters that might interfere with matching
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        
        # Remove extra spaces again
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def get_best_match(self, user_question: str, knowledge_base: pd.DataFrame) -> Optional[Dict]:
        """Get the single best match for a user question."""
        matches = self.find_matches(user_question, knowledge_base)
        
        if matches:
            return matches[0]
        
        return None
    
    def search_by_category(self, user_question: str, knowledge_base: pd.DataFrame, category: str) -> List[Dict]:
        """Search for matches within a specific category."""
        try:
            if knowledge_base.empty:
                return []
            
            # Filter by category
            category_df = knowledge_base[
                knowledge_base['Category'].str.lower() == category.lower()
            ]
            
            if category_df.empty:
                logger.warning(f"No questions found in category: {category}")
                return []
            
            # Find matches in the filtered data
            return self.find_matches(user_question, category_df)
            
        except Exception as e:
            logger.error(f"Error searching by category: {str(e)}")
            return []
    
    def get_categories(self, knowledge_base: pd.DataFrame) -> List[str]:
        """Get all available categories from the knowledge base."""
        try:
            if knowledge_base.empty or 'Category' not in knowledge_base.columns:
                return []
            
            categories = knowledge_base['Category'].dropna().unique().tolist()
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []
    
    def get_similarity_score(self, question1: str, question2: str) -> int:
        """Get similarity score between two questions."""
        try:
            cleaned_q1 = self._clean_question(question1)
            cleaned_q2 = self._clean_question(question2)
            
            if not cleaned_q1 or not cleaned_q2:
                return 0
            
            return fuzz.token_sort_ratio(cleaned_q1, cleaned_q2)
            
        except Exception as e:
            logger.error(f"Error calculating similarity score: {str(e)}")
            return 0
