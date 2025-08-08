#!/usr/bin/env python3
"""
System Setup Script
Initializes the enhanced LLM system with RAG capabilities
"""

import os
import sys
import logging
from pathlib import Path

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import modules with error handling
try:
    from src.excel_to_md_converter import ExcelToMarkdownConverter
    from src.rag_system import RAGSystem
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Some dependencies not installed: {e}")
    print("Please run 'pip install -r requirements.txt' first")
    DEPENDENCIES_AVAILABLE = False

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def setup_directories():
    """Create necessary directories"""
    directories = [
        "src",
        "core", 
        "config",
        "scripts",
        "auth", 
        "uploads",
        "chroma_db",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"OK: Directory created/verified: {directory}")

def convert_excel_to_markdown():
    """Convert Excel files to combined markdown"""
    if not DEPENDENCIES_AVAILABLE:
        print("ERROR: Cannot convert Excel files - dependencies not installed")
        return False
        
    print("\nConverting Excel files to Markdown...")
    
    converter = ExcelToMarkdownConverter()
    success = converter.convert_all_files()
    
    if success:
        print("OK: Excel to Markdown conversion completed")
        return True
    else:
        print("ERROR: Excel to Markdown conversion failed")
        return False

def setup_rag_system():
    """Initialize and populate RAG system"""
    if not DEPENDENCIES_AVAILABLE:
        print("ERROR: Cannot setup RAG system - dependencies not installed")
        return False
        
    print("\nSetting up RAG system...")
    
    try:
        rag = RAGSystem()
        
        # Check if combined_data.md exists
        if not Path("combined_data.md").exists():
            print("ERROR: combined_data.md not found. Please run Excel conversion first.")
            return False
        
        # Try to reinitialize collection to fix any existing issues
        if hasattr(rag, 'reinitialize_collection'):
            print("Reinitializing collection to ensure compatibility...")
            rag.reinitialize_collection()
        
        # Ingest the document
        success = rag.ingest_document("combined_data.md", force_reload=True)
        
        if success:
            stats = rag.get_collection_stats()
            print(f"OK: RAG system setup completed")
            print(f"RAG Stats: {stats}")
            return True
        else:
            print("ERROR: RAG system setup failed")
            return False
            
    except Exception as e:
        print(f"ERROR: RAG system initialization failed: {str(e)}")
        print("Attempting to clear ChromaDB and retry...")
        
        # Try to clear the ChromaDB directory and retry
        try:
            import shutil
            chroma_path = Path("./chroma_db")
            if chroma_path.exists():
                shutil.rmtree(chroma_path)
                print("Cleared ChromaDB directory")
                
            # Retry initialization
            rag = RAGSystem()
            success = rag.ingest_document("combined_data.md", force_reload=True)
            
            if success:
                stats = rag.get_collection_stats()
                print(f"OK: RAG system setup completed after reset")
                print(f"RAG Stats: {stats}")
                return True
            else:
                print("ERROR: RAG system setup failed even after reset")
                return False
                
        except Exception as retry_error:
            print(f"ERROR: Could not recover RAG system: {str(retry_error)}")
            return False

def verify_system():
    """Verify system components"""
    print("\nVerifying system components...")
    
    checks = []
    
    # Check if combined_data.md exists
    if Path("combined_data.md").exists():
        checks.append(("Combined markdown file", True))
    else:
        checks.append(("Combined markdown file", False))
    
    # Check RAG system using the same approach as test_rag_config.py
    try:
        # Test embedding model availability directly (like test_rag_config.py)
        import requests
        import json
        
        # Load config
        with open("config/config.json", 'r') as f:
            config = json.load(f)
        
        embedding_config = config.get("rag", {}).get("embedding", {})
        model = embedding_config.get("model", "nomic-embed-text:latest")
        host = embedding_config.get("ollama_host", "http://localhost:11434")
        url = f"{host}/api/embeddings"
        
        # Test Ollama connection directly
        payload = {"model": model, "prompt": "test"}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        embedding_available = 'embedding' in result and len(result['embedding']) > 0
        
        checks.append(("RAG embedding model", embedding_available))
        
        # Check if documents exist without creating RAG system
        combined_data_exists = Path("combined_data.md").exists()
        checks.append(("RAG system", combined_data_exists))
        
    except Exception as e:
        checks.append(("RAG embedding model", False))
        checks.append(("RAG system", False))
    
    # Check required directories
    required_dirs = ["src", "uploads", "chroma_db"]
    for dir_name in required_dirs:
        checks.append((f"Directory: {dir_name}", Path(dir_name).exists()))
    
    # Print results
    print("\nSystem Verification Results:")
    print("-" * 40)
    
    all_good = True
    for component, status in checks:
        status_icon = "OK" if status else "ERROR"
        print(f"{status_icon} {component}")
        if not status:
            all_good = False
    
    print("-" * 40)
    if all_good:
        print("System verification passed! All components are ready.")
    else:
        print("WARNING: Some components need attention.")
    
    return all_good

def main():
    """Main setup function"""
    print("HE Team LLM Assistant - Enhanced Setup")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Step 1: Create directories
    print("\nSetting up directories...")
    setup_directories()
    
    # Step 2: Convert Excel files to Markdown (if dependencies available)
    if DEPENDENCIES_AVAILABLE:
        if convert_excel_to_markdown():
            # Step 3: Setup RAG system
            setup_rag_system()
    else:
        print("\nWARNING: Skipping Excel conversion and RAG setup - install dependencies first")
    
    # Step 4: Verify system
    verify_system()
    
    print("\n" + "=" * 50)
    print("Setup completed! Next steps:")
    print("1. Install requirements: pip install -r requirements.txt")
    
    # Check if we need to install embedding model using the same approach as verify_system
    try:
        import requests
        import json
        
        # Load config and test embedding model
        with open("config/config.json", 'r') as f:
            config = json.load(f)
        
        embedding_config = config.get("rag", {}).get("embedding", {})
        model = embedding_config.get("model", "nomic-embed-text:latest")
        host = embedding_config.get("ollama_host", "http://localhost:11434")
        url = f"{host}/api/embeddings"
        
        # Test Ollama connection
        payload = {"model": model, "prompt": "test"}
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        if 'embedding' in result and len(result['embedding']) > 0:
            print("2. Start the server: python server.py")
            print("3. Open enhanced UI: http://localhost:3000")
        else:
            print("2. Install embedding model: ollama pull nomic-embed-text:latest")
            print("3. Start the server: python server.py")
            print("4. Open enhanced UI: http://localhost:3000")
    except:
        print("2. Install embedding model: ollama pull nomic-embed-text:latest")
        print("3. Start the server: python server.py")
        print("4. Open enhanced UI: http://localhost:3000")
    
    print("=" * 50)

if __name__ == "__main__":
    main()