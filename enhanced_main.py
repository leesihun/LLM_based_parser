"""
Enhanced LLM-based Parser Main Pipeline
Orchestrates the complete process: Excel reading -> Translation -> Markdown generation -> Query system
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_excel_reader import EnhancedExcelReader
from src.enhanced_ollama_client import EnhancedOllamaClient
from src.markdown_generator import MarkdownGenerator
from src.enhanced_query_engine import EnhancedQueryEngine
from config.enhanced_config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedPipeline:
    def __init__(self):
        self.excel_reader = EnhancedExcelReader(config.data_directory)
        self.ollama_client = EnhancedOllamaClient()
        self.markdown_generator = MarkdownGenerator(config.output_directory)
        self.query_engine = None
        self.processed_reviews = []
        self.markdown_file_path = None
        
        logger.info("Enhanced LLM Pipeline initialized")
        logger.info(f"Configuration: {config}")
    
    def step1_read_excel_files(self) -> List[Dict[str, Any]]:
        """Step 1: Read all Excel files and extract reviews."""
        logger.info("=== STEP 1: Reading Excel Files ===")
        
        raw_reviews = self.excel_reader.read_all_excel_files()
        
        if not raw_reviews:
            logger.error("No reviews found in Excel files!")
            return []
        
        logger.info(f"Successfully extracted {len(raw_reviews)} raw reviews")
        return raw_reviews
    
    def step2_process_language_and_translation(self, raw_reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 2: Detect language, translate, and correct spelling."""
        logger.info("=== STEP 2: Language Processing and Translation ===")
        
        processed_reviews = []
        
        for i, review in enumerate(raw_reviews):
            logger.info(f"Processing review {i+1}/{len(raw_reviews)} from {review['file_source']}")
            
            # Process text with language detection and translation
            processing_result = self.ollama_client.process_review_text(review['original_text'])
            
            # Merge results
            enhanced_review = {
                **review,  # Original data
                **processing_result  # Language processing results
            }
            
            processed_reviews.append(enhanced_review)
            
            # Log progress every 10 reviews
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1}/{len(raw_reviews)} reviews")
        
        self.processed_reviews = processed_reviews
        logger.info(f"Language processing complete: {len(processed_reviews)} reviews processed")
        return processed_reviews
    
    def step3_generate_markdown(self, processed_reviews: List[Dict[str, Any]]) -> str:
        """Step 3: Generate consolidated markdown file."""
        logger.info("=== STEP 3: Generating Consolidated Markdown ===")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"consolidated_reviews_{timestamp}.md"
        
        self.markdown_file_path = self.markdown_generator.generate_consolidated_markdown(
            processed_reviews, filename
        )
        
        logger.info(f"Markdown file generated: {self.markdown_file_path}")
        return self.markdown_file_path
    
    def step4_initialize_query_system(self, markdown_path: str) -> EnhancedQueryEngine:
        """Step 4: Initialize the query system."""
        logger.info("=== STEP 4: Initializing Query System ===")
        
        self.query_engine = EnhancedQueryEngine(markdown_path, self.ollama_client)
        
        logger.info("Query system ready for questions")
        return self.query_engine
    
    def run_complete_pipeline(self) -> Dict[str, Any]:
        """Run the complete pipeline from Excel files to query system."""
        start_time = datetime.now()
        logger.info("🚀 Starting Enhanced LLM Pipeline")
        
        try:
            # Step 1: Read Excel files
            raw_reviews = self.step1_read_excel_files()
            if not raw_reviews:
                return {"success": False, "error": "No reviews found"}
            
            # Step 2: Language processing and translation
            processed_reviews = self.step2_process_language_and_translation(raw_reviews)
            
            # Step 3: Generate markdown
            markdown_path = self.step3_generate_markdown(processed_reviews)
            
            # Step 4: Initialize query system
            query_engine = self.step4_initialize_query_system(markdown_path)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result = {
                "success": True,
                "processing_time_seconds": processing_time,
                "total_reviews": len(processed_reviews),
                "markdown_file": markdown_path,
                "sentiment_distribution": self.excel_reader.get_sentiment_counts(),
                "ready_for_queries": True
            }
            
            logger.info("✅ Pipeline completed successfully!")
            logger.info(f"Processing time: {processing_time:.2f} seconds")
            logger.info(f"Generated file: {markdown_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return {"success": False, "error": str(e)}
    
    def save_processing_log(self, result: Dict[str, Any]) -> str:
        """Save processing log for reference."""
        log_filename = os.path.join(config.output_directory, "processing_log.json")
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "config": str(config),
            "result": result,
            "processed_reviews_count": len(self.processed_reviews)
        }
        
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processing log saved: {log_filename}")
        return log_filename
    
    def test_sample_questions(self) -> List[Dict[str, Any]]:
        """Test the system with the sample questions from requirements."""
        if not self.query_engine:
            logger.error("Query engine not initialized. Run pipeline first.")
            return []
        
        sample_questions = [
            "How many responses are good and how many are bad?",
            "What keyword is used most often? and how many times has it been mentioned? Semantically analyze it.",
            "Give me an example of good review regarding screen size.",
            "Give me an example of bad review regarding screen time."
        ]
        
        results = []
        logger.info("🔍 Testing sample questions...")
        
        for question in sample_questions:
            logger.info(f"Testing: {question}")
            try:
                answer = self.query_engine.query(question)
                results.append({
                    "question": question,
                    "answer": answer.get('answer', 'No answer generated'),
                    "type": answer.get('type', 'unknown'),
                    "success": True
                })
                logger.info(f"✅ Question answered successfully")
            except Exception as e:
                logger.error(f"❌ Error answering question: {e}")
                results.append({
                    "question": question,
                    "error": str(e),
                    "success": False
                })
        
        return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enhanced LLM-based Review Parser")
    parser.add_argument("--mode", choices=["pipeline", "query", "test"], 
                       default="pipeline", help="Run mode")
    parser.add_argument("--question", type=str, help="Question to ask (for query mode)")
    parser.add_argument("--markdown", type=str, help="Path to markdown file (for query mode)")
    
    args = parser.parse_args()
    
    pipeline = EnhancedPipeline()
    
    if args.mode == "pipeline":
        # Run complete pipeline
        result = pipeline.run_complete_pipeline()
        pipeline.save_processing_log(result)
        
        if result["success"]:
            print("✅ Pipeline completed successfully!")
            print(f"📄 Markdown file: {result['markdown_file']}")
            print(f"📊 Total reviews: {result['total_reviews']}")
            print(f"⏱️  Processing time: {result['processing_time_seconds']:.2f}s")
            print(f"📈 Sentiment distribution: {result['sentiment_distribution']}")
            
            # Run sample tests
            test_results = pipeline.test_sample_questions()
            print(f"\n🔍 Sample question tests: {len([r for r in test_results if r.get('success')])}/{len(test_results)} passed")
            
        else:
            print(f"❌ Pipeline failed: {result['error']}")
            sys.exit(1)
    
    elif args.mode == "query":
        if not args.question:
            print("❌ Question required for query mode. Use --question")
            sys.exit(1)
        
        markdown_path = args.markdown or pipeline.markdown_file_path
        if not markdown_path or not os.path.exists(markdown_path):
            print("❌ Markdown file required for query mode. Run pipeline first or use --markdown")
            sys.exit(1)
        
        query_engine = EnhancedQueryEngine(markdown_path)
        result = query_engine.query(args.question)
        
        print(f"Question: {args.question}")
        print(f"Answer: {result.get('answer', 'No answer generated')}")
    
    elif args.mode == "test":
        # Test mode - run sample questions
        if not pipeline.markdown_file_path:
            print("❌ Run pipeline first to generate markdown file")
            sys.exit(1)
        
        test_results = pipeline.test_sample_questions()
        
        for result in test_results:
            print(f"\nQ: {result['question']}")
            if result.get('success'):
                print(f"A: {result['answer'][:200]}...")
            else:
                print(f"❌ Error: {result.get('error')}")

if __name__ == "__main__":
    main()