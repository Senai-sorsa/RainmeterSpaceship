# Sets a Legion Toolkit feature through its CLI:  llt.ps1 -Exe <path> -Feature <name> -Value <value>
# Falls back to opening Legion Toolkit if the CLI is missing or refuses the value.
param([string]$Exe, [string]$Feature, [string]$Value)
# Legion Toolkit moved from Program Files to %LOCALAPPDATA%\Programs in newer versions: try the
# configured path first, then the known install locations
function Resolve-Llt([string]$p) {
  $cands = @($p, "$env:LOCALAPPDATA\Programs\LenovoLegionToolkit\llt.exe", "$env:ProgramFiles\LenovoLegionToolkit\llt.exe",
             "${env:ProgramFiles(x86)}\LenovoLegionToolkit\llt.exe")
  foreach ($c in $cands) { if ($c -and (Test-Path $c)) { return $c } }
  return $p
}
$Exe = Resolve-Llt $Exe
$log = Join-Path $PSScriptRoot '..\Data\llt.log'
if (-not (Test-Path $Exe)) {
  Add-Content $log "$(Get-Date -f s) CLI not found at $Exe"
  $gui = Join-Path (Split-Path $Exe) 'Lenovo Legion Toolkit.exe'
  if (Test-Path $gui) { Start-Process $gui }
  Write-Output 'result=missing'
  exit 1
}
$res = & $Exe feature set $Feature $Value 2>&1 | Out-String
Add-Content $log "$(Get-Date -f s) set $Feature $Value -> exit $LASTEXITCODE : $($res.Trim())"
if ($LASTEXITCODE -ne 0) {
  $gui = Join-Path (Split-Path $Exe) 'Lenovo Legion Toolkit.exe'
  if (Test-Path $gui) { Start-Process $gui }
  Write-Output "result=error"; exit 1
}
Write-Output 'result=ok'
