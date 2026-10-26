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
}

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
