"""Troubleshooting script for LLM-based parser Ollama connection issues."""

import sys
from pathlib import Path
import logging

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent))

from config.config import config
import ollama

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_ollama_connection():
    """Test connection to Ollama server."""
    print("🔍 Testing Ollama Connection")
    print("=" * 50)
    
    try:
        # Test with configured host
        ollama_host = f"http://{config.ollama_host}"
        print(f"Connecting to Ollama at: {ollama_host}")
        
        client = ollama.Client(host=ollama_host)
        
        # Test basic connection
        response = client.list()
        models = [model['name'] for model in response['models']]
        
        print(f"✅ Connection successful!")
        print(f"Available models ({len(models)}):")
        for model in models:
            print(f"  - {model}")
        
        return True, client, models
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if Ollama is running:")
        print("   ollama serve")
        print(f"2. Test manual connection:")
        print(f"   curl http://{config.ollama_host}/api/tags")
        print("3. Check host configuration in .env:")
        print(f"   OLLAMA_HOST={config.ollama_host}")
        
        return False, None, []

def test_embedding_model():
    """Test if the embedding model is available."""
    print("\n🤖 Testing Embedding Model")
    print("=" * 50)
    
    success, client, models = test_ollama_connection()
    if not success:
        return False
    
    embedding_model = config.embedding_model
    print(f"Required embedding model: {embedding_model}")
    
    if embedding_model in models:
        print(f"✅ Embedding model '{embedding_model}' is available!")
        
        # Test actual embedding generation
        try:
            print("Testing embedding generation...")
            response = client.embeddings(
                model=embedding_model,
                prompt="Test embedding generation"
            )
            
            if 'embedding' in response:
                embedding_dim = len(response['embedding'])
                print(f"✅ Embedding generation successful! Dimension: {embedding_dim}")
                return True
            else:
                print("❌ Invalid response format from embedding API")
                return False
                
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return False
    else:
        print(f"❌ Embedding model '{embedding_model}' not found!")
        print(f"Install it with: ollama pull {embedding_model}")
        return False

def test_excel_files():
    """Test if Excel files exist."""
    print("\n📊 Testing Excel Files")
    print("=" * 50)
    
    print(f"Data directory: {config.data_dir}")
    print(f"Positive file: {config.positive_filename}")
    print(f"Negative file: {config.negative_filename}")
    
    pos_exists = config.positive_file.exists()
    neg_exists = config.negative_file.exists()
    
    if pos_exists:
        print(f"✅ Found positive file: {config.positive_file}")
    else:
        print(f"❌ Missing positive file: {config.positive_file}")
    
    if neg_exists:
        print(f"✅ Found negative file: {config.negative_file}")
    else:
        print(f"❌ Missing negative file: {config.negative_file}")
    
    if not (pos_exists and neg_exists):
        print("\n🔧 Solutions:")
        print("1. Place Excel files in data/ directory")
        print("2. Configure custom filenames in .env:")
        print(f"   POSITIVE_FILENAME={config.positive_filename}")
        print(f"   NEGATIVE_FILENAME={config.negative_filename}")
    
    return pos_exists and neg_exists

def test_system_health():
    """Run complete system health check."""
    print("🏥 System Health Check")
    print("=" * 60)
    
    print(f"Configuration:")
    print(f"  - Ollama Host: {config.ollama_host}")
    print(f"  - Embedding Model: {config.embedding_model}")
    print(f"  - Data Directory: {config.data_dir}")
    print(f"  - Positive File: {config.positive_filename}")
    print(f"  - Negative File: {config.negative_filename}")
    
    # Run all tests
    tests = [
        ("Ollama Connection", lambda: test_ollama_connection()[0]),
        ("Embedding Model", test_embedding_model),
        ("Excel Files", test_excel_files)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    print("\n📋 Summary")
    print("=" * 30)
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Your system is ready to use.")
        print("Run: python cli.py setup")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    test_system_health()