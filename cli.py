"""Command-line interface for the LLM-based parser."""

import argparse
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from excel_reader import ExcelReader
from rag_system import RAGSystem
from config.config import config
import ollama


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
    
    # Load data using new detailed format
    print("📊 Loading review data with detailed metadata...")
    detailed_documents = excel_reader.get_detailed_documents()
    
    if not detailed_documents:
        print(f"❌ No review data found. Please ensure {config.positive_filename} and {config.negative_filename} exist in data/ directory.")
        return False
    
    # Show detailed statistics
    total_chars = sum(len(doc) for doc in detailed_documents)
    avg_chars = total_chars / len(detailed_documents) if detailed_documents else 0
    
    # Count sentiments from document text (they start with [POSITIVE] or [NEGATIVE])
    sentiments = {}
    for doc in detailed_documents:
        if doc.startswith("[POSITIVE]"):
            sentiments["positive"] = sentiments.get("positive", 0) + 1
        elif doc.startswith("[NEGATIVE]"):
            sentiments["negative"] = sentiments.get("negative", 0) + 1
        else:
            sentiments["unknown"] = sentiments.get("unknown", 0) + 1
    
    print(f"📈 Dataset Statistics:")
    print(f"   Total documents: {len(detailed_documents)}")
    print(f"   Average document length: {avg_chars:.0f} characters")
    print(f"   Sentiment distribution: {dict(sentiments)}")
    print(f"   Total context size: {total_chars:,} characters")
    
    # Add to RAG system
    print(f"🔄 Processing {len(detailed_documents)} detailed documents...")
    rag_system.clear_collection()
    rag_system.add_documents(detailed_documents)
    
    print(f"✅ Successfully loaded {len(detailed_documents)} detailed documents into RAG system")
    return True


def query_mode():
    """Interactive query mode using hybrid query engine."""
    print("💬 Entering interactive query mode...")
    print("Type 'quit' or 'exit' to stop\n")
    
    # Initialize components
    rag_system = RAGSystem(
        collection_name=config.rag_collection_name,
        embedding_model=config.embedding_model,
        persist_directory=str(config.chromadb_dir)
    )
    
    # Initialize Ollama client
    from src.ollama_client import OllamaClient
    ollama_client = OllamaClient()
    
    # Load documents for hybrid engine
    from src.excel_reader import ExcelReader
    reader = ExcelReader()
    detailed_documents = reader.get_detailed_documents()
    
    if not detailed_documents:
        print("❌ No documents found. Please run 'python cli.py setup' first.")
        return
    
    # Initialize hybrid query engine
    from src.query_engine import HybridQueryEngine
    query_engine = HybridQueryEngine(detailed_documents, rag_system, ollama_client)
    
    print(f"🤖 Using model: {config.default_ollama_model}")
    print(f"📊 Loaded {len(detailed_documents)} documents for analysis")
    print(f"🔧 Hybrid query engine ready (RAG + Analytics)\n")
    
    while True:
        try:
            query = input("❓ Enter your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print("\n🔍 Processing query...")
            
            # Process with hybrid query engine
            result = query_engine.process_query(query)
            
            print(f"📋 Query type: {result['type'].upper()} (confidence: {result['confidence']:.2f})")
            print(f"🔧 Modules used: {', '.join(result['modules_used'])}")
            
            # Display results based on query type
            if result['type'] == 'count':
                data = result['data']
                print(f"🔢 Count result: {data.get('count', 0)}")
                if 'breakdown' in data:
                    breakdown = data['breakdown']
                    print(f"   Breakdown: {breakdown.get('positive', 0)} positive, {breakdown.get('negative', 0)} negative")
                
            elif result['type'] == 'keyword_extraction':
                data = result['data']
                keywords = data.get('keywords', [])[:10]  # Show top 10
                print(f"🔑 Top keywords:")
                for i, (word, score) in enumerate(keywords, 1):
                    print(f"   {i}. {word} ({score:.2f})")
                
            elif result['type'] == 'statistics':
                data = result['data']
                sentiment_counts = data.get('sentiment_counts', {})
                print(f"📊 Dataset statistics:")
                print(f"   Total: {sentiment_counts.get('total', 0)} reviews")
                print(f"   Positive: {sentiment_counts.get('positive', 0)}")
                print(f"   Negative: {sentiment_counts.get('negative', 0)}")
                
            elif result['type'] == 'comparison':
                data = result['data']
                pos_keywords = data.get('keyword_comparison', {}).get('positive', [])[:5]
                neg_keywords = data.get('keyword_comparison', {}).get('negative', [])[:5]
                print(f"⚖️ Sentiment comparison:")
                print(f"   Top positive: {', '.join(word for word, score in pos_keywords)}")
                print(f"   Top negative: {', '.join(word for word, score in neg_keywords)}")
                
            else:  # semantic_search
                data = result['data']
                rag_results = data.get('rag_results', {})
                print(f"📋 Found {len(rag_results.get('documents', []))} relevant documents")
            
            print(f"\n💬 Response:")
            print(result['summary'])
            
            if 'error' in result:
                print(f"\n⚠️ Error: {result['error']}")
                
            print("-" * 80)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n👋 Goodbye!")


def launch_excel_viewer():
    """Launch the Excel viewer Jupyter notebook."""
    import subprocess
    import os
    from pathlib import Path
    
    notebook_path = Path("excel_viewer.ipynb")
    
    if not notebook_path.exists():
        print(f"❌ Excel viewer not found: {notebook_path}")
        print("Make sure excel_viewer.ipynb is in the current directory.")
        return
    
    print("📊 Launching Excel Viewer...")
    print(f"🚀 Opening Jupyter notebook: {notebook_path}")
    
    try:
        # Try to launch with jupyter
        print("🔧 Starting Jupyter Notebook...")
        subprocess.run(["jupyter", "notebook", str(notebook_path)], check=False)
    except FileNotFoundError:
        print("⚠️ Jupyter not found. Trying alternative methods...")
        
        # Try jupyter-lab as alternative
        try:
            print("🔧 Starting Jupyter Lab...")
            subprocess.run(["jupyter-lab", str(notebook_path)], check=False)
        except FileNotFoundError:
            print("❌ Neither 'jupyter notebook' nor 'jupyter-lab' found.")
            print("\n💡 Installation options:")
            print("   pip install notebook")
            print("   pip install jupyterlab")
            print("\n💡 Alternative: Open the file directly:")
            print(f"   - VS Code: Open {notebook_path}")
            print(f"   - Any Jupyter-compatible editor")
            print(f"   - Or copy/paste cells into a Python script")


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
  python cli.py view           # Launch Excel viewer (Jupyter notebook)
        """
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'query', 'status', 'view'],
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
    
    elif args.command == 'view':
        launch_excel_viewer()


if __name__ == "__main__":
    main()