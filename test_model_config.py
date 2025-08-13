#!/usr/bin/env python3
"""
Model Configuration API Testing Script
Demonstrates the new model configuration endpoints
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def get_session_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    return response.json().get("session_token") if response.status_code == 200 else None

def test_available_models():
    """Test listing available models"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Getting Available Models")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/models/available", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        print(f"Found {len(models)} models:")
        
        for model in models:
            name = model.get('name', 'Unknown')
            size = model.get('size', 0)
            size_mb = round(size / (1024 * 1024), 1) if size > 0 else 0
            print(f"  • {name} ({size_mb} MB)")
    else:
        print(f"Error: {response.json()}")
    
    print()

def test_current_model():
    """Test getting current model configuration"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("📋 Current Model Configuration")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/models/current", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        config = data.get('current_model', {})
        
        print(f"Model: {config.get('model', 'Unknown')}")
        print(f"Host: {config.get('host', 'Unknown')}")
        print(f"Temperature: {config.get('temperature', 'Unknown')}")
        print(f"Top-P: {config.get('top_p', 'Unknown')}")
        print(f"Top-K: {config.get('top_k', 'Unknown')}")
        print(f"Context Size: {config.get('num_ctx', 'Unknown')}")
        print(f"Timeout: {config.get('timeout', 'Unknown')}ms")
    else:
        print(f"Error: {response.json()}")
    
    print()

def test_model_configuration():
    """Test configuring model parameters"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("⚙️ Testing Model Configuration")
    print("=" * 50)
    
    # Test different configuration changes
    test_configs = [
        {
            "name": "High Creativity",
            "config": {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 50
            }
        },
        {
            "name": "Precise Mode",
            "config": {
                "temperature": 0.2,
                "top_p": 0.7,
                "top_k": 20
            }
        },
        {
            "name": "Large Context",
            "config": {
                "num_ctx": 8192
            }
        }
    ]
    
    for test_config in test_configs:
        print(f"--- Testing {test_config['name']} ---")
        
        response = requests.post(
            f"{BASE_URL}/api/models/configure",
            headers=headers,
            json=test_config['config']
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message', 'Success')}")
            print(f"Changes: {', '.join(data.get('changes', []))}")
        else:
            print(f"❌ Error: {response.json().get('error', 'Unknown error')}")
        
        print()
        time.sleep(1)  # Small delay between tests

def test_model_presets():
    """Test model presets"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🎯 Testing Model Presets")
    print("=" * 50)
    
    # Get available presets
    response = requests.get(f"{BASE_URL}/api/models/presets", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        presets = data.get('presets', {})
        
        print(f"Available presets: {list(presets.keys())}")
        print()
        
        # Test applying a preset
        preset_name = 'balanced'
        if preset_name in presets:
            print(f"--- Applying '{preset_name}' preset ---")
            
            response = requests.post(
                f"{BASE_URL}/api/models/preset/{preset_name}",
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Preset applied: {data.get('preset_applied')}")
                print(f"Description: {data.get('preset_description')}")
                print(f"Changes: {', '.join(data.get('changes', []))}")
            else:
                print(f"❌ Error: {response.json().get('error', 'Unknown error')}")
    else:
        print(f"❌ Failed to get presets: {response.json()}")
    
    print()

def test_model_test():
    """Test the model testing endpoint"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("🧪 Testing Model Response")
    print("=" * 50)
    
    test_messages = [
        "Hello, can you introduce yourself?",
        "What is artificial intelligence?",
        "Write a short poem about programming"
    ]
    
    for message in test_messages:
        print(f"--- Testing: {message} ---")
        
        response = requests.post(
            f"{BASE_URL}/api/models/test",
            headers=headers,
            json={"message": message}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('test_successful'):
                print(f"✅ Test successful")
                print(f"Model: {data.get('model', 'Unknown')}")
                print(f"Processing time: {data.get('processing_time_ms', 0)}ms")
                print(f"Tokens/sec: {data.get('tokens_per_second', 0)}")
                print(f"Response: {data.get('response', 'No response')}")
            else:
                print(f"❌ Test failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Request failed: {response.json()}")
        
        print()
        time.sleep(2)  # Delay between tests

def demonstrate_model_switching():
    """Demonstrate switching between models"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("🔄 Demonstrating Model Switching")
    print("=" * 50)
    
    # Get current model first
    current_response = requests.get(f"{BASE_URL}/api/models/current", headers=headers)
    if current_response.status_code == 200:
        current_model = current_response.json().get('current_model', {}).get('model', 'unknown')
        print(f"Current model: {current_model}")
    
    # Get available models
    models_response = requests.get(f"{BASE_URL}/api/models/available", headers=headers)
    if models_response.status_code == 200:
        available_models = [m.get('name', '') for m in models_response.json().get('models', [])]
        print(f"Available models: {available_models}")
        
        # Try to switch to a different model if available
        if len(available_models) > 1:
            # Find a different model
            for model in available_models:
                if model != current_model:
                    print(f"\n--- Switching to {model} ---")
                    
                    switch_response = requests.post(
                        f"{BASE_URL}/api/models/configure",
                        headers=headers,
                        json={"model": model}
                    )
                    
                    print(f"Switch status: {switch_response.status_code}")
                    if switch_response.status_code == 200:
                        print(f"✅ Successfully switched to {model}")
                        
                        # Test the new model
                        test_response = requests.post(
                            f"{BASE_URL}/api/models/test",
                            headers=headers,
                            json={"message": "Hello from the new model!"}
                        )
                        
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            if test_data.get('test_successful'):
                                print(f"✅ New model is working: {test_data.get('response', '')[:100]}...")
                            else:
                                print(f"❌ New model test failed: {test_data.get('error')}")
                        
                        # Switch back to original model
                        print(f"\n--- Switching back to {current_model} ---")
                        back_response = requests.post(
                            f"{BASE_URL}/api/models/configure",
                            headers=headers,
                            json={"model": current_model}
                        )
                        
                        if back_response.status_code == 200:
                            print(f"✅ Switched back to {current_model}")
                        else:
                            print(f"❌ Failed to switch back: {back_response.json()}")
                    else:
                        print(f"❌ Failed to switch: {switch_response.json()}")
                    
                    break
        else:
            print("Only one model available, cannot demonstrate switching")
    else:
        print(f"❌ Failed to get available models: {models_response.json()}")

def main():
    print("🤖 Model Configuration API Testing")
    print("=" * 60)
    
    # Test server health first
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️ Server health check returned {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Run all tests
    test_available_models()
    test_current_model()
    test_model_presets()
    test_model_configuration()
    test_model_test()
    demonstrate_model_switching()
    
    print("🎉 Model Configuration API Testing Complete!")
    print("\n💡 Available Endpoints:")
    print("   GET  /api/models/available     - List available models")
    print("   GET  /api/models/current       - Get current configuration")
    print("   POST /api/models/configure     - Configure model parameters")
    print("   POST /api/models/test          - Test current model")
    print("   GET  /api/models/presets       - Get configuration presets")
    print("   POST /api/models/preset/<name> - Apply configuration preset")

if __name__ == "__main__":
    main()