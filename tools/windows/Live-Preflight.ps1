# Read-only checks before the standalone app's live test. Changes nothing: no launch, no key presses, no registry writes.
#   powershell -ExecutionPolicy Bypass -File tools\windows\Live-Preflight.ps1
# Exit code 0 when every required check passes, 1 when one fails. WARN lines are advice, not failures.
$ErrorActionPreference = 'Continue'
$script:failed = 0
function Check([string]$name, [bool]$ok, [string]$detail, [switch]$Advice) {
    $tag = if ($ok) { 'PASS' } elseif ($Advice) { 'WARN' } else { 'FAIL'; $script:failed++ }
    Write-Host ("[{0}] {1,-28} {2}" -f $tag, $name, $detail)
}

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo
$exe = Join-Path $repo 'SpaceshipApp\ShipCore.App\bin\Debug\net10.0-windows\ShipCore.App.exe'
$settings = Join-Path $env:LOCALAPPDATA 'Spaceship\settings.json'
$marker = Join-Path $env:LOCALAPPDATA 'Spaceship\running.marker'
$schema = Join-Path $repo 'contract\config-keys.json'

$branch = (git rev-parse --abbrev-ref HEAD 2>&1) -join ''
Check 'git branch' ($branch -eq 'feature/standalone-host') "$branch (expected feature/standalone-host)"
$head = (git log --oneline -1 2>&1) -join ''
Check 'git head' ($LASTEXITCODE -eq 0) $head
Check 'build output' (Test-Path $exe) $(if (Test-Path $exe) { $exe } else { 'missing: run dotnet build SpaceshipApp\ShipCore.App first' })
Check 'contract schema' (Test-Path $schema) $schema
$wv = @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
        'HKCU:\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}') |
  ForEach-Object { (Get-ItemProperty $_ -ErrorAction SilentlyContinue).pv } | Where-Object { $_ } | Select-Object -First 1
Check 'WebView2 runtime' ([bool]$wv) $(if ($wv) { "version $wv" } else { 'not found: install the Evergreen runtime' })
$running = @(Get-Process ShipCore.App -ErrorAction SilentlyContinue)
Check 'app not already running' ($running.Count -eq 0) $(if ($running.Count -eq 0) { 'none' } else { "$($running.Count) running: close it first" })
Check 'leftover run marker' (-not (Test-Path $marker)) $(if (Test-Path $marker) { "$marker exists: the last run did not exit cleanly" } else { 'none' }) -Advice
Check 'settings file' (Test-Path $settings) $(if (Test-Path $settings) { $settings } else { 'absent: first run will import from the skin' }) -Advice
Check 'Rainmeter running' (-not (Get-Process Rainmeter -ErrorAction SilentlyContinue)) $(if (Get-Process Rainmeter -ErrorAction SilentlyContinue) { 'yes: two HUDs will overlap' } else { 'no' }) -Advice
$hw = [bool](Get-Process HWiNFO64, HWiNFO32 -ErrorAction SilentlyContinue)
Check 'HWiNFO running' $hw $(if ($hw) { 'yes' } else { 'no: the fallback sensor values will be used (HWiNFO path is not built yet)' }) -Advice
Write-Host ''
Write-Host "Manual, not checked here: press Ctrl+Alt+Shift+1 during the live run and watch that the app and its msedgewebview2 children all end."
Write-Host ("Result: {0} required check(s) failed." -f $script:failed)
exit $(if ($script:failed -eq 0) { 0 } else { 1 })
