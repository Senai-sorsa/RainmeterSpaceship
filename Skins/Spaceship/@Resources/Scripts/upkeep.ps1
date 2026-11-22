# updates|upgrades|antivirus  - pending Windows updates, winget upgrades, AV product + state.
$ErrorActionPreference = 'SilentlyContinue'
$updates = -1
try {
  $s = New-Object -ComObject Microsoft.Update.Session
  $r = $s.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0")
  $updates = $r.Updates.Count
} catch {}
$upgrades = -1
$w = winget upgrade --include-unknown --accept-source-agreements 2>$null | Out-String
if ($w) {
  $m = [regex]::Match($w, '(\d+)\s+upgrades? available')
  if ($m.Success) { $upgrades = [int]$m.Groups[1].Value } elseif ($w -match 'No installed package') { $upgrades = 0 }
}
$av = 'NONE'
$p = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Select-Object -First 1
if ($p) {
  $on = (([int]$p.productState -shr 12) -band 0xF) -eq 1
  $av = "$($p.displayName.ToUpper())|$(if ($on) {'ON'} else {'OFF'})"
}
Write-Output "$updates|$upgrades|$av"
