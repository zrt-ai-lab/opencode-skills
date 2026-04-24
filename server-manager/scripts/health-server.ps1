param(
    [Parameter(Mandatory=$true)][string]$Name,
    [string]$Path = "/",
    [int]$TimeoutSec = 3
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

$port = $entry.port
$url = "http://localhost:$port$Path"

$start = Get-Date
try {
    $resp = Invoke-WebRequest -Uri $url -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
    $ms = [int]((Get-Date) - $start).TotalMilliseconds
    $status = $resp.StatusCode
    Write-Output "OK  $status  ${ms}ms  $url"
} catch {
    $msg = $_.Exception.Message
    if ($msg -match "Unable to connect" -or $msg -match "connection refused" -or $msg -match "timeout") {
        Write-Output "DOWN  connection refused  $url"
    } else {
        Write-Output "DOWN  $msg  $url"
    }
}