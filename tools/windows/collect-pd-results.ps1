# Gathers what the P-D checklist asks for into ONE text file you can paste or attach. Read-only except for writing that file.
#   powershell -ExecutionPolicy Bypass -File tools\windows\collect-pd-results.ps1
# Written on Ubuntu and NOT run on Windows yet.
$dir = Join-Path $env:TEMP 'spaceship-pd'
$out = Join-Path $dir 'report.txt'
if (-not (Test-Path $dir)) { Write-Host "No $dir folder: run the prototype first."; exit 1 }
$lines = @()
$lines += "P-D report, $(Get-Date -Format s)"
$os = Get-CimInstance Win32_OperatingSystem
$lines += "OS: $($os.Caption) build $($os.BuildNumber)"
$lines += "CPU: $((Get-CimInstance Win32_Processor | Select-Object -First 1).Name)"
$lines += "GPU: $((Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + ' ' + $_.DriverVersion }) -join '; ')"
$lines += "Displays: $((Get-CimInstance Win32_VideoController | ForEach-Object { '' + $_.CurrentHorizontalResolution + 'x' + $_.CurrentVerticalResolution + '@' + $_.CurrentRefreshRate }) -join '; ')"
$lines += "WebView2 processes now: $(@(Get-Process msedgewebview2 -ErrorAction SilentlyContinue).Count)"
$lines += "Rainmeter running: $([bool](Get-Process Rainmeter -ErrorAction SilentlyContinue))"
$csv = Get-ChildItem $dir -Filter 'perf-*.csv' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($csv) {
  $rows = Import-Csv $csv.FullName | Where-Object { $_.cpu_percent_of_one_core -match '^[0-9.]+$' }
  $lines += "CSV: $($csv.Name), $($rows.Count) samples"
  if ($rows.Count -gt 0) {
    $cpu = $rows | ForEach-Object { [double]$_.cpu_percent_of_one_core }
    $fps = $rows | ForEach-Object { [double]$_.js_fps }
    $mem = $rows | ForEach-Object { [double]$_.working_set_mb }
    $lines += ("host CPU % of one core: avg {0:N1}, max {1:N1}" -f ($cpu | Measure-Object -Average).Average, ($cpu | Measure-Object -Maximum).Maximum)
    $lines += ("js fps: avg {0:N0}, min {1:N0}" -f ($fps | Measure-Object -Average).Average, ($fps | Measure-Object -Minimum).Minimum)
    $lines += ("host memory MB: avg {0:N0}, max {1:N0}" -f ($mem | Measure-Object -Average).Average, ($mem | Measure-Object -Maximum).Maximum)
  }
  $lines += "PROCESS_FAILED lines: $(@(Select-String -Path $csv.FullName -Pattern PROCESS_FAILED).Count)"
} else { $lines += 'No perf CSV found.' }
$lines += ''
$lines += 'Fill in by hand (docs/P-D-PROTOTYPE.md checklist): items 1-8 PASS/FAIL, and Task Manager CPU % / GPU % for Rainmeter vs the prototype (include every msedgewebview2.exe).'
$lines | Set-Content -Path $out -Encoding UTF8
Write-Host "Wrote $out"
$lines | ForEach-Object { Write-Host $_ }
