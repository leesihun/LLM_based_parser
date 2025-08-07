"""Command-line interface for the LLM-based parser."""

import argparse
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from excel_reader import ExcelReader
from rag_system import RAGSystem
from ollama_client import OllamaClient
from config.config import config


def setup_rag_system():
    """Initialize and populate RAG system with data."""
    print("🚀 Initializing RAG system...")
    
    # Initialize components
    excel_reader = ExcelReader()  # Uses config defaults
    rag_system = RAGSystem(
        collection_name=config.rag_collection_name,
        embedding_model=config.embedding_model,
        persist_directory=str(config.chromadb_dir)
    )
    
    # Load data
    print("📊 Loading review data...")
    review_texts = excel_reader.get_review_texts()
    
    if not review_texts:
        print(f"❌ No review data found. Please ensure {config.positive_filename} and {config.negative_filename} exist in data/ directory.")
        return False
    
    # Add to RAG system
    print(f"🔄 Processing {len(review_texts)} reviews...")
    rag_system.clear_collection()
    rag_system.add_documents(review_texts)
    
    print(f"✅ Successfully loaded {len(review_texts)} reviews into RAG system")
    return True


def query_mode():
    """Interactive query mode."""
    print("💬 Entering interactive query mode...")
    print("Type 'quit' or 'exit' to stop\n")
    
    # Initialize components
    rag_system = RAGSystem(
        collection_name=config.rag_collection_name,
        embedding_model=config.embedding_model,
        persist_directory=str(config.chromadb_dir)
    )
    ollama_client = OllamaClient(config.default_ollama_model)
    
    # Check if we can connect to Ollama and use the configured model
    try:
        # Test with a simple model check - don't try to parse complex responses
        available_models = ollama_client.get_available_models()
        
        if available_models and ollama_client.default_model in available_models:
            print(f"🤖 Using model: {ollama_client.default_model}")
            print(f"📋 Other available models: {', '.join(available_models)}\n")
        elif available_models:
            print(f"⚠️ Configured model '{ollama_client.default_model}' not found")
            print(f"📋 Available models: {', '.join(available_models)}")
            print(f"🤖 Will try to use configured model anyway\n")
        else:
            # Fall back to just trying to use the configured model
            print(f"🤖 Using configured model: {ollama_client.default_model}")
            print("⚠️ Could not list models, but will proceed with configured model\n")
            
    except Exception as e:
        print(f"⚠️ Model detection failed: {e}")
        print(f"🤖 Will try using configured model: {ollama_client.default_model}\n")
    
    while True:
        try:
            query = input("❓ Enter your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print("\n🔍 Searching relevant reviews...")
            context = rag_system.get_context_for_query(query, config.rag_context_size)
            
            print("🤖 Generating response...")
            response = ollama_client.generate_with_context(
                query=query,
                context=context,
                model=ollama_client.default_model
            )
            
            print(f"\n💬 Response:\n{response}\n")
            print("-" * 80)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM-based Parser for Cellphone Reviews",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py setup          # Initialize RAG system with review data
  python cli.py query          # Start interactive query mode
  python cli.py status         # Show system status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'query', 'status'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Specify Ollama model to use'
    )
    
    args = parser.parse_args()
    
    # Update default model if specified
    if args.model:
        config.default_ollama_model = args.model
    
    if args.command == 'setup':
        success = setup_rag_system()
        sys.exit(0 if success else 1)
    
    elif args.command == 'query':
        query_mode()
    
    elif args.command == 'status':
        print("📊 System Status:")
        print(f"Config: {config.to_dict()}")
        print(f"Files: {config.get_file_status()}")


if __name__ == "__main__":
    main()