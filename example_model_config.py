#!/usr/bin/env python3
"""
Model Configuration API Examples
Demonstrates practical use cases for dynamic model configuration
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

def example_creative_writing():
    """Example: Configure model for creative writing"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("✍️ Example: Creative Writing Mode")
    print("=" * 50)
    
    # Apply creative preset
    print("Applying creative preset...")
    response = requests.post(f"{BASE_URL}/api/models/preset/creative", headers=headers)
    
    if response.status_code == 200:
        print("✅ Creative mode enabled")
        
        # Test with creative writing prompt
        chat_response = requests.post(
            f"{BASE_URL}/api/chat",
            headers=headers,
            json={"message": "Write a short story about a robot discovering emotions"}
        )
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            print(f"📝 Creative story (first 200 chars): {result['response'][:200]}...")
        else:
            print(f"❌ Chat failed: {chat_response.json()}")
    else:
        print(f"❌ Failed to set creative mode: {response.json()}")
    
    print()

def example_code_generation():
    """Example: Configure model for code generation"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("💻 Example: Code Generation Mode")
    print("=" * 50)
    
    # Apply coding preset
    print("Applying coding preset...")
    response = requests.post(f"{BASE_URL}/api/models/preset/coding", headers=headers)
    
    if response.status_code == 200:
        print("✅ Coding mode enabled")
        
        # Test with code generation prompt
        chat_response = requests.post(
            f"{BASE_URL}/api/chat",
            headers=headers,
            json={"message": "Write a Python function that finds the factorial of a number"}
        )
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            print(f"🐍 Generated code:\n{result['response']}")
        else:
            print(f"❌ Chat failed: {chat_response.json()}")
    else:
        print(f"❌ Failed to set coding mode: {response.json()}")
    
    print()

def example_research_analysis():
    """Example: Configure model for research and analysis"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("🔬 Example: Research Analysis Mode")
    print("=" * 50)
    
    # Apply research preset (large context)
    print("Applying research preset...")
    response = requests.post(f"{BASE_URL}/api/models/preset/research", headers=headers)
    
    if response.status_code == 200:
        print("✅ Research mode enabled (large context)")
        
        # Test with analytical prompt
        chat_response = requests.post(
            f"{BASE_URL}/api/chat",
            headers=headers,
            json={"message": "Analyze the pros and cons of renewable energy vs fossil fuels"}
        )
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            print(f"📊 Analysis (first 300 chars): {result['response'][:300]}...")
        else:
            print(f"❌ Chat failed: {chat_response.json()}")
    else:
        print(f"❌ Failed to set research mode: {response.json()}")
    
    print()

def example_model_switching():
    """Example: Switch between different models"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("🔄 Example: Model Switching")
    print("=" * 50)
    
    # Get available models
    models_response = requests.get(f"{BASE_URL}/api/models/available", headers=headers)
    
    if models_response.status_code == 200:
        models = [m['name'] for m in models_response.json()['models']]
        print(f"Available models: {models}")
        
        if len(models) >= 2:
            # Switch to first model
            first_model = models[0]
            print(f"\nSwitching to {first_model}...")
            
            response = requests.post(
                f"{BASE_URL}/api/models/configure",
                headers=headers,
                json={"model": first_model}
            )
            
            if response.status_code == 200:
                # Test first model
                test_response = requests.post(
                    f"{BASE_URL}/api/models/test",
                    headers=headers,
                    json={"message": "Hello from model 1"}
                )
                
                if test_response.status_code == 200:
                    test1_data = test_response.json()
                    print(f"✅ {first_model}: {test1_data['response'][:100]}...")
                    print(f"   Processing time: {test1_data['processing_time_ms']}ms")
                
                # Switch to second model
                second_model = models[1]
                print(f"\nSwitching to {second_model}...")
                
                response2 = requests.post(
                    f"{BASE_URL}/api/models/configure",
                    headers=headers,
                    json={"model": second_model}
                )
                
                if response2.status_code == 200:
                    # Test second model
                    test_response2 = requests.post(
                        f"{BASE_URL}/api/models/test",
                        headers=headers,
                        json={"message": "Hello from model 2"}
                    )
                    
                    if test_response2.status_code == 200:
                        test2_data = test_response2.json()
                        print(f"✅ {second_model}: {test2_data['response'][:100]}...")
                        print(f"   Processing time: {test2_data['processing_time_ms']}ms")
                        
                        # Compare performance
                        print(f"\n📈 Performance comparison:")
                        print(f"   {first_model}: {test1_data['processing_time_ms']}ms")
                        print(f"   {second_model}: {test2_data['processing_time_ms']}ms")
        else:
            print("Need at least 2 models to demonstrate switching")
    else:
        print(f"❌ Failed to get models: {models_response.json()}")
    
    print()

def example_custom_configuration():
    """Example: Create custom configuration for specific task"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("⚙️ Example: Custom Configuration")
    print("=" * 50)
    
    # Create custom config for Q&A tasks
    print("Creating custom configuration for Q&A tasks...")
    
    custom_config = {
        "temperature": 0.4,  # Moderate creativity
        "top_p": 0.8,        # Focus on likely responses
        "top_k": 25,         # Limited choices
        "num_ctx": 6144      # Good context size
    }
    
    response = requests.post(
        f"{BASE_URL}/api/models/configure",
        headers=headers,
        json=custom_config
    )
    
    if response.status_code == 200:
        print("✅ Custom Q&A configuration applied")
        print(f"Changes: {', '.join(response.json()['changes'])}")
        
        # Test with Q&A
        qa_questions = [
            "What is machine learning?",
            "How does photosynthesis work?",
            "Explain quantum computing in simple terms"
        ]
        
        for question in qa_questions:
            print(f"\n❓ Q: {question}")
            
            chat_response = requests.post(
                f"{BASE_URL}/api/chat",
                headers=headers,
                json={"message": question}
            )
            
            if chat_response.status_code == 200:
                result = chat_response.json()
                print(f"💡 A: {result['response'][:200]}...")
            else:
                print(f"❌ Failed: {chat_response.json()}")
            
            time.sleep(1)  # Small delay between questions
    else:
        print(f"❌ Failed to apply custom config: {response.json()}")
    
    print()

def example_optimization_testing():
    """Example: Test different configurations for optimization"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("🏎️ Example: Performance Optimization Testing")
    print("=" * 50)
    
    test_message = "Explain the concept of artificial intelligence"
    
    # Test different temperature settings
    temperature_tests = [0.1, 0.3, 0.7, 0.9]
    
    print("Testing different temperature settings...")
    results = []
    
    for temp in temperature_tests:
        print(f"\nTesting temperature {temp}...")
        
        # Configure
        config_response = requests.post(
            f"{BASE_URL}/api/models/configure",
            headers=headers,
            json={"temperature": temp}
        )
        
        if config_response.status_code == 200:
            # Test
            test_response = requests.post(
                f"{BASE_URL}/api/models/test",
                headers=headers,
                json={"message": test_message}
            )
            
            if test_response.status_code == 200:
                test_data = test_response.json()
                results.append({
                    'temperature': temp,
                    'processing_time': test_data['processing_time_ms'],
                    'tokens_per_second': test_data.get('tokens_per_second', 0),
                    'response_length': test_data['response_length']
                })
                print(f"   ⏱️ {test_data['processing_time_ms']}ms")
                print(f"   🚀 {test_data.get('tokens_per_second', 0)} tokens/sec")
    
    # Show results
    if results:
        print(f"\n📊 Temperature Performance Comparison:")
        print(f"{'Temp':<6} {'Time (ms)':<10} {'Tokens/sec':<12} {'Length':<8}")
        print("-" * 40)
        for result in results:
            print(f"{result['temperature']:<6} {result['processing_time']:<10.1f} {result['tokens_per_second']:<12.1f} {result['response_length']:<8}")
        
        # Find fastest
        fastest = min(results, key=lambda x: x['processing_time'])
        print(f"\n🏆 Fastest: Temperature {fastest['temperature']} ({fastest['processing_time']:.1f}ms)")

def main():
    print("🤖 Model Configuration API - Practical Examples")
    print("=" * 60)
    
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️ Server responded with {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    print()
    
    # Run practical examples
    example_creative_writing()
    example_code_generation()
    example_research_analysis()
    example_model_switching()
    example_custom_configuration()
    example_optimization_testing()
    
    print("🎉 All examples completed!")
    print("\n💡 Key Benefits:")
    print("   • Dynamic model switching without restart")
    print("   • Task-specific optimization presets")
    print("   • Real-time performance testing")
    print("   • Custom configuration for specific use cases")
    print("   • A/B testing different model parameters")

if __name__ == "__main__":
    main()