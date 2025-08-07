#!/usr/bin/env python3
"""
Debug script for Ollama connection and model detection issues.
"""

import logging
from config.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_ollama_connection():
    """Debug Ollama connection without requiring actual connection."""
    print("Ollama Connection Debug")
    print("=" * 40)
    
    config = Config()
    
    print(f"Current Configuration:")
    print(f"  Ollama Host: {config.ollama_host}")
    print(f"  Default Model: {config.default_ollama_model}")
    print(f"  Timeout: {config.ollama_timeout}")
    print(f"  Full URL: http://{config.ollama_host}")
    
    print("\nCommon Issues & Solutions:")
    print("-" * 30)
    
    print("\n1. REMOTE MACHINE SETUP:")
    print("   If Ollama is on a different machine, you need to:")
    print("   a) Update config/config.py:")
    print("      self.ollama_host = 'REMOTE_IP:11434'  # Replace REMOTE_IP")
    print("   b) Make sure Ollama server allows external connections:")
    print("      OLLAMA_HOST=0.0.0.0 ollama serve")
    print("   c) Check firewall allows port 11434")
    
    print("\n2. MODEL NAME ISSUES:")
    print("   Current model: gemma3:12b")
    print("   Common alternatives:")
    print("   - llama3 or llama3:latest")
    print("   - mistral or mistral:latest") 
    print("   - qwen2 or qwen2:latest")
    print("   - gemma2 (not gemma3)")
    
    print("\n3. CONNECTION TESTING:")
    print("   Test manually from your machine:")
    print("   curl http://REMOTE_IP:11434/api/tags")
    print("   Should return JSON with model list")
    
    print("\n4. OLLAMA VERSION:")
    print("   Make sure Ollama version is compatible")
    print("   Minimum recommended: v0.1.9+")
    
    print("\n5. DEBUG STEPS:")
    print("   a) Check if Ollama service is running on remote machine")
    print("   b) Verify network connectivity (ping, telnet)")
    print("   c) Test API endpoint manually")
    print("   d) Update configuration with correct host/model")
    
def create_config_template():
    """Create a template for remote Ollama configuration."""
    template = '''
# Example configuration for remote Ollama setup
# Copy this to config/config.py and modify as needed

class Config:
    def __init__(self):
        # ... other settings ...
        
        # Ollama settings for REMOTE machine
        self.default_ollama_model = "llama3"  # or whatever model you have
        self.ollama_host = "192.168.1.100:11434"  # Replace with actual IP
        self.ollama_timeout = 120  # Longer timeout for network requests
        
        # ... rest of settings ...

# Steps to set up remote Ollama:
# 1. On remote machine, start Ollama with external access:
#    OLLAMA_HOST=0.0.0.0 ollama serve
#
# 2. Test from this machine:
#    curl http://192.168.1.100:11434/api/tags
#
# 3. Update the IP address above to match your remote machine
# 4. Update the model name to match what you have available
'''
    
    with open('config_template_remote_ollama.py', 'w') as f:
        f.write(template)
    
    print(f"\n6. CONFIGURATION TEMPLATE:")
    print(f"   Created: config_template_remote_ollama.py")
    print(f"   Review and copy relevant parts to config/config.py")

def test_connection_mock():
    """Mock test to show what should happen with working connection."""
    print(f"\n7. EXPECTED WORKING BEHAVIOR:")
    print(f"   INFO: Initializing Ollama client with host: http://REMOTE_IP:11434")
    print(f"   INFO: Found 3 available models: ['llama3', 'mistral', 'qwen2']")
    print(f"   INFO: Using model: llama3")
    print(f"   INFO: LLM query classifier initialized successfully")

if __name__ == "__main__":
    debug_ollama_connection()
    create_config_template()
    test_connection_mock()
    
    print(f"\nNext Steps:")
    print(f"1. Update config/config.py with your remote machine's IP and correct model name")
    print(f"2. Test the connection manually using curl")  
    print(f"3. Run your application again")
    print(f"4. If still issues, check the debug log messages for more details")