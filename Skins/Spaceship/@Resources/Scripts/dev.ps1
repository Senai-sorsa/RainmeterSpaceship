# wsl|ollama|tailscale|docker  - counts / states for the dev status block (-1 = not installed)
$ErrorActionPreference = 'SilentlyContinue'
$wsl = -1
if (Get-Command wsl.exe) { $wsl = @((wsl.exe -l --running -q) -replace "`0", '' | Where-Object { $_.Trim() }).Count }
$ollama = -1
if (Get-Command ollama) { $ollama = [math]::Max(0, @(ollama ps 2>$null).Count - 1) }
$ts = 'NONE'
if (Get-Command tailscale) { $j = tailscale status --json 2>$null | ConvertFrom-Json; if ($j) { $ts = $j.BackendState.ToUpper() } }
$docker = -1
if (Get-Command docker) { $docker = @(docker ps -q 2>$null).Count }
Write-Output "$wsl|$ollama|$ts|$docker"
