using System.Runtime.InteropServices;
using System.Text;
using ShipCore.Core;

// The mission clock's events, as the skin's ShipCore does it: the calendar links (DPAPI, %LOCALAPPDATA%\SpaceshipHUD\calendars.dat)
// fetched every 10 min into Data\calendar.txt, which JARVIS reads too. While the skin's ShipCore runs (Rainmeter up) it stays the only
// writer and this only reads the file. Checks once a minute, only while the HUD is shown; a message goes to the page when the file changes.
sealed class CalendarRunner(string data, Func<bool> shown, Action<string> post, Action<string> log) : IDisposable
{
    static readonly HttpClient Http = CreateHttp();
    readonly System.Windows.Forms.Timer _tick = new() { Interval = 2000 }; // 60 s once the HUD has been shown (it is not yet at Start)
    readonly string _file = Path.Combine(data, "calendar.txt");
    DateTime _fetchDue, _stamp;
    bool _fetching;

    /// <summary>The last message, for a page that just loaded.</summary>
    public string? Last { get; private set; }

    static HttpClient CreateHttp()
    {
        var h = new HttpClient { Timeout = TimeSpan.FromSeconds(30), MaxResponseContentBufferSize = 16 << 20 }; // a school calendar's ICS can be a few MB
        h.DefaultRequestHeaders.UserAgent.ParseAdd("SpaceshipHUD/1.0");
        return h;
    }

    public void Start()
    {
        _tick.Tick += (_, _) => Tick();
        _tick.Start();
    }

    async void Tick()
    {
        if (!shown()) { if (_tick.Interval < 2000) _tick.Interval = 2000; return; } // after Soon(): don't spin while hidden
        _tick.Interval = 60000;
        if (DateTime.UtcNow >= _fetchDue && !_fetching && !SkinCoreRunning())
        {
            _fetchDue = DateTime.UtcNow.AddMinutes(10); _fetching = true;
            try { await Fetch(); }
            finally { _fetching = false; }
        }
        Read();
    }

    static bool SkinCoreRunning()
    {
        if (!Mutex.TryOpenExisting("SpaceshipShipCore", out var m)) return false;
        m.Dispose();
        return true;
    }

    async Task Fetch()
    {
        var text = Unprotect(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SpaceshipHUD", "calendars.dat"));
        if (text is null) return; // no calendars set up (or not readable): leave the file as it is
        var now = DateTime.UtcNow;
        var events = new List<Ics.Event>();
        int on = 0, errors = 0;
        foreach (var src in Ics.Sources(text).Where(s => s.On))
        {
            on++;
            // the link is a secret: the log names only the label and the error kind
            if (Ics.FetchUri(src.Url) is not { } uri) { errors++; log($"CAL_BAD_LINK,{src.Label}"); continue; }
            try { events.AddRange(Ics.Parse(await Http.GetStringAsync(uri), src.Label, now.AddHours(-6), now.AddDays(21))); }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException or InvalidOperationException) { errors++; log($"CAL_FETCH_FAILED,{src.Label},{e.GetType().Name}"); }
        }
        try
        {
            var tmp = _file + ".tmp" + Environment.ProcessId;
            File.WriteAllText(tmp, Ics.Text(events, on, errors, DateTime.UtcNow), new UTF8Encoding(false));
            File.Move(tmp, _file, overwrite: true);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { log($"CAL_WRITE_FAILED,{e.GetType().Name}"); }
    }

    void Read()
    {
        try
        {
            var stamp = File.GetLastWriteTimeUtc(_file);
            if (stamp == _stamp || !File.Exists(_file)) return;
            _stamp = stamp;
            Last = System.Text.Json.JsonSerializer.Serialize(new { type = "calendar.update", text = File.ReadAllText(_file) });
            post(Last);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
    }

    // DPAPI, current user, with the skin's entropy, so the links the skin saved open here (crypt32, no extra package)
    [StructLayout(LayoutKind.Sequential)] struct Blob { public int Size; public IntPtr Data; }
    [DllImport("crypt32.dll", SetLastError = true)] static extern bool CryptUnprotectData(ref Blob input, IntPtr desc, ref Blob entropy, IntPtr reserved, IntPtr prompt, int flags, out Blob output);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr p);

    internal static string? Unprotect(string path)
    {
        byte[] enc;
        try { if (!File.Exists(path)) return null; enc = File.ReadAllBytes(path); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { return null; }
        var ent = Encoding.UTF8.GetBytes("SpaceshipHUD");
        var hEnc = GCHandle.Alloc(enc, GCHandleType.Pinned); var hEnt = GCHandle.Alloc(ent, GCHandleType.Pinned);
        try
        {
            var input = new Blob { Size = enc.Length, Data = hEnc.AddrOfPinnedObject() };
            var entropy = new Blob { Size = ent.Length, Data = hEnt.AddrOfPinnedObject() };
            if (!CryptUnprotectData(ref input, IntPtr.Zero, ref entropy, IntPtr.Zero, IntPtr.Zero, 1 /* UI_FORBIDDEN */, out var output)) return null;
            try
            {
                var bytes = new byte[output.Size];
                Marshal.Copy(output.Data, bytes, 0, output.Size);
                return Encoding.UTF8.GetString(bytes);
            }
            finally { LocalFree(output.Data); }
        }
        finally { hEnc.Free(); hEnt.Free(); }
    }

    /// <summary>location.lua right-click (Data\calendar.refresh): fetch the feeds on the next tick.</summary>
    public void Soon() { _fetchDue = DateTime.MinValue; _tick.Stop(); _tick.Interval = 1; _tick.Start(); }

    public void Dispose() { _tick.Stop(); _tick.Dispose(); }
}
