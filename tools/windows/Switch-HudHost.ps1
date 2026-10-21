# Switch the HUD from Rainmeter to the standalone host, or back. Dry run by default: it prints what it would do and changes nothing.
#   Dry run:   powershell -ExecutionPolicy Bypass -File tools\windows\Switch-HudHost.ps1
#   Apply:     ... -Apply     records the active Rainmeter skins, deactivates them, then asks the host to close
#   Rollback:  ... -Rollback  asks the host to close, then reactivates the recorded skins
# Never force-kills, never touches Run keys, power, or the recycle bin. Needs the host already running for -Apply,
# so the desktop is not left empty. Config layout read from %APPDATA%\Rainmeter\Rainmeter.ini: [Config\Sub\File] Active=1.
param([switch]$Apply, [switch]$Rollback)
$ErrorActionPreference = 'Stop'

$ini = Join-Path $env:APPDATA 'Rainmeter\Rainmeter.ini'
$rainmeter = Join-Path $env:ProgramFiles 'Rainmeter\Rainmeter.exe'
$state = Join-Path $env:LOCALAPPDATA 'Spaceship\cutover-state.json'
$hostProcess = 'ShipCore.App'
$mode = if ($Rollback) { 'rollback' } elseif ($Apply) { 'apply' } else { 'dry run' }

function Get-ActiveSkins {
    $section = ''
    $found = @()
    foreach ($line in Get-Content -LiteralPath $ini -Encoding Unicode) {
        if ($line -match '^\[(.+)\]$') { $section = $Matches[1] }
        elseif ($line -eq 'Active=1' -and $section -match '^([^\\]+)\\(.+)$') {
            $found += [pscustomobject]@{ Config = $Matches[1]; File = "$($Matches[2]).ini" }
        }
    }
    , $found
}

function Invoke-Bang($bang, $skin) {
    Write-Host "  Rainmeter.exe $bang `"$($skin.Config)`" `"$($skin.File)`""
    if (-not $Apply -and -not $Rollback) { return }
    & $rainmeter $bang $skin.Config $skin.File
    if ($LASTEXITCODE -ne 0) { throw "Rainmeter $bang failed for $($skin.Config)\$($skin.File): exit $LASTEXITCODE" }
}

function Close-Host {
    $proc = Get-Process -Name $hostProcess -ErrorAction SilentlyContinue
    if (-not $proc) { Write-Host '  host: not running'; return }
    Write-Host "  host: asking $hostProcess to close (no force-kill)"
    if (-not ($Apply -or $Rollback)) { return }
    $asked = $proc | ForEach-Object { $_.CloseMainWindow() }
    if (-not ($asked -contains $true)) { throw 'The host has no main window to close. Quit it from the tray menu, then run again.' }
    if ($proc | Where-Object { -not $_.WaitForExit(10000) }) {
        throw 'The host is still running after 10 s. Quit it from the tray menu, then run again.'
    }
}

Write-Host "Mode: $mode"
if (-not (Test-Path $rainmeter)) { throw "Rainmeter.exe not found at $rainmeter" }

if ($Rollback) {
    if (-not (Test-Path $state)) { throw "No recorded state at $state, nothing to roll back" }
    $recorded = @(Get-Content -LiteralPath $state -Raw | ConvertFrom-Json)
    Close-Host
    if (-not (Get-Process -Name Rainmeter -ErrorAction SilentlyContinue)) { Start-Process -FilePath $rainmeter }
    Write-Host "Reactivating $($recorded.Count) recorded skin file(s):"
    foreach ($skin in $recorded) { Invoke-Bang '!ActivateConfig' $skin }
    return
}

$active = Get-ActiveSkins
Write-Host "Active Rainmeter skin files: $($active.Count)"
if ($Apply -and -not (Get-Process -Name $hostProcess -ErrorAction SilentlyContinue)) {
    throw "$hostProcess is not running. Start the standalone host first, so the desktop is not left empty."
}
if ($Apply) {
    New-Item -ItemType Directory -Force -Path (Split-Path $state) | Out-Null
    $active | ConvertTo-Json | Set-Content -LiteralPath $state -Encoding utf8
    Write-Host "Recorded to $state"
}
Write-Host 'Deactivate:'
foreach ($skin in $active) { Invoke-Bang '!DeactivateConfig' $skin }
Close-Host
if (-not $Apply) { Write-Host 'Dry run only. Nothing was changed. Add -Apply to switch; -Rollback reverses it.' }
