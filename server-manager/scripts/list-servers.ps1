$ErrorActionPreference = "Stop"
$stateFile = ".servers.json"
$logDir = ".server-logs"

if (Test-Path $stateFile) {
    $state = Get-Content $stateFile | ConvertFrom-Json
    $cleanServers = @()

    foreach ($entry in $state.servers) {
        $stillAlive = $false
        if ($entry.port) {
            $conn = Get-NetTCPConnection -LocalPort $entry.port -State Listen -ErrorAction SilentlyContinue
            if ($conn) { $stillAlive = $true }
        } elseif ($entry.pid) {
            $proc = Get-Process -Id $entry.pid -ErrorAction SilentlyContinue
            if ($proc) { $stillAlive = $true }
        }

        if ($stillAlive) {
            $cleanServers += $entry
        } else {
            Write-Output "[cleaned] $($entry.name) (was port: $($entry.port))"
        }
    }

    $state.servers = $cleanServers
    $state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8
}

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
    $status = "unknown"
    $uptime = "-"
    $logHint = ""

    if ($entry.port) {
        $conn = Get-NetTCPConnection -LocalPort $entry.port -State Listen -ErrorAction SilentlyContinue
        if ($conn) {
            $status = "running"
            try {
                $started = [DateTime]::Parse($entry.startedAt)
                $span = (Get-Date) - $started
                if ($span.TotalSeconds -lt 60) {
                    $uptime = "$([int]$span.TotalSeconds)s"
                } elseif ($span.TotalHours -lt 1) {
                    $uptime = "$([int]$span.TotalMinutes)m"
                } else {
                    $uptime = "$([int]$span.TotalHours)h"
                }
            } catch {}
        } else {
            $status = "?? port $($entry.port) not listening"
        }
    }

    if ($entry.logFile) {
        $logHint = "| log: $($entry.logFile)"
    }

    Write-Output "$($entry.name) | port: $($entry.port) | $uptime | $status $logHint"
}
