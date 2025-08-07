#!/usr/bin/env python3
"""
Debug script for local Ollama model detection issues.
"""

import logging
from config.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_local_ollama():
    """Debug local Ollama model detection."""
    print("Local Ollama Model Detection Debug")
    print("=" * 45)
    
    config = Config()
    
    print(f"Configuration:")
    print(f"  Host: {config.ollama_host}")
    print(f"  Model: {config.default_ollama_model}")
    print(f"  URL: http://{config.ollama_host}")
    
    print(f"\nTrying to connect and get models...")
    
    try:
        # Try importing ollama
        import ollama
        print("✓ Ollama package imported successfully")
        
        # Create client
        ollama_host = f"http://{config.ollama_host}"
        client = ollama.Client(host=ollama_host, timeout=config.ollama_timeout)
        print(f"✓ Client created for {ollama_host}")
        
        # Try to get models
        print(f"\nCalling client.list()...")
        models_response = client.list()
        print(f"✓ Got response from ollama")
        
        # Debug the response format
        print(f"\nResponse Details:")
        print(f"  Type: {type(models_response)}")
        print(f"  Content: {models_response}")
        
        # Check if it's an object with models attribute
        if hasattr(models_response, 'models'):
            print(f"  Has .models attribute: True")
            model_list = models_response.models
            print(f"  models_response.models: {model_list}")
            print(f"  models type: {type(model_list)}")
        elif isinstance(models_response, dict) and 'models' in models_response:
            print(f"  Is dict with 'models' key: True")
            model_list = models_response['models']
            print(f"  models_response['models']: {model_list}")
            print(f"  models type: {type(model_list)}")
        else:
            print(f"  Unknown response format!")
            model_list = []
        
        # Parse individual models
        print(f"\nParsing individual models:")
        models = []
        for i, model in enumerate(model_list):
            print(f"  Model {i+1}:")
            print(f"    Type: {type(model)}")
            print(f"    Content: {model}")
            
            name = None
            if isinstance(model, dict):
                print(f"    Dict keys: {list(model.keys())}")
                name = model.get('name') or model.get('model') or model.get('id')
                print(f"    Extracted name: {name}")
            elif isinstance(model, str):
                name = model
                print(f"    String name: {name}")
            elif hasattr(model, 'name'):
                name = model.name
                print(f"    Object name: {name}")
            
            if name:
                models.append(name)
                print(f"    ✓ Added: {name}")
            else:
                print(f"    ✗ Could not extract name")
        
        print(f"\nFinal Results:")
        print(f"  Extracted models: {models}")
        print(f"  Count: {len(models)}")
        
        if len(models) == 0:
            print(f"\n❌ ISSUE FOUND: No models extracted")
            print(f"   Raw response: {models_response}")
            print(f"   Model list: {model_list}")
            
            # Suggest fixes
            print(f"\nPossible fixes:")
            print(f"  1. Check if Ollama is actually running: ollama serve")
            print(f"  2. Check if you have models installed: ollama list")
            print(f"  3. Try pulling a model: ollama pull llama3")
            print(f"  4. Check Ollama version: ollama --version")
        else:
            print(f"\n✓ SUCCESS: Found {len(models)} models")
            
            # Check if configured model exists
            if config.default_ollama_model in models:
                print(f"✓ Configured model '{config.default_ollama_model}' is available")
            else:
                print(f"⚠ Configured model '{config.default_ollama_model}' NOT found")
                print(f"  Available models: {models}")
                print(f"  Suggest updating config.py to use one of: {models}")
        
    except ImportError:
        print("❌ Failed to import ollama package")
        print("   Install with: pip install ollama")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e)}")
        print(f"   Make sure Ollama service is running: ollama serve")

def suggest_fixes():
    """Suggest common fixes for Ollama issues."""
    print(f"\nCommon Issues & Solutions:")
    print(f"-" * 30)
    print(f"1. Ollama not running:")
    print(f"   Solution: ollama serve")
    print(f"")
    print(f"2. No models installed:")
    print(f"   Solution: ollama pull llama3")
    print(f"   Or: ollama pull mistral")
    print(f"")
    print(f"3. Wrong model name in config:")
    print(f"   Check actual names with: ollama list")
    print(f"   Update config.py with correct name")
    print(f"")
    print(f"4. Ollama version issues:")
    print(f"   Check: ollama --version")
    print(f"   Update if needed")
    print(f"")
    print(f"5. Port issues:")
    print(f"   Default: localhost:11434")
    print(f"   Check if something else uses port 11434")

if __name__ == "__main__":
    debug_local_ollama()
    suggest_fixes()