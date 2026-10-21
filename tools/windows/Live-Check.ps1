# Watch one live run of the standalone app. Dry run by default: it prints the steps and changes nothing.
#   Dry run:  powershell -ExecutionPolicy Bypass -File tools\windows\Live-Check.ps1
#   Run:      powershell -ExecutionPolicy Bypass -File tools\windows\Live-Check.ps1 -Run
# With -Run it starts the built app, samples it for 60 s, then waits up to 2 min for YOU to press Ctrl+Alt+Shift+1.
# It sends no keys and never force-kills. If the app is still alive at the end it reports that and leaves it for you to close.
param([switch]$Run, [int]$SampleSeconds = 60, [int]$KillWaitSeconds = 120)
$ErrorActionPreference = 'Stop'

$exe = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'SpaceshipApp\ShipCore.App\bin\Debug\net10.0-windows\ShipCore.App.exe'
$mode = if ($Run) { 'RUN' } else { 'dry run' }
Write-Host "Live check ($mode) of $exe"
if (-not (Test-Path $exe)) { throw "missing build output: run dotnet build SpaceshipApp\ShipCore.App first" }

if (-not $Run) {
    Write-Host 'Steps that -Run would do:'
    Write-Host "  1. Start the app (no arguments) and note its PID."
    Write-Host "  2. Sample for $SampleSeconds s: alive, descendant processes, msedgewebview2 count, newest perf CSV tail."
    Write-Host "  3. Ask you to press Ctrl+Alt+Shift+1, then watch up to $KillWaitSeconds s for the app and its children to end."
    Write-Host '  4. Print the result. Nothing is killed by this script.'
    Write-Host 'Run it with -Run only when the live test is approved.'
    exit 0
}

function Get-Tree([int]$root) {
    $all = Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name
    $set = New-Object System.Collections.Generic.HashSet[int]
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue($root)
    while ($queue.Count -gt 0) {
        $p = [int]$queue.Dequeue()
        foreach ($c in ($all | Where-Object { $_.ParentProcessId -eq $p })) {
            if ($set.Add([int]$c.ProcessId)) { $queue.Enqueue([int]$c.ProcessId) }
        }
    }
    return @($all | Where-Object { $set.Contains([int]$_.ProcessId) })
}
function Count-WebView2 { @(Get-Process msedgewebview2 -ErrorAction SilentlyContinue).Count }

$app = Start-Process -FilePath $exe -PassThru
Write-Host "APP_PID=$($app.Id)"
$start = Get-Date
while (((Get-Date) - $start).TotalSeconds -lt $SampleSeconds) {
    Start-Sleep -Seconds 5
    if ($app.HasExited) { Write-Host "APP_EXITED_EARLY code=$($app.ExitCode)"; break }
    $kids = @(Get-Tree $app.Id)
    Write-Host ("t={0,3}s alive descendants={1} webview2_total={2}" -f [int]((Get-Date) - $start).TotalSeconds, $kids.Count, (Count-WebView2))
}
$perf = Get-ChildItem (Join-Path $env:TEMP 'spaceship-app\perf-*.csv') -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
if ($perf) { Write-Host "PERF_FILE=$($perf.FullName)"; Get-Content $perf.FullName -Tail 5 } else { Write-Host 'PERF_FILE=none' }
$before = @(Get-Tree $app.Id)

Write-Host ''
Write-Host "NOW press Ctrl+Alt+Shift+1 (you press it; this script sends nothing). Waiting up to $KillWaitSeconds s."
$wait = Get-Date
while (-not $app.HasExited -and ((Get-Date) - $wait).TotalSeconds -lt $KillWaitSeconds) { Start-Sleep -Seconds 1 }

$exited = $app.HasExited
Write-Host "APP_EXITED_AFTER_CHORD=$exited"
$left = @($before | Where-Object { Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue })
Write-Host "DESCENDANTS_STILL_ALIVE=$($left.Count)"
$left | ForEach-Object { Write-Host "  still alive: pid=$($_.ProcessId) name=$($_.Name)" }
Write-Host "WEBVIEW2_TOTAL_AFTER=$(Count-WebView2)"
if (-not $exited) { Write-Host "NOT STOPPED: the app is still running (PID $($app.Id)). Close it yourself; the script did not kill it." }
if ($exited -and $left.Count -eq 0) { Write-Host 'RESULT=PASS (app and children gone)'; exit 0 }
Write-Host 'RESULT=FAIL (see lines above)'
exit 1
