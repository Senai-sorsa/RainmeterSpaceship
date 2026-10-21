using System.Text.Json;

namespace ShipCore.Core;

/// <summary>One reading for the page. Null means not available right now: the first CPU figure has no earlier sample, and a HWiNFO value needs the sensor mapped and HWiNFO running.</summary>
public sealed record SystemFrame(long Seq, double? CpuPercent, double? MemoryPercent, ulong UptimeMs, bool? OnAc, int? BatteryPercent, IReadOnlyDictionary<string, double?> Hw, (double Down, double Up)? Net = null);

/// <summary>Builds one frame per call. Keeps the previous CPU and network samples, which the rates need.</summary>
public sealed class SystemSampler(ISystemMetrics metrics, IHwinfoRegistry registry, INetworkCounters? network = null)
{
    private CpuTimes? _prev;
    private NetCounters? _prevNet;

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

        return new SystemFrame(seq, cpuPercent, SystemMetrics.MemoryPercent(total, available), metrics.UptimeMs(), power.OnAc, power.BatteryPercent, hw, rate);
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
        hw = f.Hw,
    });
}
