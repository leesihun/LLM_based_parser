# Simple SearXNG Portproxy Setup
# Run this script as Administrator to enable browser access to SearXNG

$WSL_IP = "172.20.221.97"
$PORT = 8080

Write-Host "Setting up portproxy for SearXNG..." -ForegroundColor Cyan
Write-Host "WSL IP: $WSL_IP" -ForegroundColor Yellow
Write-Host "Port: $PORT" -ForegroundColor Yellow

# Remove existing portproxy rule if it exists
Write-Host "`nRemoving any existing portproxy rules..." -ForegroundColor Cyan
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=$PORT 2>$null

# Add new portproxy rule
Write-Host "Adding portproxy rule (0.0.0.0:${PORT} -> ${WSL_IP}:${PORT})..." -ForegroundColor Cyan
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=$PORT connectaddress=$WSL_IP connectport=$PORT

# Show current portproxy rules
Write-Host "`nCurrent portproxy rules:" -ForegroundColor Cyan
netsh interface portproxy show v4tov4

# Configure firewall rule
Write-Host "`nConfiguring firewall rule..." -ForegroundColor Cyan
$ruleName = "SearXNG Port $PORT"

# Remove existing rule if it exists
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "Removing existing firewall rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName $ruleName -Confirm:$false
}

# Add new firewall rule
Write-Host "Adding firewall rule to allow TCP $PORT..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $PORT | Out-Null

Write-Host "`n" -NoNewline
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host "`nSearXNG is now accessible at:" -ForegroundColor Cyan
Write-Host "  - Homepage: http://localhost:$PORT" -ForegroundColor White
Write-Host "  - Search API: http://localhost:$PORT/search?q=YOUR_QUERY&format=json" -ForegroundColor White
Write-Host "`nYou can also access it from other devices on your network using:" -ForegroundColor Cyan
Write-Host "  - http://192.168.219.113:$PORT" -ForegroundColor White
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
