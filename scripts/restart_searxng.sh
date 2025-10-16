#!/bin/bash
# SearXNG Restart Script
# Restarts the SearXNG Docker container

echo "Restarting SearXNG container..."

# Restart the container
docker restart searxng

if [ $? -eq 0 ]; then
    echo "✓ SearXNG container restarted successfully"

    # Wait for service to be ready
    echo "Waiting for SearXNG to be ready..."
    sleep 3

    # Test if service responds
    echo "Testing SearXNG connection..."
    response=$(curl -s --max-time 5 'http://localhost:8080/search?q=test&format=json&language=en' | head -c 50)

    if [ -n "$response" ]; then
        echo "✓ SearXNG is responding"
        echo "Response preview: $response"
    else
        echo "✗ SearXNG is not responding yet, may need more time"
    fi
else
    echo "✗ Failed to restart SearXNG container"
    exit 1
fi
