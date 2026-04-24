param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$Command,
    [string]$Cwd,
    [int]$Port
)

$ErrorActionPreference = "Continue"
$stateFile = ".servers.json"
$logDir = ".server-logs"

if (-not (Test-Path $stateFile)) {
    @{ servers = @() } | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8
}

$state = Get-Content $stateFile | ConvertFrom-Json

if ($state.servers | Where-Object { $_.name -eq $Name }) {
    Write-Error "Server '$Name' already tracked. Use 'stop-server $Name' first."
    exit 1
}

if ($Cwd) {
    $workDir = $Cwd
} else {
    $workDir = $PWD.Path
}

$logFile = Join-Path $workDir "$logDir\$Name.log"

if (-not (Test-Path (Join-Path $workDir $logDir))) {
    New-Item -ItemType Directory -Path (Join-Path $workDir $logDir) -Force | Out-Null
}

$timestamp = Get-Date -Format "o"

$cmdArgs = "/c $Command > `"$logFile`" 2>&1"
Start-Process cmd -ArgumentList $cmdArgs -WorkingDirectory $workDir -WindowStyle Hidden -PassThru | Out-Null

$actualPort = $null
$serverPid = $null
$portNote = ""

if ($Port) {
    # Port was specified - check if it's already in use, auto-switch if needed
    $occupied = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($occupied) {
        $scannedPort = $Port + 1
        while ($scannedPort -le 65535) {
            $next = Get-NetTCPConnection -LocalPort $scannedPort -State Listen -ErrorAction SilentlyContinue
            if (-not $next) {
                $Port = $scannedPort
                $portNote = " (port $scannedPort free, auto-switched from original port)"
                break
            }
            $scannedPort++
        }
        if ($scannedPort -gt 65535) {
            Write-Error "No available port found starting from $Port"
            exit 1
        }
    }

    # Wait for the (possibly switched) port to come up
    $maxWait = 15
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep 1
        $waited++
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($conn) {
            $actualPort = $Port
            $serverPid = $conn[0].OwningProcess
            break
        }
    }

    if (-not $actualPort) {
        $portNote = " (port $Port not reached after ${maxWait}s, server may use different port)"
    }
} else {
    # No port specified - capture existing ports, then detect NEW ones after startup
    $existingPorts = @{}
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -ge 3000 -and $_.LocalPort -le 9999 } |
        ForEach-Object { $existingPorts[$_.LocalPort] = $true }

    Start-Sleep 2

    $newConn = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -ge 3000 -and $_.LocalPort -le 9999 -and -not $existingPorts.ContainsKey($_.LocalPort) } |
        Select-Object -First 1
    if ($newConn) {
        $actualPort = $newConn.LocalPort
        $serverPid = $newConn.OwningProcess
        $portNote = " (auto-detected port: $actualPort)"
    }
}

$entry = @{
    name = $Name
    port = $actualPort
    command = $Command
    cwd = $workDir
    pid = $serverPid
    startedAt = $timestamp
    logFile = $logFile
}

$state.servers += $entry
$state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8

$portInfo = if ($actualPort) { "port: $actualPort" } else { "no port detected" }
Write-Output "Started: $Name $portInfo$portNote"
Write-Output "Log: $logFile"