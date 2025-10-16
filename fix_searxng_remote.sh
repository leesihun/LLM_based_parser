#!/bin/bash
# Run this script on 192.168.219.113 to diagnose and fix SearXNG

echo "========================================="
echo "SearXNG Server Fix Script"
echo "========================================="

# Check if Docker is installed
echo -e "\n[1] Checking Docker..."
if command -v docker &> /dev/null; then
    echo "    [OK] Docker is installed"
    docker --version
else
    echo "    [FAIL] Docker not found"
    echo "    Install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if SearXNG container exists
echo -e "\n[2] Checking for SearXNG container..."
if docker ps -a | grep -q searxng; then
    echo "    [OK] SearXNG container found"
    
    # Check if it's running
    if docker ps | grep -q searxng; then
        echo "    [OK] Container is running"
        
        # Show logs
        echo -e "\n[3] Recent logs:"
        docker logs --tail 20 searxng
        
        # Check port binding
        echo -e "\n[4] Port bindings:"
        docker port searxng
        
    else
        echo "    [WARN] Container exists but is not running"
        echo "    Starting container..."
        docker start searxng
        sleep 3
        docker logs --tail 20 searxng
    fi
else
    echo "    [FAIL] No SearXNG container found"
    echo "    Would you like to create one? (This will use default settings)"
    echo ""
    echo "    To create SearXNG:"
    echo "    docker run -d --name searxng \\"
    echo "      -p 8080:8080 \\"
    echo "      -v \$(pwd)/searxng:/etc/searxng \\"
    echo "      --restart unless-stopped \\"
    echo "      searxng/searxng:latest"
fi

# Test endpoint
echo -e "\n[5] Testing HTTP endpoint..."
curl -s --max-time 3 http://localhost:8080/ > /dev/null
if [ $? -eq 0 ]; then
    echo "    [OK] SearXNG is responding on port 8080"
else
    echo "    [FAIL] SearXNG not responding"
    echo "    Check firewall: sudo ufw status"
    echo "    Check if port is in use: sudo netstat -tlnp | grep 8080"
fi

echo -e "\n========================================="
echo "Diagnostic complete"
echo "========================================="
