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

    [StructLayout(LayoutKind.Sequential)] struct LastInputInfo { public uint Size, Time; }
    [DllImport("user32.dll")] static extern bool GetLastInputInfo(ref LastInputInfo info);

    // DEVMODEW, 220 bytes; only the size, resolution and refresh fields are read
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct DevMode
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
        public short SpecVersion, DriverVersion, Size, DriverExtra;
        public int Fields, PositionX, PositionY, Orientation, FixedOutput;
        public short Color, Duplex, YResolution, TTOption, Collate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string FormName;
        public short LogPixels;
        public int BitsPerPel, PelsWidth, PelsHeight, DisplayFlags, DisplayFrequency, IcmMethod, IcmIntent, MediaType, DitherType, Reserved1, Reserved2, PanningWidth, PanningHeight;
    }
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern bool EnumDisplaySettings(string? device, int mode, ref DevMode dm);

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

    // the input time is a 32-bit tick count, so the difference is taken in 32 bits (it wraps every 49 days)
    public ulong? IdleMs()
    {
        var i = new LastInputInfo { Size = (uint)Marshal.SizeOf<LastInputInfo>() };
        return GetLastInputInfo(ref i) ? unchecked((uint)GetTickCount64() - i.Time) : null;
    }

    /// <summary>The primary screen's current mode, as the panel's DISP row shows it: 2560x1600 @240. Null if Windows does not say.</summary>
    public static string? Display()
    {
        var dm = new DevMode { Size = (short)Marshal.SizeOf<DevMode>() };
        if (!EnumDisplaySettings(null, -1 /* ENUM_CURRENT_SETTINGS */, ref dm) || dm.PelsWidth <= 0) return null;
        return dm.DisplayFrequency > 1 ? $"{dm.PelsWidth}x{dm.PelsHeight} @{dm.DisplayFrequency}" : $"{dm.PelsWidth}x{dm.PelsHeight}";
    }
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
