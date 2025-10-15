[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [int]$ListenPort = 8080,
    [int]$ConnectPort = 8080,
    [string]$ExternalHost,
    [string]$FirewallRuleName = "SearXNG 8080",
    [switch]$SkipCompose,
    [switch]$AllowNonAdmin
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Administrator {
    param(
        [switch]$Allow
    )
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        if (-not $Allow) {
            throw "This script must be run from an elevated PowerShell session."
        }
        Write-Warning "Not running as Administrator; portproxy/firewall steps may fail."
        return $false
    }
    return $true
}

function Invoke-WSLCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Command
    )

    & wsl.exe -d $Distro -- bash -lc "$Command"
    if ($LASTEXITCODE -ne 0) {
        throw "WSL command failed: $Command"
    }
}

function Get-WSLIPv4 {
    $raw = (& wsl.exe -d $Distro -- hostname -I).Trim()
    if (-not $raw) {
        throw "Unable to determine WSL IPv4 address (hostname -I returned empty output)."
    }

    $parts = $raw -split '\s+' | Where-Object { $_ -and $_ -match '^\d{1,3}(\.\d{1,3}){3}$' }
    if (-not $parts) {
        throw "hostname -I did not return an IPv4 address. Output: $raw"
    }

    return $parts[0]
}

function Get-HostIPv4 {
    $candidates = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
        Where-Object {
            $_.IPAddress -notmatch '^127\.' -and
            $_.IPAddress -notmatch '^169\.254' -and
            $_.PrefixOrigin -in @('Dhcp', 'Manual')
        } |
        Sort-Object -Property InterfaceMetric, SkipAsSource

    if (-not $candidates) {
        throw "Unable to determine an external IPv4 address for the host. Please specify -ExternalHost."
    }

    return $candidates[0].IPAddress
}

 $isAdmin = Assert-Administrator -Allow:$AllowNonAdmin

if (-not $ExternalHost) {
    $ExternalHost = Get-HostIPv4
}

if ($ExternalHost -notmatch '^\d{1,3}(\.\d{1,3}){3}$' -and $ExternalHost -notmatch '^[A-Za-z0-9\-\.]+$') {
    throw "ExternalHost '$ExternalHost' is not a valid IPv4 address or hostname."
}

Write-Host "Using external host: $ExternalHost" -ForegroundColor Cyan

# Ensure Docker is running inside WSL
Write-Host "Starting Docker service inside WSL ($Distro)..." -ForegroundColor Cyan
Invoke-WSLCommand "sudo service docker start"

# Update SearXNG hostname (.env) inside WSL
$envCommand = @"
cat <<'EOF' > /opt/searxng/searxng-docker/.env
SEARXNG_HOSTNAME={0}:{1}
EOF
"@ -f $ExternalHost, $ListenPort
Invoke-WSLCommand $envCommand

# Update docker-compose BASE_URL to reflect external host
$composeCommand = @'
sed -i "s|SEARXNG_BASE_URL=.*|      - SEARXNG_BASE_URL=http://{0}:{1}/|" /opt/searxng/searxng-docker/docker-compose.yaml
'@
$composeCommand = $composeCommand -f $ExternalHost, $ListenPort
try {
    Invoke-WSLCommand $composeCommand
} catch {
    Write-Warning "Failed to update docker-compose.yaml with external host: $_"
}

if (-not $SkipCompose) {
    Write-Host "Bringing up SearXNG stack via docker compose..." -ForegroundColor Cyan
    Invoke-WSLCommand "cd /opt/searxng/searxng-docker && docker compose up -d"
}

$wslIp = Get-WSLIPv4
Write-Host "WSL IPv4 address: $wslIp" -ForegroundColor Cyan

# Configure portproxy
if ($isAdmin) {
    Write-Host ("Configuring portproxy (0.0.0.0:{0} -> {1}:{2})..." -f $ListenPort, $wslIp, $ConnectPort) -ForegroundColor Cyan
    & netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=$ListenPort | Out-Null
    & netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=$ListenPort connectaddress=$wslIp connectport=$ConnectPort | Out-Null

    # Configure firewall rule
    Write-Host "Ensuring inbound firewall rule '$FirewallRuleName' allows TCP $ListenPort..." -ForegroundColor Cyan
    $existingRule = Get-NetFirewallRule -DisplayName $FirewallRuleName -ErrorAction SilentlyContinue
    if ($existingRule) {
        Remove-NetFirewallRule -DisplayName $FirewallRuleName -Confirm:$false
    }
    New-NetFirewallRule -DisplayName $FirewallRuleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $ListenPort | Out-Null
} else {
    Write-Warning "Skipped portproxy and firewall configuration (non-admin run). Remote access via host IP may not work until those steps are applied."
}

Write-Host ""
Write-Host ("SearXNG is now accessible at: http://{0}:{1}/search" -f $ExternalHost, $ListenPort) -ForegroundColor Green
Write-Host ("Portproxy target: {0}:{1}" -f $wslIp, $ConnectPort) -ForegroundColor Green
Write-Host ""
Write-Host "If you reboot, rerun this script to restore Docker, portproxy, and firewall settings." -ForegroundColor Yellow




