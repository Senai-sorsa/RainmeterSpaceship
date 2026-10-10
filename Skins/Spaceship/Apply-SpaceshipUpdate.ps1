<#
.SYNOPSIS
  Applies a Spaceship HUD update (the files in the "Spaceship" folder next to this script).

  - Finds your Spaceship skin: the one Rainmeter loads (Rainmeter.ini SkinPath) and, if present, the copy
    in C:\Users\<you>\RainmeterSpaceship\Skins\Spaceship - both get the update, so a rebuild from either
    can't bring the old files back.
  - Backs up every file it replaces to Spaceship\@Resources\Backups\<update>-<date>\ first.
  - Adds new settings to Settings.inc only if they're missing (never overwrites your values), and fixes
    LltPath if it points to a Legion Toolkit that isn't there.
  - Refreshes Rainmeter.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\Apply-SpaceshipUpdate.ps1            # apply
  powershell -ExecutionPolicy Bypass -File .\Apply-SpaceshipUpdate.ps1 -Restore   # undo the last update
#>
[CmdletBinding()]
param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $here 'Spaceship'
$updateName = (Get-Content (Join-Path $here 'UPDATE.txt') -TotalCount 1).Trim()
function Step($t) { Write-Host "`n>> $t" -ForegroundColor Cyan }

# ------------------------------------------------------------------ find the skin copies
$targets = New-Object System.Collections.Generic.List[string]
$rmIni = Join-Path $env:APPDATA 'Rainmeter\Rainmeter.ini'
if (Test-Path $rmIni) {
  $line = Select-String -Path $rmIni -Pattern '^\s*SkinPath\s*=\s*(.+)$' | Select-Object -First 1
  if ($line) {
    $p = Join-Path $line.Matches[0].Groups[1].Value.Trim().TrimEnd('\') 'Spaceship'
    if (Test-Path (Join-Path $p '@Resources\Scripts\lib.lua')) { $targets.Add((Resolve-Path $p).Path) }
  }
}
foreach ($c in @((Join-Path $env:USERPROFILE 'RainmeterSpaceship\Skins\Spaceship'),
                 (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Rainmeter\Skins\Spaceship'),
                 (Join-Path $env:USERPROFILE 'OneDrive\Documents\Rainmeter\Skins\Spaceship'))) {
  if ((Test-Path (Join-Path $c '@Resources\Scripts\lib.lua'))) {
    $r = (Resolve-Path $c).Path
    if (-not ($targets | Where-Object { $_ -ieq $r })) { $targets.Add($r) }
  }
}
if ($targets.Count -eq 0) { throw "Couldn't find your Spaceship skin folder." }
Write-Host "Spaceship skin copies found:"; $targets | ForEach-Object { Write-Host "  $_" }

$rmExe = $null
$proc = Get-Process Rainmeter -ErrorAction SilentlyContinue | Select-Object -First 1
if ($proc -and $proc.Path) { $rmExe = $proc.Path }
elseif (Test-Path "$env:ProgramFiles\Rainmeter\Rainmeter.exe") { $rmExe = "$env:ProgramFiles\Rainmeter\Rainmeter.exe" }

function Stop-Helper { Get-Process ShipCore -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue }

# ------------------------------------------------------------------ restore
if ($Restore) {
  Stop-Helper
  foreach ($t in $targets) {
    $b = Get-ChildItem (Join-Path $t '@Resources\Backups') -Directory -ErrorAction SilentlyContinue |
         Where-Object { $_.Name -like "$updateName-*" } | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $b) { Write-Host "  no backup of $updateName in $t"; continue }
    Step "Restoring $t from $($b.Name)"
    $manifest = Join-Path $b.FullName '_new_files.txt'
    Get-ChildItem $b.FullName -Recurse -File | Where-Object { $_.Name -ne '_new_files.txt' } | ForEach-Object {
      $rel = $_.FullName.Substring($b.FullName.Length + 1)
      Copy-Item $_.FullName (Join-Path $t $rel) -Force
    }
    if (Test-Path $manifest) { Get-Content $manifest | ForEach-Object { $f = Join-Path $t $_; if (Test-Path $f) { Remove-Item $f -Force } } }
  }
  if ($rmExe) { Start-Process $rmExe -ArgumentList '!RefreshApp' }
  Write-Host "`nRestored." -ForegroundColor Green; exit 0
}

# ------------------------------------------------------------------ apply
Stop-Helper
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$files = Get-ChildItem $src -Recurse -File
foreach ($t in $targets) {
  Step "Updating $t"
  $bk = Join-Path $t "@Resources\Backups\$updateName-$stamp"
  $new = New-Object System.Collections.Generic.List[string]
  foreach ($f in $files) {
    $rel = $f.FullName.Substring($src.Length + 1)
    $dst = Join-Path $t $rel
    if (Test-Path $dst) {
      $bdst = Join-Path $bk $rel
      New-Item -ItemType Directory -Force -Path (Split-Path $bdst) | Out-Null
      Copy-Item $dst $bdst -Force
    } else { $new.Add($rel) }
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    Copy-Item $f.FullName $dst -Force
  }
  New-Item -ItemType Directory -Force -Path $bk | Out-Null
  Set-Content -Path (Join-Path $bk '_new_files.txt') -Value $new
  # a new ShipCore.cs always gets a fresh build (the old helper could look newer than the new source)
  if (Test-Path (Join-Path $src '@Resources\Scripts\ShipCore.cs')) {
    $oldExe = Join-Path $t '@Resources\Bin\ShipCore.exe'
    if (Test-Path $oldExe) { Remove-Item $oldExe -Force -ErrorAction SilentlyContinue }
  }
  Write-Host "  $($files.Count) files written ($($new.Count) new), originals backed up to @Resources\Backups\$updateName-$stamp"

  # settings: add missing keys, fix a dead LltPath
  $set = Join-Path $t '@Resources\Settings.inc'
  if (Test-Path $set) {
    $text = Get-Content $set -Raw
    $adds = @()
    foreach ($line in (Get-Content (Join-Path $here 'settings-add.txt'))) {
      if ($line -match '^\s*;' -or $line.Trim() -eq '') { $adds += $line; continue }
      $key = ($line -split '=', 2)[0].Trim()
      if ($text -notmatch "(?m)^\s*$([regex]::Escape($key))\s*=") { $adds += $line } else { $adds += $null }
    }
    $real = $adds | Where-Object { $_ -and $_ -notmatch '^\s*;' -and $_.Trim() -ne '' }
    if ($real) {
      Add-Content -Path $set -Value ("`r`n" + (($adds | Where-Object { $_ -ne $null }) -join "`r`n"))
      Write-Host "  Settings.inc: added $(@($real).Count) new setting(s)"
    }
    $m = [regex]::Match($text, '(?m)^\s*LltPath\s*=\s*(.+?)\s*$')
    $llt = @("$env:LOCALAPPDATA\Programs\LenovoLegionToolkit\llt.exe", "$env:ProgramFiles\LenovoLegionToolkit\llt.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($m.Success -and -not (Test-Path $m.Groups[1].Value) -and $llt) {
      $text = Get-Content $set -Raw
      $text = [regex]::Replace($text, '(?m)^(\s*LltPath\s*=).*$', "`${1}$llt")
      Set-Content -Path $set -Value $text -NoNewline
      Write-Host "  Settings.inc: LltPath -> $llt"
    }
  }
}

Step 'Refreshing Rainmeter'
if ($rmExe) { Start-Process $rmExe -ArgumentList '!RefreshApp'; Write-Host '  done' }
else { Write-Host '  Rainmeter is not running - start it and the HUD loads the update.' }
Write-Host "`n$updateName applied. Undo with:  powershell -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`" -Restore" -ForegroundColor Green
