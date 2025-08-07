"""Troubleshooting script for LLM-based parser Ollama connection issues."""

import sys
from pathlib import Path
import logging

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent))

from config.config import config
import ollama
from ollama_client import OllamaClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def safe_extract_model_names(response):
    """Safely extract model names from Ollama response."""
    try:
        print(f"🔍 Debug - Raw response type: {type(response)}")
        print(f"🔍 Debug - Response keys: {list(response.keys()) if hasattr(response, 'keys') else 'Not a dict'}")
        
        models = []
        
        # Handle different response structures
        if 'models' in response:
            model_list = response['models']
            print(f"🔍 Debug - Found 'models' key with {len(model_list)} items")
        else:
            model_list = response if isinstance(response, list) else []
            print(f"🔍 Debug - Using response as direct list with {len(model_list)} items")
        
        # Extract names from each model entry
        for i, model in enumerate(model_list):
            print(f"🔍 Debug - Model {i}: {model}")
            print(f"🔍 Debug - Model {i} type: {type(model)}")
            print(f"🔍 Debug - Model {i} keys: {list(model.keys()) if hasattr(model, 'keys') else 'Not a dict'}")
            
            # Try different approaches based on type
            name = None
            
            if isinstance(model, str):
                # Model is directly a string (model name)
                name = model
                print(f"🔍 Debug - Model is string: {name}")
            elif isinstance(model, dict):
                # Model is a dictionary, try different field names
                name = model.get('name') or model.get('model') or model.get('id')
                if name:
                    print(f"🔍 Debug - Extracted from dict field: {name}")
                else:
                    print(f"🔍 Debug - Dict fields available: {list(model.keys())}")
                    # Try to get any string value from the dict
                    for key, value in model.items():
                        if isinstance(value, str) and value:
                            name = value
                            print(f"🔍 Debug - Using value from '{key}' field: {name}")
                            break
            else:
                print(f"🔍 Debug - Unknown model type: {type(model)}")
            
            if name:
                models.append(name)
                print(f"🔍 Debug - ✅ Extracted name: {name}")
            else:
                print(f"⚠️ Debug - ❌ Could not extract name from model {i}: {model}")
        
        return models
        
    except Exception as e:
        print(f"❌ Debug - Error extracting model names: {e}")
        print(f"🔍 Debug - Raw response: {response}")
        return []

def test_ollama_connection():
    """Test connection to Ollama server."""
    print("🔍 Testing Ollama Connection")
    print("=" * 50)
    
    try:
        # Test with configured host
        ollama_host = f"http://{config.ollama_host}"
        print(f"Connecting to Ollama at: {ollama_host}")
        
        client = ollama.Client(host=ollama_host)
        
        # Simple connection test - just try to call list() without parsing
        print("📞 Testing basic connection to Ollama...")
        response = client.list()
        
        print(f"✅ Connection successful!")
        print(f"Raw response type: {type(response)}")
        print("Ollama server is responding properly.")
        
        # Don't try to parse models - just confirm connection works
        return True, client, ["connection_verified"]
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"🔍 Debug - Error type: {type(e).__name__}")
        print(f"🔍 Debug - Error details: {str(e)}")
        
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if Ollama is running:")
        print("   ollama serve")
        print(f"2. Test manual connection:")
        print(f"   curl http://{config.ollama_host}/api/tags")
        print("3. Check host configuration in config/config.py:")
        print(f"   self.ollama_host = \"{config.ollama_host}\"")
        print("   Edit config/config.py to change host if needed")
        
        return False, None, []

def test_embedding_model():
    """Test if the embedding model is available."""
    print("\n🤖 Testing Embedding Model")
    print("=" * 50)
    
    success, client, _ = test_ollama_connection()
    if not success:
        return False
    
    embedding_model = config.embedding_model
    print(f"Required embedding model: {embedding_model}")
    
    # Skip model availability check - just test embedding generation directly
    print("Testing embedding generation...")
    try:
        response = client.embeddings(
            model=embedding_model,
            prompt="Test embedding generation"
        )
        
        if 'embedding' in response:
            embedding_dim = len(response['embedding'])
            print(f"✅ Embedding generation successful! Dimension: {embedding_dim}")
            print(f"✅ Model '{embedding_model}' is working correctly!")
            return True
        else:
            print("❌ Invalid response format from embedding API")
            print(f"Response keys: {list(response.keys()) if hasattr(response, 'keys') else 'Not a dict'}")
            return False
            
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        if "not found" in str(e).lower():
            print(f"💡 Install the model with: ollama pull {embedding_model}")
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
        print("2. Configure custom filenames in config/config.py:")
        print(f"   self.positive_filename = \"{config.positive_filename}\"")
        print(f"   self.negative_filename = \"{config.negative_filename}\"")
    
    return pos_exists and neg_exists

def test_ollama_client():
    """Test OllamaClient model detection (used by CLI)."""
    print("\n🤖 Testing OllamaClient Model Detection")
    print("=" * 50)
    
    try:
        print(f"Initializing OllamaClient with default model: {config.default_ollama_model}")
        ollama_client = OllamaClient(config.default_ollama_model)
        
        print("Testing get_available_models()...")
        available_models = ollama_client.get_available_models()
        
        if available_models:
            print(f"✅ Found {len(available_models)} models via OllamaClient:")
            for i, model in enumerate(available_models, 1):
                print(f"  {i}. {model}")
            
            # Check if the default model is available
            if config.default_ollama_model in available_models:
                print(f"✅ Default model '{config.default_ollama_model}' is available")
            else:
                print(f"❌ Default model '{config.default_ollama_model}' NOT found in available models")
                print(f"💡 Available models: {available_models}")
            
            return True
        else:
            print("❌ No models found via OllamaClient")
            print("This is the same issue you're seeing in cli.py query")
            
            # Compare with direct ollama client
            print("\n🔍 Comparing with direct ollama client...")
            direct_client = ollama.Client(host=f"http://{config.ollama_host}", timeout=config.ollama_timeout)
            direct_response = direct_client.list()
            print(f"Direct client response type: {type(direct_response)}")
            print(f"Direct client response: {direct_response}")
            
            return False
            
    except Exception as e:
        print(f"❌ OllamaClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_health():
    """Run complete system health check."""
    print("🏥 System Health Check")
    print("=" * 60)
    
    print(f"Configuration:")
    print(f"  - Ollama Host: {config.ollama_host}")
    print(f"  - Default Model: {config.default_ollama_model}")
    print(f"  - Embedding Model: {config.embedding_model}")
    print(f"  - Data Directory: {config.data_dir}")
    print(f"  - Positive File: {config.positive_filename}")
    print(f"  - Negative File: {config.negative_filename}")
    
    # Run all tests
    tests = [
        ("Ollama Connection", lambda: test_ollama_connection()[0]),
        ("Embedding Model", test_embedding_model),
        ("OllamaClient Detection", test_ollama_client),
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