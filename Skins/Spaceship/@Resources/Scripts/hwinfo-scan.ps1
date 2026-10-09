# Lists HWiNFO gadget sensors as  index|sensor|label|value  into ..\Data\HWiNFO.txt
$ErrorActionPreference = 'SilentlyContinue'
$key = 'HKCU:\Software\HWiNFO64\VSB'
$out = Join-Path $PSScriptRoot '..\Data\HWiNFO.txt'
$lines = @()
if (Test-Path $key) {
  $p = Get-ItemProperty $key
  for ($i = 0; $i -lt 200; $i++) {
    $label = $p."Label$i"
    if ($null -eq $label) { continue }
    $lines += "$i|$($p."Sensor$i")|$label|$($p."ValueRaw$i")"
  }
}
[IO.File]::WriteAllLines($out, [string[]]$lines)
Write-Output "sensors=$($lines.Count)"
