using System.Runtime.InteropServices;
using Microsoft.Win32;
using ShipCore.Core;

// Windows implementations of ISystemMetrics and IHwinfoRegistry. Read-only: nothing here writes to the OS.

sealed class WindowsMetrics : ISystemMetrics
{
    [StructLayout(LayoutKind.Sequential)]
    struct MemoryStatusEx { public uint Length, MemoryLoad; public ulong TotalPhys, AvailPhys, TotalPageFile, AvailPageFile, TotalVirtual, AvailVirtual, AvailExtendedVirtual; }

    [StructLayout(LayoutKind.Sequential)]
    struct PowerStatus { public byte ACLineStatus, BatteryFlag, BatteryLifePercent, SystemStatusFlag; public uint BatteryLifeTime, BatteryFullLifeTime; }

    // FILETIME is passed as a 64-bit integer: same layout, and it avoids a struct for two fields.
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetSystemTimes(out long idle, out long kernel, out long user);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GlobalMemoryStatusEx(ref MemoryStatusEx status);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetSystemPowerStatus(out PowerStatus status);
    [DllImport("kernel32.dll")] static extern ulong GetTickCount64();

    public CpuTimes ReadCpuTimes()
    {
        if (!GetSystemTimes(out var idle, out var kernel, out var user)) throw new System.ComponentModel.Win32Exception();
        return new CpuTimes((ulong)idle, (ulong)kernel, (ulong)user);
    }

    public (ulong Total, ulong Available) ReadMemory()
    {
        var s = new MemoryStatusEx { Length = (uint)Marshal.SizeOf<MemoryStatusEx>() };
        if (!GlobalMemoryStatusEx(ref s)) throw new System.ComponentModel.Win32Exception();
        return (s.TotalPhys, s.AvailPhys);
    }

    public (byte AcLine, byte BatteryPercent) ReadPower()
    {
        if (!GetSystemPowerStatus(out var s)) throw new System.ComponentModel.Win32Exception();
        return (s.ACLineStatus, s.BatteryLifePercent);
    }

    public ulong UptimeMs() => GetTickCount64();
}

// Reads one value per sensor from HWiNFO's gadget keys. Missing key or HWiNFO not running gives null, never an error.
sealed class WindowsHwinfoRegistry : IHwinfoRegistry
{
    public string? ReadValueRaw(int index)
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(@"SOFTWARE\HWiNFO64\VSB");
            return key?.GetValue("ValueRaw" + index)?.ToString();
        }
        catch (Exception e) when (e is System.Security.SecurityException or UnauthorizedAccessException or IOException) { return null; }
    }

    public IReadOnlyDictionary<int, string> ReadLabels()
    {
        var labels = new Dictionary<int, string>();
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(@"SOFTWARE\HWiNFO64\VSB");
            for (var i = 0; key is not null && i < 200; i++) // hwinfo-scan.ps1 reads the same 200 slots
                if (key.GetValue("Label" + i) is string l) labels[i] = l;
        }
        catch (Exception e) when (e is System.Security.SecurityException or UnauthorizedAccessException or IOException) { }
        return labels;
    }
}
