# diag.ps1: READ-ONLY look at this PC for "what is wrong?" (Phase 9). Prints ONE JSON object, exits 0.
# One sub-read that fails becomes null, the others still answer. Never prints event messages, window titles or the Wi-Fi name.
param(
    [Parameter(Mandatory = $true)][ValidateSet('processes', 'logs', 'network', 'system')][string]$Part,
    [ValidateRange(1, 720)][int]$Hours = 24
)
$ErrorActionPreference = 'SilentlyContinue'

function Get-Epoch($d) { [int64][math]::Floor(([DateTimeOffset]$d).ToUnixTimeSeconds()) }

function Get-Processes {
    $paths = '\Process(*)\% Processor Time', '\Process(*)\Working Set - Private', '\Process(*)\IO Data Bytes/sec',
             '\Process(*)\ID Process', '\GPU Engine(*)\Utilization Percentage', '\GPU Process Memory(*)\Dedicated Usage',
             '\PhysicalDisk(_Total)\% Disk Time'
    $s = $null
    try { $s = (Get-Counter -Counter $paths -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue).CounterSamples } catch { }
    if (-not $s) {                                  # a machine with no GPU counters can make the whole call fail: ask again without them
        $s = (Get-Counter -Counter ($paths | Where-Object { $_ -notlike '*GPU*' }) -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue).CounterSamples
    }
    $by = @{}; $gpu = @{}; $gmem = @{}; $disk = $null
    foreach ($x in $s) {
        $p = $x.Path; $i = $x.InstanceName
        if ($p -like '*\process(*') {
            if ($i -eq '_total' -or $i -eq 'idle') { continue }
            if (-not $by.ContainsKey($i)) { $by[$i] = @{ name = ($i -replace '#\d+$', ''); pid = 0; cpu = 0; mem = 0; io = 0 } }
            $v = $x.CookedValue
            if ($p -like '*% processor time') { $by[$i].cpu = [math]::Round($v, 1) }
            elseif ($p -like '*working set - private') { $by[$i].mem = [int64]$v }
            elseif ($p -like '*io data bytes/sec') { $by[$i].io = [int64]$v }
            elseif ($p -like '*id process') { $by[$i].pid = [int]$v }
        }
        elseif ($p -like '*\gpu engine(*') {
            if ($i -match 'pid_(\d+)_') { $k = [int]$Matches[1]; $gpu[$k] = [math]::Min(100, [double]$gpu[$k] + $x.CookedValue) }
        }
        elseif ($p -like '*\gpu process memory(*') {
            if ($i -match 'pid_(\d+)_') { $k = [int]$Matches[1]; $gmem[$k] = [int64]$gmem[$k] + [int64]$x.CookedValue }
        }
        elseif ($p -like '*physicaldisk(_total)*') { $disk = [math]::Round($x.CookedValue, 1) }
    }
    [ordered]@{
        cpus     = [int]$env:NUMBER_OF_PROCESSORS
        procs    = @($by.Values | ForEach-Object { [ordered]@{ name = $_.name; pid = $_.pid; cpu = $_.cpu; mem = $_.mem; io = $_.io } })
        gpu      = @($gpu.Keys | ForEach-Object { [ordered]@{ pid = $_; util = [math]::Round($gpu[$_], 1) } })
        gpumem   = @($gmem.Keys | ForEach-Object { [ordered]@{ pid = $_; bytes = $gmem[$_] } })
        disk_busy = $disk
    }
}

function Get-Boot {
    $b = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    if ($b) { Get-Epoch $b } else { $null }
}

function Get-Logs {
    $start = (Get-Date).AddHours(-$Hours)
    $ev = @()
    foreach ($log in 'System', 'Application') {
        $ev += @(Get-WinEvent -FilterHashtable @{ LogName = $log; Level = 1, 2; StartTime = $start } -MaxEvents 500 -ErrorAction SilentlyContinue |
            ForEach-Object {
                $app = $null                         # only the crashed/hung program's file name; the message text is never read
                if (($_.ProviderName -eq 'Application Error' -and $_.Id -eq 1000) -or ($_.ProviderName -eq 'Application Hang' -and $_.Id -eq 1002)) {
                    $app = [string]$_.Properties[0].Value
                }
                [ordered]@{ log = $log; provider = $_.ProviderName; id = [int]$_.Id; time = (Get-Epoch $_.TimeCreated); app = $app }
            })
    }
    [ordered]@{ boot = (Get-Boot); events = @($ev) }
}

function Get-Ping($addr) {
    $ms = $null
    try {
        $r = (New-Object System.Net.NetworkInformation.Ping).Send($addr, 1000)
        if ($r.Status -eq 'Success') { $ms = [int]$r.RoundtripTime }
    } catch { }
    $ms
}

function Get-Network {
    $wifi = $null
    try {
        $n = netsh wlan show interfaces 2>$null
        $st = $n | Where-Object { $_ -match '^\s*State\s*:' } | Select-Object -First 1
        $sg = $n | Where-Object { $_ -match '^\s*Signal\s*:' } | Select-Object -First 1
        if ($st) { $wifi = [ordered]@{ state = ($st -replace '^[^:]*:\s*', '').Trim(); signal = $(if ($sg -match '(\d+)\s*%') { [int]$Matches[1] } else { $null }) } }
    } catch { }
    $gw = $null
    try {
        $r = Get-NetRoute -DestinationPrefix 0.0.0.0/0 -ErrorAction Stop | Sort-Object RouteMetric | Select-Object -First 1
        if ($r) { $gw = [ordered]@{ ip = [string]$r.NextHop; ms = (Get-Ping $r.NextHop) } }
    } catch { }
    [ordered]@{
        wifi    = $wifi
        gateway = $gw
        public  = @(foreach ($a in '1.1.1.1', '8.8.8.8') { [ordered]@{ ip = $a; ms = (Get-Ping $a) } })
    }
}

function Get-System {
    $boot = Get-Boot
    $up = $null; if ($boot) { $up = [math]::Round(((Get-Epoch (Get-Date)) - $boot) / 86400, 1) }
    $pend = $null
    try {
        $pend = [bool]((Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or
                       (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired'))
    } catch { }
    $starts = $null; try { $starts = @(Get-CimInstance Win32_StartupCommand -ErrorAction Stop).Count } catch { }
    $bad = $null; try { $bad = @(Get-CimInstance Win32_PnPEntity -Filter 'ConfigManagerErrorCode <> 0' -ErrorAction Stop).Count } catch { }
    $bat = $null
    try {
        $b = Get-CimInstance Win32_Battery -ErrorAction Stop | Select-Object -First 1
        if ($b) { $bat = [ordered]@{ percent = [int]$b.EstimatedChargeRemaining; charging = [bool]($b.BatteryStatus -in 2, 6, 7, 8, 9) } }
    } catch { }
    [ordered]@{ boot = $boot; uptime_days = $up; reboot_pending = $pend; startup_count = $starts; faulty_devices = $bad; battery = $bat }
}

try {
    $out = switch ($Part) {
        'processes' { Get-Processes }
        'logs'      { Get-Logs }
        'network'   { Get-Network }
        'system'    { Get-System }
    }
    [Console]::Out.Write(($out | ConvertTo-Json -Compress -Depth 4))
    exit 0
}
catch { exit 1 }
