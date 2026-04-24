param(
    [Parameter(Mandatory=$true)][string]$Name
)

$ErrorActionPreference = "Stop"
$stateFile = ".servers.json"
if (-not (Test-Path $stateFile)) {
    Write-Error "No servers tracked."
    exit 1
}

$state = Get-Content $stateFile | ConvertFrom-Json
$entry = $state.servers | Where-Object { $_.name -eq $Name } | Select-Object -First 1

if (-not $entry) {
    Write-Error "Server '$Name' not found in tracking."
    exit 1
}

if ($entry.port) {
    $conn = Get-NetTCPConnection -LocalPort $entry.port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $killPid = $conn.OwningProcess | Select-Object -First 1
        Stop-Process -Id $killPid -Force -ErrorAction SilentlyContinue
    }
} elseif ($entry.pid) {
    Stop-Process -Id $entry.pid -Force -ErrorAction SilentlyContinue
}

$state.servers = $state.servers | Where-Object { $_.name -ne $Name }
$state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8

Write-Output "Stopped: $Name"
