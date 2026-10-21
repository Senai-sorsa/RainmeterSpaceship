using System.Runtime.InteropServices;
using ShipCore.Core;

// WASAPI loopback capture of the default speaker output, for the audio spectrum. Read-only: it never changes a device.
// Compiled but not run on hardware yet: a live capture needs the user's go (see the standalone plan, section 6).
// Only 32-bit float mix formats are read; anything else reports unavailable and the spectrum stays null.
sealed class WasapiLoopback : ISpectrumSource, IDisposable
{
    const int Bands = 16, Block = 1024;
    const uint AUDCLNT_SHAREMODE_SHARED = 0, AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000, AUDCLNT_BUFFERFLAGS_SILENT = 0x2;
    const int CLSCTX_ALL = 23, eRender = 0, eConsole = 0, WAVE_FORMAT_IEEE_FLOAT = 3, WAVE_FORMAT_EXTENSIBLE = 0xFFFE;
    static readonly Guid AudioClientIid = new("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2");
    static readonly Guid CaptureClientIid = new("C8ADBD64-E71E-48A0-A4DE-185C395CD317");
    static readonly Guid FloatSubformat = new("00000003-0000-0010-8000-00AA00389B71");

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

    [ComImport, Guid("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioClient
    {
        [PreserveSig] int Initialize(uint shareMode, uint streamFlags, long bufferDuration, long periodicity, IntPtr format, IntPtr sessionGuid);
        [PreserveSig] int GetBufferSize(out uint frames);
        [PreserveSig] int GetStreamLatency(out long latency);
        [PreserveSig] int GetCurrentPadding(out uint padding);
        [PreserveSig] int IsFormatSupported(uint shareMode, IntPtr format, out IntPtr closest);
        [PreserveSig] int GetMixFormat(out IntPtr format);
        [PreserveSig] int GetDevicePeriod(out long defaultPeriod, out long minimumPeriod);
        [PreserveSig] int Start();
        [PreserveSig] int Stop();
        [PreserveSig] int Reset();
        [PreserveSig] int SetEventHandle(IntPtr handle);
        [PreserveSig] int GetService(ref Guid iid, [MarshalAs(UnmanagedType.IUnknown)] out object service);
    }

    [ComImport, Guid("C8ADBD64-E71E-48A0-A4DE-185C395CD317"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioCaptureClient
    {
        [PreserveSig] int GetBuffer(out IntPtr data, out uint frames, out uint flags, out ulong devicePosition, out ulong qpcPosition);
        [PreserveSig] int ReleaseBuffer(uint frames);
        [PreserveSig] int GetNextPacketSize(out uint frames);
    }

    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
    class MMDeviceEnumeratorComObject { }

    private IAudioClient? _client;
    private IAudioCaptureClient? _capture;
    private Thread? _thread;
    private volatile bool _running;
    private double[]? _latest;

    /// <summary>The newest spectrum (16 bands, 0 to 1), or null before the first block or when capture is not running.</summary>
    public double[]? Latest => Volatile.Read(ref _latest);

    /// <returns>true when capture started. False when there is no output device or its format is not float: the spectrum stays null.</returns>
    public bool Start()
    {
        if (_running) return true;
        try
        {
            var enumerator = (IMMDeviceEnumerator)new MMDeviceEnumeratorComObject();
            if (enumerator.GetDefaultAudioEndpoint(eRender, eConsole, out var device) != 0) return false;
            var iid = AudioClientIid;
            if (device.Activate(ref iid, CLSCTX_ALL, IntPtr.Zero, out var obj) != 0) return false;
            _client = (IAudioClient)obj;
            if (_client.GetMixFormat(out var fmt) != 0) return false;
            try
            {
                if (!IsFloat(fmt, out var channels, out var rate)) return false;
                if (_client.Initialize(AUDCLNT_SHAREMODE_SHARED, AUDCLNT_STREAMFLAGS_LOOPBACK, 10_000_000, 0, fmt, IntPtr.Zero) != 0) return false;
                var captureId = CaptureClientIid;
                if (_client.GetService(ref captureId, out var svc) != 0) return false;
                _capture = (IAudioCaptureClient)svc;
                if (_client.Start() != 0) return false;
                _running = true;
                _thread = new Thread(() => Pump(channels, rate)) { IsBackground = true, Name = "wasapi-loopback" };
                _thread.Start();
                return true;
            }
            finally { Marshal.FreeCoTaskMem(fmt); }
        }
        catch (COMException) { Stop(); return false; }
    }

    public void Stop()
    {
        _running = false;
        _thread?.Join(500);
        _thread = null;
        if (_client is not null) _client.Stop();
        _capture = null;
        _client = null;
        Volatile.Write(ref _latest, null);
    }

    public void Dispose() => Stop();

    private void Pump(int channels, int rate)
    {
        var block = new float[Block];
        var filled = 0;
        while (_running)
        {
            Thread.Sleep(10);
            if (_capture is null || _capture.GetNextPacketSize(out var packet) != 0) continue;
            while (packet > 0 && _running)
            {
                if (_capture.GetBuffer(out var data, out var frames, out var flags, out _, out _) != 0) break;
                var silent = (flags & AUDCLNT_BUFFERFLAGS_SILENT) != 0;
                for (var f = 0; f < frames; f++)
                {
                    // Mono mix of the frame. A silent packet counts as zeros, as the device reported it.
                    var sum = 0f;
                    if (!silent)
                        for (var c = 0; c < channels; c++) sum += Marshal.PtrToStructure<float>(data + (f * channels + c) * 4);
                    block[filled++] = sum / channels;
                    if (filled == Block)
                    {
                        Volatile.Write(ref _latest, SpectrumBands.Compute(block, rate, Bands));
                        filled = 0;
                    }
                }
                _capture.ReleaseBuffer(frames);
                if (_capture.GetNextPacketSize(out packet) != 0) break;
            }
        }
    }

    /// <returns>true when the mix format is 32-bit float, with its channel count and sample rate.</returns>
    private static bool IsFloat(IntPtr fmt, out int channels, out int rate)
    {
        channels = Marshal.ReadInt16(fmt, 2);
        rate = Marshal.ReadInt32(fmt, 4);
        var tag = Marshal.ReadInt16(fmt, 0) & 0xFFFF;
        var bits = Marshal.ReadInt16(fmt, 14);
        if (tag == WAVE_FORMAT_IEEE_FLOAT) return bits == 32;
        if (tag != WAVE_FORMAT_EXTENSIBLE || bits != 32 || Marshal.ReadInt16(fmt, 16) < 22) return false;
        var sub = new byte[16];
        Marshal.Copy(fmt + 24, sub, 0, 16);
        return new Guid(sub) == FloatSubformat;
    }
}
