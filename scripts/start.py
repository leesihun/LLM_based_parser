#!/usr/bin/env python3
"""
Startup script for Local LLM Backbone
Handles installation of dependencies and server startup
"""

import subprocess
import sys
import os
import json

def install_requirements():
    """Install Python requirements if needed"""
    try:
        import flask
        import flask_cors
        import requests
        print("✓ All dependencies are already installed")
        return True
    except ImportError:
        print("Installing required dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies")
            return False

def check_config():
    """Check if config file exists and is valid"""
    if not os.path.exists("config/config.json"):
        print("✗ config/config.json not found")
        return False
    
    try:
        with open("config/config.json", 'r') as f:
            config = json.load(f)
        print("✓ Configuration file is valid")
        return True
    except json.JSONDecodeError:
        print("✗ Invalid JSON in config/config.json")
        return False

def main():
    """Main startup function"""
    print("=" * 50)
    print("Local LLM Backbone - Startup")
    print("=" * 50)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Install dependencies
    if not install_requirements():
        sys.exit(1)
    
    print("\nStarting server...")
    print("=" * 50)
    
    # Start the server
    try:
        from server import main as server_main
        server_main()
    except ImportError:
        print("✗ Failed to import server module")
        sys.exit(1)

if __name__ == "__main__":
    main()