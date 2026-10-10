# Builds (when missing or out of date) and starts the ShipCore helper. Run by the Controller on load and
# every 10 minutes, so the helper comes back if it was closed.  Output: core=<state>
$ErrorActionPreference = 'Stop'
$res = Split-Path $PSScriptRoot -Parent
$cs  = Join-Path $PSScriptRoot 'ShipCore.cs'
$bin = Join-Path $res 'Bin'
$exe = Join-Path $bin 'ShipCore.exe'
$log = Join-Path $res 'Data\shipcore.log'
try {
  New-Item -ItemType Directory -Force -Path $bin, (Join-Path $res 'Data') | Out-Null
  $stale = (-not (Test-Path $exe)) -or ((Get-Item $cs).LastWriteTimeUtc -gt (Get-Item $exe).LastWriteTimeUtc)
  if ($stale) {
    Get-Process ShipCore -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 300
    $csc = @("$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
             "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $csc) { Add-Content $log "$(Get-Date -f s) core: no C# compiler found"; Write-Output 'core=nocompiler'; exit 1 }
    $ErrorActionPreference = 'Continue'
    $out = & $csc /nologo /target:winexe /optimize+ "/out:$exe" /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Security.dll /r:System.Management.dll $cs 2>&1 | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -ne 0) { Add-Content $log "$(Get-Date -f s) core: build failed`r`n$out"; Write-Output 'core=buildfailed'; exit 1 }
    Add-Content $log "$(Get-Date -f s) core: built ShipCore.exe"
  }
  if (-not (Get-Process ShipCore -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $exe -ArgumentList @('watch', "`"$res`"") -WindowStyle Hidden
    Write-Output 'core=started'
  } else { Write-Output 'core=running' }
} catch {
  Add-Content $log "$(Get-Date -f s) core: $($_.Exception.Message)"
  Write-Output 'core=error'
}
