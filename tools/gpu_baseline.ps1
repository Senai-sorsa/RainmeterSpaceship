# gpu_baseline.ps1 - read-only GPU measurement for the HUD (Phase 10B, G1; CLAUDE.md section 4).
# Samples every GPU engine once a second and prints, per process and per GPU, the median and the peak utilisation, plus
# nvidia-smi's own number. It changes nothing. Run it once per condition and keep the output:
#   powershell -File tools\gpu_baseline.ps1 -Seconds 30 -Label "FULL, JARVIS running"
#   powershell -File tools\gpu_baseline.ps1 -Seconds 30 -Label "FULL, JARVIS quit"
#   ... then LITE, LOW, STEALTH (Control Center > PERFORMANCE), and with one skin unloaded at a time.
# Reading the result: "luid" is one GPU (the Radeon and the RTX each have one); the process rows say who uses it.
param(
    [int]$Seconds = 30,
    [string]$Label = ""
)

$samples = @{}      # "name|luid" -> list of per-second totals
$totals = @{}       # "luid" -> list of per-second totals
$smi = @()

for ($i = 0; $i -lt $Seconds; $i++) {
    $perSecond = @{}
    $perLuid = @{}
    try {
        $counters = (Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction Stop).CounterSamples
    } catch {
        Write-Output "No GPU engine counters on this PC: $($_.Exception.Message)"
        exit 1
    }
    foreach ($c in $counters) {
        if ($c.InstanceName -match 'pid_(\d+)_luid_(0x[0-9A-Fa-f]+_0x[0-9A-Fa-f]+)_') {
            $procId = [int]$Matches[1]
            $luid = $Matches[2]
            $name = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
            if (-not $name) { $name = "pid$procId" }
            $key = "$name|$luid"
            $perSecond[$key] = [double]$perSecond[$key] + $c.CookedValue
            $perLuid[$luid] = [double]$perLuid[$luid] + $c.CookedValue
        }
    }
    foreach ($k in $perSecond.Keys) {
        if (-not $samples.ContainsKey($k)) { $samples[$k] = New-Object System.Collections.ArrayList }
        [void]$samples[$k].Add([math]::Min(100, $perSecond[$k]))
    }
    foreach ($k in $perLuid.Keys) {
        if (-not $totals.ContainsKey($k)) { $totals[$k] = New-Object System.Collections.ArrayList }
        [void]$totals[$k].Add([math]::Min(100, $perLuid[$k]))
    }
    $one = & nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>$null
    if ($one) { $smi += [double]($one | Select-Object -First 1) }
}

function Median($list) {
    $s = @($list | Sort-Object)
    if ($s.Count -eq 0) { return 0 }
    return $s[[int][math]::Floor(($s.Count - 1) / 2)]
}

Write-Output "GPU baseline: $Label ($Seconds s, $(Get-Date -Format s))"
Write-Output "--- per GPU (all processes), % busy"
foreach ($k in ($totals.Keys | Sort-Object)) {
    Write-Output ("{0,-24} median {1,5:N1}  peak {2,5:N1}" -f $k, (Median $totals[$k]), ($totals[$k] | Measure-Object -Maximum).Maximum)
}
Write-Output "--- per process and GPU, % busy (only above 0.5)"
foreach ($k in ($samples.Keys | Sort-Object)) {
    $m = Median $samples[$k]
    $p = ($samples[$k] | Measure-Object -Maximum).Maximum
    if ($p -gt 0.5) { Write-Output ("{0,-40} median {1,5:N1}  peak {2,5:N1}" -f $k, $m, $p) }
}
if ($smi.Count -gt 0) {
    Write-Output ("--- nvidia-smi (the RTX only): median {0:N1}  peak {1:N1}" -f (Median $smi), ($smi | Measure-Object -Maximum).Maximum)
}
