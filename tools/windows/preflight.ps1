# Read-only checks before the P-D prototype run. Changes nothing. Run from the repo root:
#   powershell -ExecutionPolicy Bypass -File tools\windows\preflight.ps1
# Written on Ubuntu and NOT run on Windows yet: if a line errors, send the message.
$ErrorActionPreference = 'Continue'
function Show($name, $value) { Write-Host ("{0,-22} {1}" -f $name, $value) }
Show 'Repo' (Get-Location).Path
Show 'Branch' ((git rev-parse --abbrev-ref HEAD) 2>&1)
Show 'Commit' ((git log --oneline -1) 2>&1)
Show 'Uncommitted files' (@(git status --porcelain 2>&1).Count)
Show 'dotnet SDK' ((dotnet --version) 2>&1)
Show 'Node' ((node --version) 2>&1)
Show 'Python' ((py -3 --version) 2>&1)
$wv = @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
        'HKCU:\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}') |
  ForEach-Object { (Get-ItemProperty $_ -ErrorAction SilentlyContinue).pv } | Where-Object { $_ } | Select-Object -First 1
Show 'WebView2 runtime' ($(if ($wv) { $wv } else { 'NOT FOUND (install the Evergreen runtime from Microsoft)' }))
Show 'Rainmeter running' ($(if (Get-Process Rainmeter -ErrorAction SilentlyContinue) { 'yes' } else { 'no' }))
Show 'Prototype project' ($(if (Test-Path SpaceshipApp\ShipCore.Proto\ShipCore.Proto.csproj) { 'found' } else { 'MISSING: wrong folder or branch' }))
