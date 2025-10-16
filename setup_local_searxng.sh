#!/bin/bash
# Setup SearXNG locally using Docker

echo "========================================="
echo "Local SearXNG Setup Script"
echo "========================================="

# Check Docker
echo -e "\n[1] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "    [FAIL] Docker not installed"
    echo "    Install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "    [OK] Docker found"

# Create SearXNG directory
echo -e "\n[2] Creating SearXNG configuration directory..."
mkdir -p ~/searxng
cd ~/searxng

# Create minimal config
echo -e "\n[3] Creating configuration..."
cat > settings.yml << 'YAML'
use_default_settings: true
server:
  secret_key: "$(openssl rand -hex 32)"
  limiter: false
  image_proxy: true
search:
  safe_search: 0
  autocomplete: ""
  default_lang: "en"
engines:
  - name: bing
    disabled: false
  - name: google
    disabled: false
  - name: duckduckgo
    disabled: false
YAML

# Pull and run SearXNG
echo -e "\n[4] Pulling SearXNG Docker image..."
docker pull searxng/searxng:latest

echo -e "\n[5] Starting SearXNG container..."
docker run -d \
  --name searxng-local \
  -p 8080:8080 \
  -v "$(pwd)/settings.yml:/etc/searxng/settings.yml:rw" \
  -e BASE_URL=http://localhost:8080/ \
  --restart unless-stopped \
  searxng/searxng:latest

# Wait for startup
echo -e "\n[6] Waiting for SearXNG to start..."
sleep 5

# Test
echo -e "\n[7] Testing SearXNG..."
for i in {1..10}; do
    if curl -s http://localhost:8080/ > /dev/null 2>&1; then
        echo "    [OK] SearXNG is running!"
        echo ""
        echo "    Access it at: http://localhost:8080"
        echo "    API endpoint: http://localhost:8080/search?q=test&format=json"
        echo ""
        echo "    To use in your config, change:"
        echo "    \"searxng_url\": \"http://localhost:8080\""
        exit 0
    fi
    echo "    Waiting... ($i/10)"
    sleep 2
done

echo "    [FAIL] SearXNG did not start properly"
echo "    Check logs: docker logs searxng-local"
exit 1
