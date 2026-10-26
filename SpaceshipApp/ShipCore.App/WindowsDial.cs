using System.Diagnostics;
using System.Runtime.InteropServices;
using ShipCore.Core;

// The systems dial's writes: brightness, speaker and mic volume, power plan and refresh rate. DialGate checks every value first.
// Compiled but not run on hardware yet: a live change needs the user's go. Each write throws when Windows refuses it.
// shortcut: power modes are the built-in Windows plans, not the Lenovo modes the old Lua dial used; the plan GUIDs are the standard ones and are checked at run time.
sealed class WindowsDial : IDialActions
{
    // Fixed GUIDs, so a mode name never reaches the command line.
    static readonly Dictionary<string, string> Plans = new()
    {
        ["quiet"] = "a1841308-3541-4fab-bc81-f71556f20b4a",
        ["balance"] = "381b4222-f694-41f0-9685-ff5bb260df2e",
        ["performance"] = "8c5e7fa3-e8bf-4a06-9a0e-a1f9f9e0b0e5",
    };

    const int eRender = 0, eCapture = 1, eConsole = 0, CLSCTX_ALL = 23;
    static readonly Guid VolumeIid = new("5CDF2C82-841E-4546-9722-0CF74078229A");
    const int ENUM_CURRENT_SETTINGS = -1, DM_DISPLAYFREQUENCY = 0x400000, CDS_UPDATEREGISTRY = 1, CDS_TEST = 4;

    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceEnumerator
    {
        void EnumAudioEndpoints();
        [PreserveSig] int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice device);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDevice
    {
        [PreserveSig] int Activate(ref Guid iid, int clsctx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object iface);
    }

    // Slots in the order Windows declares them. Only SetMasterVolumeLevelScalar is called; the rest hold its place.
    [ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioEndpointVolume
    {
        [PreserveSig] int RegisterControlChangeNotify(IntPtr notify);
        [PreserveSig] int UnregisterControlChangeNotify(IntPtr notify);
        [PreserveSig] int GetChannelCount(out uint count);
        [PreserveSig] int SetMasterVolumeLevel(float dB, IntPtr context);
        [PreserveSig] int SetMasterVolumeLevelScalar(float level, IntPtr context);
    }

    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
    class MMDeviceEnumeratorComObject { }

    public void Brightness(int percent)
    {
        // WMI brightness works on built-in panels only. The script throws when there are none, so the exit code reports it.
        // shortcut: runs through powershell.exe to avoid a System.Management package; the percent is a validated int, not text.
        var script = "$ErrorActionPreference='Stop'; $m=@(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods); " +
            $"if ($m.Count -eq 0) {{ throw 'no brightness control on this display' }}; " +
            $"foreach ($x in $m) {{ Invoke-CimMethod -InputObject $x -MethodName WmiSetBrightness -Arguments @{{Timeout=1; Brightness={percent}}} | Out-Null }}";
        Run("powershell.exe", $"-NoProfile -NonInteractive -Command \"{script}\"");
    }

    public void Volume(int percent) => SetLevel(eRender, percent);

    public void Mic(int percent) => SetLevel(eCapture, percent);

    public void PowerMode(string mode)
    {
        if (!Plans.TryGetValue(mode, out var guid)) throw new ArgumentException("unknown power mode");
        Run("powercfg.exe", "/setactive " + guid);
    }

    // Starts a fixed tool and throws on a non-zero exit or after 15 s, so a failed or hung write is never reported as done.
    static void Run(string file, string args)
    {
        using var p = Process.Start(new ProcessStartInfo(file, args) { UseShellExecute = false, CreateNoWindow = true })
            ?? throw new InvalidOperationException($"{file} did not start");
        if (!p.WaitForExit(15000))
        {
            try { p.Kill(); } catch (InvalidOperationException) { } // only the child started above; it may have just exited
            throw new TimeoutException($"{file} did not finish in 15 s");
        }
        if (p.ExitCode != 0) throw new InvalidOperationException($"{file} exited {p.ExitCode}");
    }

    public void Refresh(int hz)
    {
        var dm = new DEVMODE { dmSize = (ushort)Marshal.SizeOf<DEVMODE>() };
        if (!EnumDisplaySettings(null, ENUM_CURRENT_SETTINGS, ref dm)) throw new InvalidOperationException("could not read the current display mode");
        dm.dmDisplayFrequency = (uint)hz;
        dm.dmFields |= DM_DISPLAYFREQUENCY;
        // Test first: the change is only made when the display accepts it at its current resolution.
        if (ChangeDisplaySettingsEx(null, ref dm, IntPtr.Zero, CDS_TEST, IntPtr.Zero) != 0) throw new InvalidOperationException($"display does not offer {hz} Hz");
        if (ChangeDisplaySettingsEx(null, ref dm, IntPtr.Zero, CDS_UPDATEREGISTRY, IntPtr.Zero) != 0) throw new InvalidOperationException($"display refused {hz} Hz");
    }

    static void SetLevel(int flow, int percent)
    {
        var enumerator = (IMMDeviceEnumerator)new MMDeviceEnumeratorComObject();
        var device = (IMMDevice?)null;
        object? obj = null;
        try
        {
            Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(flow, eConsole, out device));
            var iid = VolumeIid;
            Marshal.ThrowExceptionForHR(device.Activate(ref iid, CLSCTX_ALL, IntPtr.Zero, out obj));
            Marshal.ThrowExceptionForHR(((IAudioEndpointVolume)obj).SetMasterVolumeLevelScalar(percent / 100f, IntPtr.Zero));
        }
        finally
        {
            if (obj is not null) Marshal.ReleaseComObject(obj);
            if (device is not null) Marshal.ReleaseComObject(device);
            Marshal.ReleaseComObject(enumerator);
        }
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct DEVMODE
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName;
        public ushort dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
        public uint dmFields;
        public int dmPositionX, dmPositionY;
        public uint dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName;
        public ushort dmLogPixels;
        public uint dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency;
        public uint dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern bool EnumDisplaySettings(string? device, int mode, ref DEVMODE dm);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int ChangeDisplaySettingsEx(string? device, ref DEVMODE dm, IntPtr hwnd, int flags, IntPtr param);
}
