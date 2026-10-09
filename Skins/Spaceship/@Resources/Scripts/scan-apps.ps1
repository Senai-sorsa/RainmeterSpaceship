# Writes ..\Data\StartApps.txt (Name|AppID per line) from the Start menu.
# Apps.ini "start:" targets are resolved against this list.
$ErrorActionPreference = 'SilentlyContinue'
$out = Join-Path $PSScriptRoot '..\Data\StartApps.txt'
$lines = Get-StartApps | Sort-Object Name | ForEach-Object { "$($_.Name)|$($_.AppID)" }
[IO.File]::WriteAllLines($out, [string[]]$lines)
Write-Output "apps=$($lines.Count)"
