param(
    [Parameter(Mandatory=$true)][string]$Name,
    [string]$Pattern,
    [ValidateSet("error","warn","info","debug","all")][string]$Level = "all",
    [int]$Lines = 50
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
if (-not (Test-Path $logFile)) {
    Write-Error "Log file not found: $logFile"
    exit 1
}

$levelPatterns = @{
    error = '(?i)\b(error|err|fail|fatal)\b'
    warn  = '(?i)\b(warn|warning)\b'
    info  = '(?i)\b(info|notice)\b'
    debug = '(?i)\b(debug|trace|verbose)\b'
}

$output = @()
$rawOutput = Get-Content $logFile -Tail $Lines -ErrorAction SilentlyContinue

if (-not $rawOutput) {
    Write-Output "Log is empty."
    exit 0
}

foreach ($line in $rawOutput) {
    $match = $true

    if ($Level -ne "all") {
        $re = $levelPatterns[$Level]
        if ($re -and $line -notmatch $re) {
            $match = $false
        }
    }

    if ($Pattern -and $match) {
        if ($line -notmatch [regex]::Escape($Pattern)) {
            $match = $false
        }
    }

    if ($match) {
        $output += $line
    }
}

if ($output.Count -eq 0) {
    $msg = "No matches"
    if ($Level -ne "all") { $msg += " [$Level]" }
    if ($Pattern) { $msg += " ""$Pattern""" }
    $msg += " in last $Lines lines."
    Write-Output $msg
    exit 0
}

$count = $output.Count
Write-Output "=== $count matches ==="
$output | ForEach-Object { Write-Output $_ }