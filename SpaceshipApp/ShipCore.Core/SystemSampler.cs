using System.Text.Json;

namespace ShipCore.Core;

/// <summary>One reading for the page. Null means not available right now: the first CPU figure has no earlier sample, and a HWiNFO value needs the sensor mapped and HWiNFO running.</summary>
public sealed record SystemFrame(long Seq, double? CpuPercent, double? MemoryPercent, ulong UptimeMs, bool? OnAc, int? BatteryPercent, IReadOnlyDictionary<string, double?> Hw, (double Down, double Up)? Net = null, double[]? Spectrum = null, IReadOnlyDictionary<string, bool>? Processes = null, double? GpuPercent = null, ulong MemoryTotal = 0, ulong MemoryUsed = 0, ulong? IdleMs = null,
    (ulong Total, ulong Free)? Drive = null, double? DiskIo = null, int? RefreshHz = null, AudioLevel? Speaker = null, AudioLevel? Mic = null);

/// <summary>Builds one frame per call. Keeps the previous CPU and network samples, which the rates need.</summary>
public sealed class SystemSampler(ISystemMetrics metrics, IHwinfoRegistry registry, INetworkCounters? network = null, ISpectrumSource? spectrum = null, IProcessNames? processes = null, IGpuCounters? gpu = null)
{
    private CpuTimes? _prev;
    private NetCounters? _prevNet;
    private Dictionary<string, int> _auto = new();
    private int _autoAge = 59; // the first sample matches at once
    private double? _gpu;
    private long _gpuAt = -2;
    // slow readings, held between reads: audio every 2 s (a dial turn shows within that), the drive and refresh rate every 30 s
    private (ulong, ulong)? _drive;
    private int? _hz;
    private long _slowAt = -30;
    private AudioLevel? _speaker, _mic;
    private double? _disk;
    private static readonly System.Text.RegularExpressions.Regex ProcessName = new(@"^[A-Za-z0-9_.-]{1,64}$");

    /// <summary>The WatchProcesses setting: comma-separated executable names. Names with other characters are dropped, and a trailing .exe is removed.</summary>
    public static IReadOnlyList<string> WatchedNames(IReadOnlyDictionary<string, string> settings)
    {
        if (!settings.TryGetValue("WatchProcesses", out var raw)) return [];
        return raw.Split(',').Select(s => s.Trim())
            .Select(s => s.EndsWith(".exe", StringComparison.OrdinalIgnoreCase) ? s[..^4] : s)
            .Where(s => ProcessName.IsMatch(s)).Distinct(StringComparer.OrdinalIgnoreCase).Take(16).ToList();
    }

    /// <param name="settings">The HW_ entries of settings.json are read here, so a sensor mapped while the app runs is picked up on the next frame.</param>
    /// <param name="elapsedSeconds">Time since the previous frame; the network rates are per second.</param>
    public SystemFrame Sample(IReadOnlyDictionary<string, string> settings, long seq, double elapsedSeconds = 1.0)
    {
        var cpu = metrics.ReadCpuTimes();
        var cpuPercent = _prev is { } p ? SystemMetrics.CpuPercent(p, cpu) : null;
        _prev = cpu;

        var net = network?.Read();
        var rate = net is { } n && _prevNet is { } pn ? NetworkRate.Rate(pn, n, elapsedSeconds) : null;
        _prevNet = net ?? _prevNet;

        var (total, available) = metrics.ReadMemory();
        var (ac, batteryRaw) = metrics.ReadPower();
        var power = SystemMetrics.Power(ac, batteryRaw);

        // Labels are matched once a minute, not every frame; a mapped index in settings wins over the match.
        if (++_autoAge >= 60) { _autoAge = 0; _auto = HwinfoSensors.AutoBind(registry.ReadLabels()); }
        var map = HwinfoSensors.MapFrom(settings);
        foreach (var (name, index) in _auto)
            if (!map.TryGetValue(name, out var set) || set < 0) map[name] = index;
        var hwinfo = new HwinfoSensors(registry, map);
        var hw = map.Keys.ToDictionary(name => name, hwinfo.Read);

        // every 2 s, the value held between: PDH expands every engine instance on each read
        if (seq - _gpuAt >= 2)
        {
            _gpuAt = seq;
            if (gpu is not null) _gpu = GpuLoad.Busiest(gpu.Read());
            _speaker = metrics.ReadAudio(false); _mic = metrics.ReadAudio(true);
            _disk = metrics.DiskBytesPerSec();
        }
        if (seq - _slowAt >= 30) { _slowAt = seq; _drive = metrics.ReadDrive(); _hz = metrics.RefreshHz(); }

        var running = processes is null ? null : WatchedNames(settings).ToDictionary(name => name, processes.IsRunning);

        return new SystemFrame(seq, cpuPercent, SystemMetrics.MemoryPercent(total, available), metrics.UptimeMs(), power.OnAc, power.BatteryPercent, hw, rate, spectrum?.Latest, running, _gpu,
            total, total - Math.Min(available, total), metrics.IdleMs(), _drive, _disk, _hz, _speaker, _mic);
    }

    /// <summary>The message the page receives: type system.metrics, one field per reading, nulls where a reading is missing.</summary>
    public static string ToJson(SystemFrame f) => JsonSerializer.Serialize(new
    {
        type = "system.metrics",
        seq = f.Seq,
        cpuPercent = f.CpuPercent,
        memoryPercent = f.MemoryPercent,
        uptimeMs = f.UptimeMs,
        onAc = f.OnAc,
        batteryPercent = f.BatteryPercent,
        netDown = f.Net?.Down,
        netUp = f.Net?.Up,
        spectrum = f.Spectrum,
        processes = f.Processes,
        gpuPercent = f.GpuPercent,
        memoryTotal = f.MemoryTotal,
        memoryUsed = f.MemoryUsed,
        idleMs = f.IdleMs,
        driveTotal = f.Drive?.Total,
        driveFree = f.Drive?.Free,
        diskIo = f.DiskIo,
        refreshHz = f.RefreshHz,
        volume = f.Speaker?.Percent,
        volumeMuted = f.Speaker?.Muted,
        audioDevice = f.Speaker?.Device,
        mic = f.Mic?.Percent,
        micMuted = f.Mic?.Muted,
        hw = f.Hw,
    });
}
