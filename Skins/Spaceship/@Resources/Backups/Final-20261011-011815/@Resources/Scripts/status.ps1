# Reports GPU / power state for the top console, one key=value per line.
param([string]$Exe, [string]$Hybrid = 'hybrid-mode', [string]$Power = 'power-mode', [string]$Refresh = 'refresh-rate', [string]$Battery = 'battery')
$ErrorActionPreference = 'SilentlyContinue'
# Legion Toolkit moved from Program Files to %LOCALAPPDATA%\Programs in newer versions: try the
# configured path first, then the known install locations
function Resolve-Llt([string]$p) {
  $cands = @($p, "$env:LOCALAPPDATA\Programs\LenovoLegionToolkit\llt.exe", "$env:ProgramFiles\LenovoLegionToolkit\llt.exe",
             "${env:ProgramFiles(x86)}\LenovoLegionToolkit\llt.exe")
  foreach ($c in $cands) { if ($c -and (Test-Path $c)) { return $c } }
  return $p
}
$Exe = Resolve-Llt $Exe
$nv = Get-PnpDevice -Class Display | Where-Object { $_.FriendlyName -match 'NVIDIA' } | Select-Object -First 1
if ($nv) { Write-Output "dgpu=$(if ($nv.Status -eq 'OK') {'on'} else {'off'})" } else { Write-Output 'dgpu=off' }
if (Test-Path $Exe) {
  Write-Output 'llt=found'
  Write-Output "lltpath=$Exe"
  foreach ($f in @(@('hybrid', $Hybrid), @('power', $Power), @('refresh', $Refresh), @('battery', $Battery))) {
    $v = (& $Exe feature get $f[1] 2>$null | Out-String).Trim()
    Write-Output "$($f[0])=$v"
  }
} else { Write-Output 'llt=missing' }
