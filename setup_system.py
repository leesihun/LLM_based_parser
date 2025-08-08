#!/usr/bin/env python3
"""
System Setup Script
Initializes the enhanced LLM system with RAG capabilities
"""

import os
import sys
import logging
from pathlib import Path

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
    
    rag = RAGSystem()
    
    # Check if combined_data.md exists
    if not Path("combined_data.md").exists():
        print("ERROR: combined_data.md not found. Please run Excel conversion first.")
        return False
    
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

def verify_system():
    """Verify system components"""
    print("\nVerifying system components...")
    
    checks = []
    
    # Check if combined_data.md exists
    if Path("combined_data.md").exists():
        checks.append(("Combined markdown file", True))
    else:
        checks.append(("Combined markdown file", False))
    
    # Check RAG system
    if DEPENDENCIES_AVAILABLE:
        try:
            rag = RAGSystem()
            # Check embedding model availability
            embedding_available = rag.check_embedding_model_availability()
            stats = rag.get_collection_stats()
            checks.append(("RAG embedding model", embedding_available))
            checks.append(("RAG system", stats.get('document_count', 0) > 0))
        except Exception as e:
            checks.append(("RAG embedding model", False))
            checks.append(("RAG system", False))
    else:
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
    if DEPENDENCIES_AVAILABLE:
        # Check if we need to install embedding model
        try:
            rag = RAGSystem()
            if not rag.check_embedding_model_availability():
                print("2. Install embedding model: ollama pull nomic-embed-text:latest")
                print("3. Start the server: python server.py")
                print("4. Open enhanced UI: http://localhost:3000")
            else:
                print("2. Start the server: python server.py")
                print("3. Open enhanced UI: http://localhost:3000")
        except:
            print("2. Install embedding model: ollama pull nomic-embed-text:latest")
            print("3. Start the server: python server.py")
            print("4. Open enhanced UI: http://localhost:3000")
    else:
        print("2. Install embedding model: ollama pull nomic-embed-text:latest")
        print("3. Start the server: python server.py")
        print("4. Open enhanced UI: http://localhost:3000")
    print("=" * 50)

if __name__ == "__main__":
    main()