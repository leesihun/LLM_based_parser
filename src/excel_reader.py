"""Excel file reader module for processing cellphone review data."""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelReader:
    """Handles reading and processing of Excel files containing cellphone review data."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.positive_file = self.data_dir / "fold_positive.xlsx"
        self.negative_file = self.data_dir / "fold_negative.xlsx"
    
    def read_excel_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read an Excel file and return as DataFrame."""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
            
            df = pd.read_excel(file_path)
            logger.info(f"Successfully read {len(df)} rows from {file_path.name}")
            return df
        
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            return None
    
    def load_positive_reviews(self) -> Optional[pd.DataFrame]:
        """Load positive cellphone reviews from fold_positive.xlsx."""
        return self.read_excel_file(self.positive_file)
    
    def load_negative_reviews(self) -> Optional[pd.DataFrame]:
        """Load negative cellphone reviews from fold_negative.xlsx."""
        return self.read_excel_file(self.negative_file)
    
    def load_all_reviews(self) -> Dict[str, pd.DataFrame]:
        """Load both positive and negative reviews."""
        reviews = {}
        
        positive_df = self.load_positive_reviews()
        if positive_df is not None:
            positive_df['sentiment'] = 'positive'
            reviews['positive'] = positive_df
        
        negative_df = self.load_negative_reviews()
        if negative_df is not None:
            negative_df['sentiment'] = 'negative'
            reviews['negative'] = negative_df
        
        return reviews
    
    def combine_reviews(self) -> Optional[pd.DataFrame]:
        """Combine positive and negative reviews into a single DataFrame."""
        reviews = self.load_all_reviews()
        
        if not reviews:
            logger.warning("No review data loaded")
            return None
        
        combined_df = pd.concat(reviews.values(), ignore_index=True)
        logger.info(f"Combined {len(combined_df)} total reviews")
        
        return combined_df
    
    def get_review_texts(self) -> List[str]:
        """Extract review texts as a list of strings for RAG processing."""
        combined_df = self.combine_reviews()
        
        if combined_df is None:
            return []
        
        # Try common column names for review text
        text_columns = ['review', 'text', 'comment', 'content', 'description']
        text_column = None
        
        for col in text_columns:
            if col in combined_df.columns:
                text_column = col
                break
        
        if text_column is None:
            # If no standard column found, use the first string column
            string_columns = combined_df.select_dtypes(include=['object']).columns
            if len(string_columns) > 0:
                text_column = string_columns[0]
                logger.info(f"Using column '{text_column}' as review text")
            else:
                logger.error("No suitable text column found in the data")
                return []
        
        # Combine text with sentiment information
        texts = []
        for _, row in combined_df.iterrows():
            sentiment = row.get('sentiment', 'unknown')
            review_text = str(row[text_column])
            combined_text = f"[{sentiment.upper()}] {review_text}"
            texts.append(combined_text)
        
        return texts