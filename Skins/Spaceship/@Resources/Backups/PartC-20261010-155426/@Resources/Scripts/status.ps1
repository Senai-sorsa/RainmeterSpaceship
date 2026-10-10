# Reports GPU / power state for the top console, one key=value per line.
param([string]$Exe, [string]$Hybrid = 'hybrid-mode', [string]$Power = 'power-mode', [string]$Refresh = 'refresh-rate', [string]$Battery = 'battery')
$ErrorActionPreference = 'SilentlyContinue'
$nv = Get-PnpDevice -Class Display | Where-Object { $_.FriendlyName -match 'NVIDIA' } | Select-Object -First 1
if ($nv) { Write-Output "dgpu=$(if ($nv.Status -eq 'OK') {'on'} else {'off'})" } else { Write-Output 'dgpu=off' }
if (Test-Path $Exe) {
  Write-Output 'llt=found'
  foreach ($f in @(@('hybrid', $Hybrid), @('power', $Power), @('refresh', $Refresh), @('battery', $Battery))) {
    $v = (& $Exe feature get $f[1] 2>$null | Out-String).Trim()
    Write-Output "$($f[0])=$v"
  }
} else { Write-Output 'llt=missing' }
