namespace ShipCore.Core;

/// <summary>Totals from GetSystemTimes, in 100 ns units. Kernel time includes idle time, as Windows reports it.</summary>
public readonly record struct CpuTimes(ulong Idle, ulong Kernel, ulong User);

public sealed record PowerSummary(bool? OnAc, int? BatteryPercent);

/// <summary>Reads Windows' own counters. The Windows host implements it; tests use a fake.</summary>
public interface ISystemMetrics
{
    CpuTimes ReadCpuTimes();
    (ulong Total, ulong Available) ReadMemory();
    /// <summary>SYSTEM_POWER_STATUS raw bytes: ACLineStatus (0 offline, 1 online, 255 unknown) and BatteryLifePercent (255 unknown).</summary>
    (byte AcLine, byte BatteryPercent) ReadPower();
    ulong UptimeMs();
    /// <summary>Time since the last keyboard or mouse input; null where it cannot be read.</summary>
    ulong? IdleMs() => null;
    /// <summary>Drive C: size and free bytes; null where it cannot be read.</summary>
    (ulong Total, ulong Free)? ReadDrive() => null;
    /// <summary>All physical disks' read plus write bytes per second since the previous call; null on the first call or when the counter is missing.</summary>
    double? DiskBytesPerSec() => null;
    /// <summary>The primary screen's refresh rate in Hz.</summary>
    int? RefreshHz() => null;
    /// <summary>The default speaker (capture false) or microphone (capture true) level; null when there is no such device.</summary>
    AudioLevel? ReadAudio(bool capture) => null;
    /// <summary>Battery time left in seconds as Windows estimates it; null on AC, while it is still estimating, or with no battery.</summary>
    uint? BatteryLifeSec() => null;
}

/// <summary>An audio endpoint's master level, 0 to 100, its mute flag and its Windows name (null when Windows does not say).</summary>
public sealed record AudioLevel(int Percent, bool Muted, string? Device);

/// <summary>Pure arithmetic over the counters, so the numbers the modules show are tested without the OS.</summary>
public static class SystemMetrics
{
    /// <returns>Busy share of the time between two samples, 0 to 100. Null when nothing elapsed or a counter went backwards.</returns>
    public static double? CpuPercent(CpuTimes prev, CpuTimes cur)
    {
        if (cur.Idle < prev.Idle || cur.Kernel < prev.Kernel || cur.User < prev.User) return null;
        var idle = cur.Idle - prev.Idle;
        var total = (cur.Kernel - prev.Kernel) + (cur.User - prev.User); // kernel already contains idle
        if (total == 0) return null;
        return Math.Clamp(100.0 * (total - idle) / total, 0, 100);
    }

    public static double MemoryPercent(ulong total, ulong available)
    {
        if (total == 0) return 0;
        return Math.Clamp(100.0 * (total - Math.Min(available, total)) / total, 0, 100);
    }

    public static PowerSummary Power(byte acLine, byte batteryPercent) => new(
        acLine switch { 0 => false, 1 => true, _ => null },
        batteryPercent == 255 ? null : Math.Min(batteryPercent, (byte)100));
}
