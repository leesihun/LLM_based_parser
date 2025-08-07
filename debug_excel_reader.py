#!/usr/bin/env python3
"""
Debug script to test ExcelReader functionality.
"""

import logging
from src.excel_reader import ExcelReader
from config.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    print("Debugging Excel Reader")
    print("=" * 40)
    
    config = Config()
    
    print(f"Data directory: {config.data_dir}")
    print(f"Positive file: {config.positive_file}")
    print(f"Negative file: {config.negative_file}")
    print(f"Positive exists: {config.positive_file.exists()}")
    print(f"Negative exists: {config.negative_file.exists()}")
    
    if not config.positive_file.exists():
        print(f"Missing: {config.positive_file}")
        return
        
    if not config.negative_file.exists():
        print(f"Missing: {config.negative_file}")
        return
    
    print("\nTesting ExcelReader...")
    
    try:
        reader = ExcelReader()
        
        # Test loading positive reviews
        print(f"\nLoading positive reviews from {config.positive_filename}...")
        pos_df = reader.load_positive_reviews()
        if pos_df is not None:
            print(f"Loaded {len(pos_df)} positive reviews")
            print(f"Columns: {list(pos_df.columns)}")
            if not pos_df.empty:
                print(f"First few rows:")
                print(pos_df.head(2))
        else:
            print("Failed to load positive reviews")
        
        # Test loading negative reviews  
        print(f"\nLoading negative reviews from {config.negative_filename}...")
        neg_df = reader.load_negative_reviews()
        if neg_df is not None:
            print(f"Loaded {len(neg_df)} negative reviews")
            print(f"Columns: {list(neg_df.columns)}")
            if not neg_df.empty:
                print(f"First few rows:")
                print(neg_df.head(2))
        else:
            print("Failed to load negative reviews")
        
        # Test combined reviews
        print(f"\nTesting combined reviews...")
        combined_df = reader.combine_reviews()
        if combined_df is not None:
            print(f"Combined dataframe: {len(combined_df)} rows")
            print(f"Columns: {list(combined_df.columns)}")
            print(f"Sentiment counts:")
            print(combined_df['sentiment'].value_counts())
        else:
            print("Failed to create combined dataframe")
        
        # Test detailed documents
        print(f"\nTesting detailed documents...")
        detailed_docs = reader.get_detailed_documents()
        print(f"Created {len(detailed_docs)} detailed documents")
        if detailed_docs:
            print(f"First document preview: {detailed_docs[0][:200]}...")
            
            # Check sentiment distribution
            positive_count = sum(1 for doc in detailed_docs if doc.startswith("[POSITIVE]"))
            negative_count = sum(1 for doc in detailed_docs if doc.startswith("[NEGATIVE]"))
            print(f"Document sentiment distribution:")
            print(f"   Positive: {positive_count}")
            print(f"   Negative: {negative_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Exception details:")

if __name__ == "__main__":
    main()