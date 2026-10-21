using System.Text.Json;

namespace ShipCore.Core;

/// <summary>One reading for the page. Null means not available right now: the first CPU figure has no earlier sample, and a HWiNFO value needs the sensor mapped and HWiNFO running.</summary>
public sealed record SystemFrame(long Seq, double? CpuPercent, double? MemoryPercent, ulong UptimeMs, bool? OnAc, int? BatteryPercent, IReadOnlyDictionary<string, double?> Hw, (double Down, double Up)? Net = null, double[]? Spectrum = null, IReadOnlyDictionary<string, bool>? Processes = null);

/// <summary>Builds one frame per call. Keeps the previous CPU and network samples, which the rates need.</summary>
public sealed class SystemSampler(ISystemMetrics metrics, IHwinfoRegistry registry, INetworkCounters? network = null, ISpectrumSource? spectrum = null, IProcessNames? processes = null)
{
    private CpuTimes? _prev;
    private NetCounters? _prevNet;
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

        var map = HwinfoSensors.MapFrom(settings);
        var hwinfo = new HwinfoSensors(registry, map);
        var hw = map.Keys.ToDictionary(name => name, hwinfo.Read);

        var running = processes is null ? null : WatchedNames(settings).ToDictionary(name => name, processes.IsRunning);

        return new SystemFrame(seq, cpuPercent, SystemMetrics.MemoryPercent(total, available), metrics.UptimeMs(), power.OnAc, power.BatteryPercent, hw, rate, spectrum?.Latest, running);
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
        hw = f.Hw,
    });
}
