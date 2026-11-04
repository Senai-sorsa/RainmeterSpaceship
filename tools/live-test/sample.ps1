# Read-only: CPU (% of ONE core), RAM (MB) and GPU 3D/copy/video (%) summed over a process tree. Prints one JSON line.
param([int]$RootPid, [int]$Seconds = 8)
$all = @($RootPid)
do { $n = Get-CimInstance Win32_Process | Where-Object { $all -contains $_.ParentProcessId -and $all -notcontains $_.ProcessId } | Select-Object -Expand ProcessId; $all += $n } while ($n)
$t0 = @{}; foreach ($i in $all) { $p = Get-Process -Id $i -EA 0; if ($p) { $t0[$i] = $p.TotalProcessorTime.TotalSeconds } }
$sw = [Diagnostics.Stopwatch]::StartNew()
$g = Get-Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 1 -MaxSamples $Seconds
$el = $sw.Elapsed.TotalSeconds
$cpu = 0; $ram = 0
foreach ($i in $all) { $p = Get-Process -Id $i -EA 0; if ($p -and $t0.ContainsKey($i)) { $cpu += $p.TotalProcessorTime.TotalSeconds - $t0[$i]; $ram += $p.WorkingSet64 / 1MB } }
$gpu = @{}; $n = 0
foreach ($s in $g) { $n++; foreach ($c in $s.CounterSamples) { if ($c.InstanceName -match 'pid_(\d+)_.*engtype_(\w+)' -and ($all -contains [int]$matches[1])) { $gpu[$matches[2]] += $c.CookedValue } } }
$o = [ordered]@{ cpu = [math]::Round($cpu / $el * 100, 1); ram = [math]::Round($ram); procs = $all.Count }
foreach ($k in '3D', 'Copy', 'VideoDecode', 'Compute_0') { $o["gpu_$k"] = if ($gpu[$k]) { [math]::Round($gpu[$k] / $n, 2) } else { 0 } }
$o | ConvertTo-Json -Compress
