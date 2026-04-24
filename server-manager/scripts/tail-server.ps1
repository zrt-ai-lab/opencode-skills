param(
    [Parameter(Mandatory=$true)][string]$Name,
    [int]$Lines = 20
)

$stateFile = ".servers.json"
if (-not (Test-Path $stateFile)) {
    Write-Error "No servers tracked."
    exit 1
}

$state = Get-Content $stateFile | ConvertFrom-Json
$entry = $state.servers | Where-Object { $_.name -eq $Name } | Select-Object -First 1

if (-not $entry) {
    Write-Error "Server '$Name' not found."
    exit 1
}

$logFile = $entry.logFile
if (-not $logFile) {
    $logFile = ".server-logs\$Name.log"
}

if (-not (Test-Path $logFile)) {
    Write-Output "No log file found: $logFile"
    exit 0
}

$content = Get-Content $logFile -Tail $Lines -ErrorAction SilentlyContinue
if (-not $content) {
    Write-Output "Log is empty."
} else {
    $content | ForEach-Object { Write-Output $_ }
}
