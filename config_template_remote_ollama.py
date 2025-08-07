
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
