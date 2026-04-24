$ErrorActionPreference = "Stop"
$stateFile = ".servers.json"
if (-not (Test-Path $stateFile)) {
    Write-Output "No servers tracked."
    exit 0
}

$state = Get-Content $stateFile | ConvertFrom-Json
if ($state.servers.Count -eq 0) {
    Write-Output "No servers running."
    exit 0
}

foreach ($entry in $state.servers) {
    if ($entry.port) {
        $conn = Get-NetTCPConnection -LocalPort $entry.port -State Listen -ErrorAction SilentlyContinue
        if ($conn) {
            $killPid = $conn.OwningProcess | Select-Object -First 1
            Stop-Process -Id $killPid -Force -ErrorAction SilentlyContinue
        }
    } elseif ($entry.pid) {
        Stop-Process -Id $entry.pid -Force -ErrorAction SilentlyContinue
    }
    Write-Output "Stopped: $($entry.name)"
}

$state.servers = @()
$state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8
Write-Output "All servers stopped."
