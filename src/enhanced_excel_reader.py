"""
Enhanced Excel Reader for Multi-file Processing
Processes all .xlsx files and extracts reviews with metadata.
"""
import pandas as pd
import os
import glob
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedExcelReader:
    def __init__(self, data_directory: str = "data"):
        self.data_directory = data_directory
        self.reviews_data = []
    
    def find_excel_files(self) -> List[str]:
        """Find all .xlsx files in the data directory."""
        pattern = os.path.join(self.data_directory, "*.xlsx")
        excel_files = glob.glob(pattern)
        logger.info(f"Found {len(excel_files)} Excel files: {[os.path.basename(f) for f in excel_files]}")
        return excel_files
    
    def extract_sentiment_from_filename(self, filename: str) -> str:
        """Extract sentiment (positive/negative) from filename."""
        filename_lower = filename.lower()
        if "긍정" in filename or "positive" in filename_lower:
            return "positive"
        elif "부정" in filename or "negative" in filename_lower:
            return "negative"
        else:
            return "unknown"
    
    def read_single_excel_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read a single Excel file and extract all reviews."""
        try:
            filename = os.path.basename(file_path)
            sentiment = self.extract_sentiment_from_filename(filename)
            
            # Read without header (reviews are in columns across first row)
            df = pd.read_excel(file_path, header=None)
            logger.info(f"Processing {filename}: Shape {df.shape}")
            
            reviews = []
            
            # Extract reviews from the first row across all columns
            if not df.empty:
                first_row = df.iloc[0]
                for col_idx, review_text in enumerate(first_row):
                    if pd.notna(review_text) and str(review_text).strip():
                        review_data = {
                            'review_id': f"{filename}_{col_idx}",
                            'file_source': filename,
                            'sentiment': sentiment,
                            'original_text': str(review_text).strip(),
                            'column_index': col_idx,
                            'needs_translation': False,  # Will be determined by language detection
                            'translated_text': None,
                            'language': 'unknown'
                        }
                        reviews.append(review_data)
            
            logger.info(f"Extracted {len(reviews)} reviews from {filename}")
            return reviews
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def read_all_excel_files(self) -> List[Dict[str, Any]]:
        """Read all Excel files and compile reviews."""
        excel_files = self.find_excel_files()
        all_reviews = []
        
        for file_path in excel_files:
            reviews = self.read_single_excel_file(file_path)
            all_reviews.extend(reviews)
        
        self.reviews_data = all_reviews
        logger.info(f"Total reviews extracted: {len(all_reviews)}")
        
        # Log sentiment distribution
        sentiment_counts = {}
        for review in all_reviews:
            sentiment = review['sentiment']
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        logger.info(f"Sentiment distribution: {sentiment_counts}")
        return all_reviews
    
    def get_reviews_by_sentiment(self, sentiment: str) -> List[Dict[str, Any]]:
        """Get all reviews with specified sentiment."""
        return [review for review in self.reviews_data if review['sentiment'] == sentiment]
    
    def get_reviews_by_file(self, filename: str) -> List[Dict[str, Any]]:
        """Get all reviews from a specific file."""
        return [review for review in self.reviews_data if review['file_source'] == filename]
    
    def get_total_count(self) -> int:
        """Get total number of reviews."""
        return len(self.reviews_data)
    
    def get_sentiment_counts(self) -> Dict[str, int]:
        """Get count of reviews by sentiment."""
        counts = {}
        for review in self.reviews_data:
            sentiment = review['sentiment']
            counts[sentiment] = counts.get(sentiment, 0) + 1
        return counts
    
    def save_raw_data(self, output_file: str) -> None:
        """Save raw extracted data to JSON for debugging."""
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.reviews_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Raw data saved to {output_file}")

if __name__ == "__main__":
    # Test the reader
    reader = EnhancedExcelReader()
    reviews = reader.read_all_excel_files()
    
    print(f"Total reviews: {len(reviews)}")
    print(f"Sentiment counts: {reader.get_sentiment_counts()}")
    
    # Show sample reviews
    print("\nSample positive review:")
    positive_reviews = reader.get_reviews_by_sentiment('positive')
    if positive_reviews:
        print(positive_reviews[0]['original_text'][:100])
    
    print("\nSample negative review:")
    negative_reviews = reader.get_reviews_by_sentiment('negative')
    if negative_reviews:
        print(negative_reviews[0]['original_text'][:100])