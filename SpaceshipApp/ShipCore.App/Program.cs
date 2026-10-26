using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Web.WebView2.Core;
using ShipCore.Core;

// Standalone Spaceship app: one transparent window on the desktop layer, sized to the home display (the taskbar draws over it),
// hosting a composition-mode WebView2 through DirectComposition. Ctrl+Alt+Shift+1 stops the app and everything it started.
// Never topmost, no input hooks, no injection (one out-of-context foreground WinEvent). Tray menu: Start, Stop, Diagnostics, Quit.
static class Program
{
    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();
        // A second copy would fight the first for the desktop layer and the kill chord, so it asks the first to open its control panel and exits.
        using var single = new Mutex(true, @"Local\CSpace.SingleInstance", out var first);
        using var open = new EventWaitHandle(false, EventResetMode.AutoReset, @"Local\CSpace.OpenControl");
        if (!first) { open.Set(); return; }
        var marker = new RunMarker(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Spaceship", "running.marker"));
        var lastRunUnclean = marker.LastRunEndedUncleanly();
        marker.MarkRunning(DateTimeOffset.Now);
        // The kill chord is a deliberate stop, so it clears the marker before the process goes.
        // Kill(entireProcessTree) throws on a tree holding the caller, so each child's tree goes first, then this process.
        var kill = new KillSwitch(() =>
        {
            marker.MarkCleanExit();
            foreach (var pid in ChildPids(Environment.ProcessId))
                try { using var p = Process.GetProcessById(pid); p.Kill(entireProcessTree: true); }
                catch (Exception e) when (e is ArgumentException or InvalidOperationException or System.ComponentModel.Win32Exception) { /* already gone */ }
            Process.GetCurrentProcess().Kill();
        });
        var hotkey = new HotkeyThread(() => kill.Fire());
        Application.Run(new Overlay(hotkey.Registered, marker, lastRunUnclean, open));
    }

    // Direct children of a process, from a Toolhelp snapshot (.NET has no parent-pid API).
    static List<int> ChildPids(int parent)
    {
        var list = new List<int>();
        var snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if (snap == (IntPtr)(-1)) return list;
        try
        {
            var e = new ProcessEntry32 { dwSize = (uint)Marshal.SizeOf<ProcessEntry32>() };
            for (var ok = Process32FirstW(snap, ref e); ok; ok = Process32NextW(snap, ref e))
                // only our helpers (the web view, script runners); an app the HUD opened for the user is theirs and keeps running
                if (e.th32ParentProcessID == parent && e.th32ProcessID != parent && Helpers.Contains(e.szExeFile)) list.Add((int)e.th32ProcessID);
        }
        finally { CloseHandle(snap); }
        return list;
    }

    static readonly HashSet<string> Helpers = new(StringComparer.OrdinalIgnoreCase) { "msedgewebview2.exe", "powershell.exe", "pwsh.exe", "conhost.exe", "ping.exe" };
    const uint TH32CS_SNAPPROCESS = 0x2;
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct ProcessEntry32
    {
        public uint dwSize, cntUsage, th32ProcessID; public IntPtr th32DefaultHeapID; public uint th32ModuleID, cntThreads, th32ParentProcessID; public int pcPriClassBase; public uint dwFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szExeFile;
    }
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint pid);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern bool Process32FirstW(IntPtr snap, ref ProcessEntry32 e);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern bool Process32NextW(IntPtr snap, ref ProcessEntry32 e);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
}

// The kill chord on its own thread, so it still works when the window is frozen.
sealed class HotkeyThread
{
    const uint MOD_NOREPEAT = 0x4000, WM_HOTKEY = 0x0312;
    const int ID = 1;
    readonly Action _onPress;
    readonly ManualResetEventSlim _ready = new();

    public bool Registered { get; private set; }

    public HotkeyThread(Action onPress)
    {
        _onPress = onPress;
        new Thread(Run) { IsBackground = true, Name = "kill-switch" }.Start();
        _ready.Wait(2000);
    }

    void Run()
    {
        Registered = RegisterHotKey(IntPtr.Zero, ID, KillChord.Modifiers | MOD_NOREPEAT, KillChord.Key);
        _ready.Set();
        while (GetMessage(out var msg, IntPtr.Zero, 0, 0) > 0)
            if (msg.message == WM_HOTKEY) _onPress();
    }

    [StructLayout(LayoutKind.Sequential)]
    struct MsgStruct { public IntPtr hwnd; public uint message; public IntPtr wParam, lParam; public uint time; public int x, y; }

    [DllImport("user32.dll", SetLastError = true)] static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
    [DllImport("user32.dll")] static extern int GetMessage(out MsgStruct msg, IntPtr hWnd, uint min, uint max);
}

sealed class Overlay : Form
{
    const int WS_EX_NOREDIRECTIONBITMAP = 0x00200000, WS_EX_TOOLWINDOW = 0x80, WS_EX_NOACTIVATE = 0x08000000;
    const int WS_EX_LAYERED = 0x80000, WS_EX_TRANSPARENT = 0x20, LWA_ALPHA = 0x2;
    const int WM_NCHITTEST = 0x84, HTTRANSPARENT = -1, HTCLIENT = 1;
    const int WM_MOUSEMOVE = 0x200, WM_LBUTTONDOWN = 0x201, WM_LBUTTONUP = 0x202, WM_MOUSEWHEEL = 0x20A;
    const int WM_RBUTTONDOWN = 0x204, WM_RBUTTONUP = 0x205, WM_MBUTTONDOWN = 0x207, WM_MBUTTONUP = 0x208;
    const int WM_LBUTTONDBLCLK = 0x203, WM_RBUTTONDBLCLK = 0x206, WM_MBUTTONDBLCLK = 0x209;
    const int WM_XBUTTONDOWN = 0x20B, WM_XBUTTONUP = 0x20C, WM_XBUTTONDBLCLK = 0x20D, WM_MOUSEHWHEEL = 0x20E;
    const int WM_SETTINGCHANGE = 0x1A, SPI_SETWORKAREA = 0x2F, WM_DPICHANGED = 0x2E0;
    const int WM_QUERYENDSESSION = 0x11, WM_ENDSESSION = 0x16, WM_WINDOWPOSCHANGING = 0x46, WM_DISPLAYCHANGE = 0x7E;

    [StructLayout(LayoutKind.Sequential)]
    struct WindowPos { public IntPtr hwnd, hwndInsertAfter; public int x, y, cx, cy; public uint flags; }

    // The placeholder page's one clickable box. The real page sends its own regions (hit.regions).
    static readonly Rectangle Hit = new(80, 80, 360, 220);
    Rectangle _home;

    // Where the page takes the mouse. Outside it the window carries WS_EX_TRANSPARENT, so clicks reach the desktop icons and
    // apps under it (HTTRANSPARENT alone only passes them to windows of this thread). The cursor is polled, as Rainmeter does.
    readonly HitRegions _hits = new();
    readonly System.Windows.Forms.Timer _cursor = new() { Interval = 33 };
    bool _passThrough = true;

    CoreWebView2Environment? _env;
    CoreWebView2CompositionController? _cc;
    IntPtr _dcompDevice, _dcompTarget, _dcompVisual;
    readonly NotifyIcon _tray = new();
    readonly System.Windows.Forms.Timer _perf = new() { Interval = 5000 };
    readonly Process _self = Process.GetCurrentProcess();
    TimeSpan _lastCpu; DateTime _lastWall = DateTime.UtcNow;
    readonly Dictionary<int, TimeSpan> _webCpu = new(); // last CPU time per msedgewebview2 pid, for the delta
    double _fps;
    bool _running, _starting; // _running = the user asked for it; _starting = a web view is being created
    int _failures; // web view restarts since the last good page load
    const int MaxRestarts = 3;
    StreamWriter? _log;
    const long MaxLogBytes = 8 << 20; // about a week of 5 s rows (old logs expire after 7 days); the sampler stops past it
    string _lastSample = "no sample yet", _lastReason = "not decided yet";
    readonly int _uiThread = Environment.CurrentManagedThreadId;

    // Core logic. Null router = no skin folder or contract found: the page gets no settings and nothing is written.
    readonly MessageRouter? _router;
    SettingsStore? _settings;
    IReadOnlyList<string> _hwKeys = Array.Empty<string>();
    // The loopback runs while the HUD is shown and Off_BottomAudio is not 1 (AudioCapture); otherwise no audio device is opened.
    readonly WasapiLoopback _loopback = new();
    long _audioRetryAt, _audioCheckAt;
    readonly WindowsGpuCounters _gpu = new();
    readonly SystemSampler _sampler;
    readonly System.Windows.Forms.Timer _metricsTimer = new() { Interval = 1000 };
    long _metricsSeq;
    readonly VisibilityPolicy _policy;
    readonly Win32Snapshots _snapshots;
    readonly System.Windows.Forms.Timer _visibility = new() { Interval = 3000 };
    // Out-of-context WinEvent: Windows posts the event to this thread's message loop; nothing is loaded into other processes.
    delegate void WinEventProc(IntPtr hook, uint ev, IntPtr hwnd, int obj, int child, uint thread, uint time);
    const uint EVENT_SYSTEM_FOREGROUND = 3, WINEVENT_OUTOFCONTEXT = 0;
    readonly WinEventProc _onForeground; // kept in a field so the collector does not free it while Windows still calls it
    readonly IntPtr _foregroundHook;
    // Locked (Win+L, the lock screen) hides the HUD, which also pauses every timer that checks Visible.
    readonly Microsoft.Win32.SessionSwitchEventHandler _onSession;
    bool _locked;
    uint _browserPid;
    readonly AutoStart _autostart = new(new RunKeyStore());
    readonly Lifecycle _life;
    readonly RunMarker _marker;
    readonly JarvisPipe _jarvis = new(new SystemClock());
    // JARVIS state reaches the page from Data\jarvis.txt, read-only, as the skin reads it; the pipe carries nothing yet.
    readonly System.Windows.Forms.Timer _jarvisTimer = new() { Interval = 200 };
    string? _jarvisFile;
    string? _jarvisSent, _jarvisText;
    DateTime _jarvisWrite;
    readonly StatusRunner? _status;
    readonly NetRunner _net;
    readonly TodoRunner _todo;

    RegisteredWaitHandle? _openWait;
    readonly string? _resources;

    public Overlay(bool hotkeyRegistered, RunMarker marker, bool lastRunUnclean, EventWaitHandle openControl)
    {
        _marker = marker;
        _sampler = new(new WindowsMetrics(), new WindowsHwinfoRegistry(), new WindowsNetwork(), _loopback, new WindowsProcessNames(), _gpu);
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        Text = "CSpace";
        TopMost = false; // never above other apps (exam browsers, games)

        var schemaPath = FindUp(Path.Combine("contract", "config-keys.json"));
        var resources = _resources = FindUp(Path.Combine("Skins", "Spaceship", "@Resources"));
        if (resources is not null) _jarvisFile = Path.Combine(resources, "Data", "jarvis.txt");
        if (resources is not null) _status = new StatusRunner(Path.Combine(resources, "Scripts"), () => Visible, Post, m => _log?.WriteLine($"{DateTime.UtcNow:O},{m}"));
        _net = new NetRunner(() => _settings?.Get(["PingHost"]).GetValueOrDefault("PingHost"), () => Visible, () => _settings?.Get(["IpMask"]).GetValueOrDefault("IpMask") == "0", Post);
        _todo = new TodoRunner(() =>
        {
            var v = _settings?.Get(["ObsidianTodo", "ReticleTodo"]);
            return (v?.GetValueOrDefault("ObsidianTodo"), v?.GetValueOrDefault("ReticleTodo") != "0");
        }, () => Visible, Post);
        if (schemaPath is not null)
        {
            var schema = ConfigSchema.Parse(File.ReadAllText(schemaPath));
            var appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Spaceship");
            var settingsPath = Path.Combine(appData, "settings.json");
            _settings = new SettingsStore(settingsPath, schema);
            _hwKeys = schema.Keys.Keys.Where(k => k.StartsWith("HW_", StringComparison.Ordinal)).Append("Off_BottomAudio").ToList();
            // The skin's values (Settings.inc, State.inc, Offsets.inc) fill every key the app has no value for yet, on each start,
            // so keys added later (State.inc's Off_ flags) arrive too; a value already in settings.json always wins. Dry run: SkinImport.Build.
            if (resources is not null)
                _settings.Import(SkinImport.Build(new ConfigStore(resources, schema), schema).Values);
            // Shortcut: power actions and flows are not wired (the schema lists no power action, and flows need P-F). The gate refuses by throwing, which is logged.
            var unwired = new UnwiredHost();
            var state = new HostState(Path.Combine(appData, "ui-state.json"));
            _router = new MessageRouter(schema, _settings, new ActionGate(unwired, unwired), ConfirmAsync, state, new DialGate(new WindowsDial(), ConfirmAsync), _hits);
        }
        // The full display, taskbar included: the desktop layer lets the taskbar draw over it.
        _home = HomeScreen(_settings).Bounds;
        Bounds = _home;
        var examPath = FindUp(Path.Combine("contract", "exam-browsers.json"));
        _policy = new VisibilityPolicy(examPath is null ? Array.Empty<string>() : ExamBrowserList.ProcessNames(File.ReadAllText(examPath)));
        _snapshots = new Win32Snapshots(() => _home, () => _browserPid);
        _life = new Lifecycle(Stop, () => Restart(false));

        var menu = new ContextMenuStrip();
        // the Control Center lives in the page; the tray (or a double-click on the icon) asks the page to open it
        void OpenControl() { if (_running) Post("{\"type\":\"control.open\"}"); }
        menu.Items.Add("Control panel", null, (_, _) => OpenControl());
        _tray.DoubleClick += (_, _) => OpenControl();
        // a second launch signals this event (pool thread); the panel opens on the UI thread
        _openWait = ThreadPool.RegisterWaitForSingleObject(openControl, (_, _) => { if (IsHandleCreated) BeginInvoke(() => { if (!_running) Start(); OpenControl(); }); }, null, -1, false);
        menu.Items.Add("Start", null, (_, _) => Start());
        menu.Items.Add("Stop", null, (_, _) => Stop());
        // Rainmeter's Refresh: a fresh page with the restart budget reset
        menu.Items.Add("Reload HUD", null, (_, _) => { _failures = 0; _appsJson = null; ReleaseWebView(); Start(); });
        // Autostart is deferred by the user: the menu can only remove a Run entry an earlier build wrote, never add one.
        if (_autostart.IsEnabled)
        {
            var auto = new ToolStripMenuItem("Stop starting with Windows");
            auto.Click += (_, _) => { _autostart.Disable(); menu.Items.Remove(auto); };
            menu.Items.Add(auto);
        }
        menu.Items.Add("Diagnostics", null, (_, _) => MessageBox.Show(
            $"Shown: {Visible}, locked: {_locked}\nLast visibility reason: {_lastReason}\n\n" +
            $"Last sample (cpu % of one core, MB, js fps, web cpu %, web MB, web private MB, web processes):\n{_lastSample}\n\n" +
            $"Logs: {Path.Combine(Path.GetTempPath(), "spaceship-app")}",
            "CSpace diagnostics", MessageBoxButtons.OK, MessageBoxIcon.Information));
        menu.Items.Add("Open log folder", null, (_, _) => Process.Start("explorer.exe", Path.Combine(Path.GetTempPath(), "spaceship-app"))?.Dispose());
        menu.Items.Add("Quit", null, (_, _) => Quit());
        _tray.Icon = AppIcon(); _tray.Text = "CSpace"; _tray.ContextMenuStrip = menu; _tray.Visible = true;
        if (!hotkeyRegistered) _tray.ShowBalloonTip(5000, "Spaceship", $"{KillChord.Label} is taken by another app, so the kill switch is off.", ToolTipIcon.Warning);
        if (lastRunUnclean) _tray.ShowBalloonTip(5000, "Spaceship", "The last run did not exit cleanly. Its log is in the temp folder under spaceship-app.", ToolTipIcon.Warning);
        _visibility.Tick += (_, _) => ApplyVisibility();
        _visibility.Start();
        // A new foreground app (a game, an exam browser) is checked at once; the 3 s poll stays for fullscreen toggles inside one app.
        _onForeground = (_, _, _, _, _, _, _) => ApplyVisibility();
        _foregroundHook = SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, IntPtr.Zero, _onForeground, 0, 0, WINEVENT_OUTOFCONTEXT);
        // SessionSwitch arrives on the SystemEvents thread; the flag and the window are changed on this one.
        _onSession = (_, e) =>
        {
            var locked = e.Reason switch { Microsoft.Win32.SessionSwitchReason.SessionLock => true, Microsoft.Win32.SessionSwitchReason.SessionUnlock => false, _ => (bool?)null };
            if (locked is bool l && IsHandleCreated) BeginInvoke(() => { _locked = l; ApplyVisibility(); });
        };
        Microsoft.Win32.SystemEvents.SessionSwitch += _onSession;

        var dir = Path.Combine(Path.GetTempPath(), "spaceship-app");
        Directory.CreateDirectory(dir);
        var old = new DirectoryInfo(dir).GetFiles("perf-*.csv").Select(f => (f.FullName, f.LastWriteTime));
        foreach (var path in HostRules.ExpiredLogs(old, DateTime.Now, TimeSpan.FromDays(7))) File.Delete(path);
        _log = new StreamWriter(Path.Combine(dir, $"perf-{DateTime.Now:yyyyMMdd-HHmmss}.csv")) { AutoFlush = true };
        _log.WriteLine("utc,cpu_percent_of_one_core,working_set_mb,js_fps,web_cpu_percent_of_one_core,web_working_set_mb,web_private_mb,web_processes");
        _lastCpu = _self.TotalProcessorTime;
        _perf.Tick += (_, _) => Sample();
        _perf.Start();
        _metricsTimer.Tick += (_, _) => PushMetrics();
        _metricsTimer.Start();
        _cursor.Tick += (_, _) => FollowCursor();
        _cursor.Start();
        _jarvis.Start();
        _jarvisTimer.Tick += (_, _) => PushJarvis();
        _jarvisTimer.Start();
        _status?.Start();
        _net.Start();
        _todo.Start();
    }

    protected override CreateParams CreateParams
    {
        get
        {
            var p = base.CreateParams;
            p.ExStyle |= WS_EX_NOREDIRECTIONBITMAP | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED;
            if (_passThrough) p.ExStyle |= WS_EX_TRANSPARENT;
            return p;
        }
    }
    protected override bool ShowWithoutActivation => true;

    // Hidden (fullscreen app, exam browser, lock): the page stops rendering and its timers sleep; WebView2 wakes it when shown.
    protected override void OnVisibleChanged(EventArgs e)
    {
        base.OnVisibleChanged(e);
        // the per-frame timers do nothing while hidden, so they don't wake the CPU then (30 + 5 + 1 wakeups a second)
        _cursor.Enabled = _jarvisTimer.Enabled = _metricsTimer.Enabled = Visible && _running && !_covered;
        if (_covered) _loopback.Stop();
        if (_cc is null || !_running) return;
        _cc.IsVisible = Visible;
        if (!Visible) { Suspend(_cc); _loopback.Stop(); }
    }

    static async void Suspend(CoreWebView2CompositionController cc)
    {
        try { await cc.CoreWebView2.TrySuspendAsync(); }
        catch (Exception e) when (e is COMException or InvalidOperationException or ObjectDisposedException) { /* best effort, like a sleeping tab */ }
    }

    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        // Layered only so WS_EX_TRANSPARENT passes clicks to other apps; fully opaque, the page's own alpha still shows the desktop.
        // shortcut: unverified with WS_EX_NOREDIRECTIONBITMAP; if the first live run shows nothing, drop WS_EX_LAYERED and this call.
        SetLayeredWindowAttributes(Handle, 0, 255, LWA_ALPHA);
        AttachToDesktopLayer();
        Start();
    }

    // Takes the mouse only while the cursor is over a region; UpdateStyles re-reads CreateParams without a z-order move.
    void FollowCursor()
    {
        if (!Visible) return;
        var p = PointToClient(Cursor.Position);
        var through = !_hits.Contains(p.X, p.Y);
        if (through == _passThrough) return;
        _passThrough = through;
        if (through) _cc?.SendMouseInput(CoreWebView2MouseEventKind.Leave, CoreWebView2MouseEventVirtualKeys.None, 0, Point.Empty); // clear hover
        UpdateStyles();
    }

    // Desktop layer the way Rainmeter's "On Desktop" does it: a top-level window at the bottom of the z-order, above the
    // shell's desktop (which Windows keeps lowest) and its icons, below every normal window and the taskbar.
    // Not a WorkerW child: that sits under the icon view, which then takes every click, and 24H2 changed that tree.
    // shortcut: Show Desktop (Win+D) covers the HUD; Rainmeter lifts its skins under the topmost windows then. Add it if wanted.
    void AttachToDesktopLayer() => SetWindowPos(Handle, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE);

    const uint SWP_NOSIZE = 0x0001, SWP_NOMOVE = 0x0002, SWP_NOZORDER = 0x0004, SWP_NOACTIVATE = 0x0010;
    static readonly IntPtr HWND_BOTTOM = 1;

    // The display whose size matches HomeSize in settings.json (2560x1600 by default); the primary display if none does.
    static Screen HomeScreen(SettingsStore? settings)
    {
        var screens = Screen.AllScreens;
        var text = settings?.Get(new[] { "HomeSize" }).GetValueOrDefault("HomeSize") ?? "";
        var index = HostRules.PickHomeDisplay(screens.Select(s => (s.Bounds.Width, s.Bounds.Height)).ToList(), HostRules.ParseSize(text, (2560, 1600)));
        return index >= 0 ? screens[index] : Screen.PrimaryScreen!;
    }

    // The icon baked into the exe (Assets/cspace.ico); the generic one if it cannot be read.
    static Icon AppIcon()
    {
        try { return Environment.ProcessPath is { } p && Icon.ExtractAssociatedIcon(p) is { } i ? i : SystemIcons.Application; }
        catch { return SystemIcons.Application; }
    }

    void Fail(Exception ex) { MessageBox.Show($"Spaceship error: {ex.Message}\nthread {Environment.CurrentManagedThreadId}, ui {_uiThread}\n{ex}"); Quit(); }

    void Start()
    {
        _running = true;
        if (_cc is not null || _starting) { Show(); return; }
        _starting = true;
        StartWebView();
    }

    async void StartWebView()
    {
        try
        {
            _env ??= await CoreWebView2Environment.CreateAsync(null, Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Spaceship", "wv2")); // not %TEMP%: disk cleanup must not wipe a live profile
            var cc = await _env.CreateCoreWebView2CompositionControllerAsync(Handle);
            // WebView2 members may only be touched on the UI thread; an await can resume on a pool thread.
            if (InvokeRequired) BeginInvoke(new Action(() => { try { AttachOnUi(cc); } catch (Exception ex) { Fail(ex); } }));
            else AttachOnUi(cc);
        }
        catch (Exception ex) { Fail(ex); }
    }

    void AttachOnUi(CoreWebView2CompositionController cc)
    {
        _starting = false;
        if (!_running) { try { cc.Close(); } catch { /* stopped while starting */ } return; }
        _cc = cc;
        Show();
        _cc.Bounds = new Rectangle(0, 0, ClientSize.Width, ClientSize.Height);
        _cc.DefaultBackgroundColor = Color.Transparent;
        _cc.IsVisible = true;
        var s = _cc.CoreWebView2.Settings;
        s.AreDefaultContextMenusEnabled = false; // right click belongs to the HUD (Top steps back)
        // An app, not a browser: no host objects (postMessage only), no browser keys (reload, find, print, zoom), dialogs,
        // status bar, zoom or autofill (MS Learn, "Develop secure WebView2 apps").
        s.AreHostObjectsAllowed = false;
        s.AreBrowserAcceleratorKeysEnabled = false;
        s.AreDefaultScriptDialogsEnabled = false;
        s.IsStatusBarEnabled = false;
        s.IsZoomControlEnabled = false;
        s.IsGeneralAutofillEnabled = false;
        s.IsPasswordAutosaveEnabled = false;
#if !DEBUG
        s.AreDevToolsEnabled = false;
#endif
        _cc.CoreWebView2.PermissionRequested += (_, a) => a.State = CoreWebView2PermissionState.Deny; // no mic, camera, location, clipboard read
        _cc.CoreWebView2.DownloadStarting += (_, a) => a.Cancel = true;

        // DirectComposition: a visual tree rooted on this window; WebView2 renders into _dcompVisual.
        Check(DCompositionCreateDevice(IntPtr.Zero, ref IID_IDCompositionDevice, out _dcompDevice), "DCompositionCreateDevice");
        Check(Vcall<CreateTargetForHwnd>(_dcompDevice, 6)(_dcompDevice, Handle, true, out _dcompTarget), "CreateTargetForHwnd");
        Check(Vcall<CreateVisual>(_dcompDevice, 7)(_dcompDevice, out _dcompVisual), "CreateVisual");
        Check(Vcall<SetRoot>(_dcompTarget, 3)(_dcompTarget, _dcompVisual), "SetRoot");
        _cc.RootVisualTarget = Marshal.GetObjectForIUnknown(_dcompVisual); // the wrapper needs a COM object, not a raw pointer
        Check(Vcall<Commit>(_dcompDevice, 3)(_dcompDevice), "Commit");

        // the page's cursor (hand over buttons, text bar in fields); the handle belongs to WebView2, so it is not disposed here
        _cc.CursorChanged += (_, _) => { try { Cursor = new Cursor(_cc.Cursor); } catch (Exception e) when (e is COMException or ArgumentException or InvalidOperationException) { Cursor = Cursors.Default; } };
        _cc.CoreWebView2.WebMessageReceived += (_, a) => OnWebMessage(a);
        _cc.CoreWebView2.ProcessFailed += (_, a) => OnProcessFailed(a);
        // The page is the only thing this view may show: no links, no redirects, no popups.
        _cc.CoreWebView2.NavigationStarting += (_, a) => a.Cancel = a.Uri != "about:blank" && !a.Uri.StartsWith(UiOrigin, StringComparison.Ordinal);
        _cc.CoreWebView2.NewWindowRequested += (_, a) => a.Handled = true;
        _cc.CoreWebView2.NavigationCompleted += (_, a) => { if (a.IsSuccess) _failures = 0; _jarvisSent = null; foreach (var m in _status?.Last ?? []) Post(m); foreach (var m in _net.Last) Post(m); if (_todo.Last is { } t) Post(t); if (_covered) Post("{\"type\":\"host.occluded\",\"on\":true}"); PostOnce(); }; // a new page gets the JARVIS and status state again
        var ui = FindUp(Path.Combine("SpaceshipApp", "SpaceshipUI", "dist"));
        if (ui is null)
        {
            _log?.WriteLine($"{DateTime.UtcNow:O},UI_MISSING,placeholder page");
            _hits.Set(new[] { (Hit.X, Hit.Y, Hit.Width, Hit.Height) }, false);
            _cc.CoreWebView2.NavigateToString(PageHtml());
        }
        else
        {
            // The built UI, served from its folder under a fixed name; only that origin may load.
            _cc.CoreWebView2.SetVirtualHostNameToFolderMapping(UiHost, ui, CoreWebView2HostResourceAccessKind.DenyCors);
            _cc.CoreWebView2.Navigate(UiOrigin + "index.html?module=all"); // the full HUD; the page still accepts one name or a list
        }
    }

    const string UiHost = "spaceship.local";
    const string UiOrigin = "https://spaceship.local/";

    // A number is the page's frame rate; anything else is a message for MessageRouter (which checks it first).
    async void OnWebMessage(CoreWebView2WebMessageReceivedEventArgs a)
    {
        try
        {
            if (a.Source != "about:blank" && !a.Source.StartsWith(UiOrigin, StringComparison.Ordinal)) return; // only the app's own page (or the placeholder) may talk to the host
            var text = a.TryGetWebMessageAsString();
            if (double.TryParse(text, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f)) { _fps = f; return; }
            if (_router is null) return;
            var r = await _router.HandleAsync(text);
            if (r.Problem is not null) _log?.WriteLine($"{DateTime.UtcNow:O},REFUSED,{r.Problem}");
            if (r.Reply is not null) _cc?.CoreWebView2.PostWebMessageAsJson(r.Reply);
        }
        catch (Exception e) { _log?.WriteLine($"{DateTime.UtcNow:O},MESSAGE_ERROR,{e.GetType().Name}"); }
    }

    // Renderer exit or hang: reload. Browser exit: a fresh environment. GPU exit: WebView2 starts a new GPU process itself, so only log it.
    void OnProcessFailed(CoreWebView2ProcessFailedEventArgs a)
    {
        _log?.WriteLine($"{DateTime.UtcNow:O},PROCESS_FAILED,{a.ProcessFailedKind}");
        switch (a.ProcessFailedKind)
        {
            // Deferred: the web view cannot be closed from inside its own event.
            case CoreWebView2ProcessFailedKind.RenderProcessExited:
            case CoreWebView2ProcessFailedKind.RenderProcessUnresponsive: BeginInvoke(new Action(() => Restart(false))); break;
            case CoreWebView2ProcessFailedKind.BrowserProcessExited: BeginInvoke(new Action(() => Restart(true))); break;
        }
    }

    void Restart(bool freshEnvironment)
    {
        if (!_running) return;
        if (++_failures > MaxRestarts)
        {
            _log?.WriteLine($"{DateTime.UtcNow:O},GIVING_UP,{_failures}"); Stop();
            _tray.ShowBalloonTip(8000, "CSpace", "The HUD kept crashing, so it is stopped. Use Reload HUD in the tray to try again.", ToolTipIcon.Error);
            return;
        }
        ReleaseWebView();
        if (freshEnvironment) _env = null;
        Start();
    }

    // Shows the window only while the policy allows it; a fullscreen app or an exam browser sends it away.
    void ApplyVisibility()
    {
        if (!_running || _cc is null) return;
        ClickThroughWebViewShadow();
        var snap = _snapshots.Take();
        var decision = _policy.Decide(snap);
        _lastReason = decision.Reason;
        var covered = decision.Visibility == Visibility.Covered;
        var show = (decision.Visibility == Visibility.Show || covered) && !_locked;
        if (show != Visible) _log?.WriteLine($"{DateTime.UtcNow:O},{(show ? "SHOW" : "HIDE")},{decision.Reason}{(_locked ? " (locked)" : "")} [{snap.Foreground?.ClassName}/{snap.Foreground?.Process}]");
        if (show) { if (!Visible) Show(); }
        else if (Visible) Hide();
        if (covered != _covered)
        {
            _covered = covered;
            _log?.WriteLine($"{DateTime.UtcNow:O},{(covered ? "COVERED" : "UNCOVERED")},[{snap.Foreground?.ClassName}/{snap.Foreground?.Process}]");
            Post($"{{\"type\":\"host.occluded\",\"on\":{(covered ? "true" : "false")}}}");
            OnVisibleChanged(EventArgs.Empty); // re-gate the timers
        }
    }
    bool _covered; // a fullscreen window is in front: shown, but nothing is sampled or animated

    // WebView2 bug (WebView2Feedback #5668, open): with visual hosting the browser process keeps an alpha-0 layered top-level
    // window the size of ours right above it, and it still hit-tests, so it swallows every click meant for the HUD and the
    // desktop icons. Input reaches the page only through our window (SendMouseInput), so that window is made click-through.
    // Re-checked on the visibility tick because a restarted browser process makes a new one.
    void ClickThroughWebViewShadow()
    {
        uint browser;
        try { browser = _cc!.CoreWebView2.BrowserProcessId; }
        catch (Exception e) when (e is COMException or InvalidOperationException or ObjectDisposedException) { return; }
        _browserPid = browser; // clicking the HUD can make that window the foreground one; it is ours, not a fullscreen app
        EnumWindows((h, lp) =>
        {
            GetWindowThreadProcessId(h, out var pid);
            if (pid != browser) return true;
            var ex = GetWindowLong(h, GWL_EXSTYLE);
            // only the invisible one: alpha 0 and not yet click-through
            if ((ex & WS_EX_LAYERED) != 0 && (ex & WS_EX_TRANSPARENT) == 0 && GetLayeredWindowAttributes(h, out _, out var alpha, out var how) && (how & LWA_ALPHA) != 0 && alpha == 0)
                SetWindowLong(h, GWL_EXSTYLE, ex | WS_EX_TRANSPARENT);
            return true;
        }, IntPtr.Zero);
    }

    // One system.metrics frame per second, only while the window is shown; a failed read is logged and skipped.
    void PushMetrics()
    {
        if (_cc?.CoreWebView2 is null || !Visible) return;
        try
        {
            var settings = _settings?.Get(_hwKeys) ?? new Dictionary<string, string>();
            AudioCapture(settings.GetValueOrDefault("Off_BottomAudio") != "1");
            _cc.CoreWebView2.PostWebMessageAsJson(SystemSampler.ToJson(_sampler.Sample(settings, ++_metricsSeq)));
        }
        catch (Exception e) { _log?.WriteLine($"{DateTime.UtcNow:O},METRICS_FAILED,{e.GetType().Name}"); }
    }

    // The loopback runs only while the HUD is shown (OnVisibleChanged stops it) and the bottom audio is on.
    // A device that refuses, or a capture that ended on a lost device, is tried again after 30 s.
    // shortcut: a new default speaker is noticed by a 5 s poll, upgrade with IMMNotificationClient if 5 s is too slow
    void AudioCapture(bool want)
    {
        if (!want) { _loopback.Stop(); return; }
        var now = Environment.TickCount64;
        if (now >= _audioCheckAt) { _audioCheckAt = now + 5_000; if (_loopback.DefaultChanged()) _loopback.Stop(); }
        if (now < _audioRetryAt) return;
        if (!_loopback.Start()) _audioRetryAt = now + 30_000;
    }

    // Sends jarvis.update when it changes (a state, the level, or going stale). The file is opened so JARVIS can still replace it.
    void PushJarvis()
    {
        if (_cc?.CoreWebView2 is null || !Visible || _jarvisFile is null) return;
        // Re-read only when the file changed; a missing file reads as 1601 without throwing.
        var w = File.GetLastWriteTimeUtc(_jarvisFile);
        if (w != _jarvisWrite)
        {
            _jarvisWrite = w; _jarvisText = null;
            if (w.Year > 1601) try
            {
                using var f = new FileStream(_jarvisFile, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
                if (f.Length <= 16384) _jarvisText = new StreamReader(f).ReadToEnd();
            }
            catch (IOException) { _jarvisWrite = default; } // missing, or mid-replace: retry next tick
            catch (UnauthorizedAccessException) { _jarvisWrite = default; }
        }
        var json = JarvisStatus.ToJson(_jarvisText, DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        if (json == _jarvisSent) return;
        _jarvisSent = json;
        _cc.CoreWebView2.PostWebMessageAsJson(json);
    }

    void Post(string json) => _cc?.CoreWebView2?.PostWebMessageAsJson(json);

    // Data a new page gets once: the app catalog (Apps.ini, the Start-menu list, which file targets exist). Read on the
    // first page load and kept; Reload HUD reads it again, like Rainmeter's Refresh.
    string? _appsJson;
    void PostOnce()
    {
        if (_resources is null) return;
        try
        {
            _appsJson ??= AppsFeed.ToJson(File.ReadAllText(Path.Combine(_resources, "Apps.ini")),
                File.Exists(Path.Combine(_resources, "Data", "StartApps.txt")) ? File.ReadAllText(Path.Combine(_resources, "Data", "StartApps.txt")) : "",
                File.Exists, Environment.ExpandEnvironmentVariables);
            Post(_appsJson);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { _log?.WriteLine($"{DateTime.UtcNow:O},APPS_UNREADABLE,{e.GetType().Name}"); }
    }

    // Power and flow actions need a person to say yes; the schema lists none of them, so this is only reached through the gate.
    // Owned by a hidden topmost form, not the HUD: the HUD is held at the bottom of the z-order, so its dialog could open behind other windows.
    Task<bool> ConfirmAsync(string id)
    {
        using var top = new Form { TopMost = true, ShowInTaskbar = false };
        return Task.FromResult(MessageBox.Show(top, $"Allow the {id} action?", "CSpace", MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button2) == DialogResult.Yes);
    }

    static string? FindUp(string relative)
    {
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); d is not null; d = d.Parent)
        {
            var p = Path.Combine(d.FullName, relative);
            if (File.Exists(p) || Directory.Exists(p)) return p;
        }
        return null;
    }

    // The page and the hit test share one rectangle, so the two cannot drift apart.
    static string PageHtml() => Page
        .Replace("__HX__", Hit.X.ToString()).Replace("__HY__", Hit.Y.ToString())
        .Replace("__HW__", Hit.Width.ToString()).Replace("__HH__", Hit.Height.ToString());

    // Stop: hide and release the web view. Start brings it back.
    void Stop()
    {
        _running = false;
        Hide();
        ReleaseWebView();
    }

    void ReleaseWebView()
    {
        try { _cc?.Close(); } catch { /* already closing */ }
        _cc = null;
        foreach (var p in new[] { _dcompVisual, _dcompTarget, _dcompDevice }) if (p != IntPtr.Zero) Marshal.Release(p);
        _dcompVisual = _dcompTarget = _dcompDevice = IntPtr.Zero;
    }

    void Quit()
    {
        TearDown();
        Application.Exit();
    }

    bool _tornDown;
    void TearDown()
    {
        if (_tornDown) return;
        _tornDown = true;
        _life.Teardown(); // runs Stop once, whichever of quit or sign-out gets here first
        _marker.MarkCleanExit();
        _openWait?.Unregister(null);
        if (_foregroundHook != IntPtr.Zero) UnhookWinEvent(_foregroundHook);
        Microsoft.Win32.SystemEvents.SessionSwitch -= _onSession; // a static event: left attached it would keep this form alive
        _visibility.Stop(); _perf.Stop(); _metricsTimer.Stop(); _jarvisTimer.Stop(); _status?.Dispose(); _net.Dispose(); _todo.Dispose(); _cursor.Stop(); _loopback.Dispose(); _gpu.Dispose(); _tray.Dispose(); _log?.Dispose(); _log = null; _jarvis.Dispose();
    }

    // A WM_CLOSE from outside (a task manager's "End task") ends the run cleanly: marker cleared, no ghost tray icon.
    protected override void OnFormClosed(FormClosedEventArgs e) { TearDown(); base.OnFormClosed(e); }

    // Resolution or display set changed: pick the home display again and fill it.
    void Rehome()
    {
        _home = HomeScreen(_settings).Bounds;
        Bounds = _home;
        if (_cc is not null) _cc.Bounds = new Rectangle(0, 0, ClientSize.Width, ClientSize.Height);
    }

    protected override void WndProc(ref Message m)
    {
        switch (m.Msg)
        {
            case WM_QUERYENDSESSION: m.Result = _life.OnQueryEndSession() ? (IntPtr)1 : IntPtr.Zero; return; // never block sign-out
            case WM_ENDSESSION: _life.OnEndSession(m.WParam != IntPtr.Zero); if (m.WParam != IntPtr.Zero) Quit(); m.Result = IntPtr.Zero; return;
            case WM_DISPLAYCHANGE: case WM_DPICHANGED: BeginInvoke(new Action(Rehome)); break; // after Windows finishes moving the screens
            case WM_SETTINGCHANGE when m.WParam == (IntPtr)SPI_SETWORKAREA: BeginInvoke(new Action(Rehome)); break; // taskbar moved or resized
            case WM_WINDOWPOSCHANGING:
            {
                // Any z-order move (a click, Show) is turned into "stay at the bottom", so the HUD never covers an app.
                var pos = Marshal.PtrToStructure<WindowPos>(m.LParam);
                if ((pos.flags & SWP_NOZORDER) == 0) { pos.hwndInsertAfter = HWND_BOTTOM; Marshal.StructureToPtr(pos, m.LParam, false); }
                break;
            }
            case WM_NCHITTEST:
            {
                var p = PointToClient(new Point((short)(m.LParam.ToInt64() & 0xFFFF), (short)((m.LParam.ToInt64() >> 16) & 0xFFFF)));
                m.Result = (IntPtr)(_hits.Contains(p.X, p.Y) ? HTCLIENT : HTTRANSPARENT); // between two cursor polls
                return;
            }
            case WM_LBUTTONDOWN:
                // The page is showing something to type into: take the keyboard (the window never activates by itself).
                if (_hits.Keyboard && _cc is not null) { SetForegroundWindow(Handle); _cc.MoveFocus(CoreWebView2MoveFocusReason.Programmatic); }
                ForwardMouse(m); return;
            case WM_MOUSEMOVE: case WM_LBUTTONUP: case WM_MOUSEWHEEL: case WM_MOUSEHWHEEL:
            case WM_RBUTTONDOWN: case WM_RBUTTONUP: case WM_MBUTTONDOWN: case WM_MBUTTONUP:
            case WM_LBUTTONDBLCLK: case WM_RBUTTONDBLCLK: case WM_MBUTTONDBLCLK:
            case WM_XBUTTONDOWN: case WM_XBUTTONUP: case WM_XBUTTONDBLCLK:
                ForwardMouse(m);
                if (m.Msg is WM_XBUTTONDOWN or WM_XBUTTONUP or WM_XBUTTONDBLCLK) m.Result = (IntPtr)1; // X buttons say they were handled
                return;
        }
        base.WndProc(ref m);
    }

    void ForwardMouse(Message m)
    {
        if (_cc is null) return;
        var lp = m.LParam.ToInt64();
        var pt = new Point((short)(lp & 0xFFFF), (short)((lp >> 16) & 0xFFFF));
        var wheel = m.Msg is WM_MOUSEWHEEL or WM_MOUSEHWHEEL;
        if (wheel) pt = PointToClient(pt); // wheel coordinates are screen-relative
        var kind = m.Msg switch
        {
            WM_MOUSEMOVE => CoreWebView2MouseEventKind.Move,
            WM_LBUTTONDOWN => CoreWebView2MouseEventKind.LeftButtonDown,
            WM_LBUTTONUP => CoreWebView2MouseEventKind.LeftButtonUp,
            WM_LBUTTONDBLCLK => CoreWebView2MouseEventKind.LeftButtonDoubleClick,
            WM_RBUTTONDOWN => CoreWebView2MouseEventKind.RightButtonDown,
            WM_RBUTTONUP => CoreWebView2MouseEventKind.RightButtonUp,
            WM_RBUTTONDBLCLK => CoreWebView2MouseEventKind.RightButtonDoubleClick,
            WM_MBUTTONDOWN => CoreWebView2MouseEventKind.MiddleButtonDown,
            WM_MBUTTONUP => CoreWebView2MouseEventKind.MiddleButtonUp,
            WM_MBUTTONDBLCLK => CoreWebView2MouseEventKind.MiddleButtonDoubleClick,
            WM_XBUTTONDOWN => CoreWebView2MouseEventKind.XButtonDown,
            WM_XBUTTONUP => CoreWebView2MouseEventKind.XButtonUp,
            WM_XBUTTONDBLCLK => CoreWebView2MouseEventKind.XButtonDoubleClick,
            WM_MOUSEHWHEEL => CoreWebView2MouseEventKind.HorizontalWheel,
            _ => CoreWebView2MouseEventKind.Wheel,
        };
        var hi = (m.WParam.ToInt64() >> 16) & 0xFFFF;
        // wheel: signed delta; X buttons: which one (1 or 2); the MK_ flags in the low word map 1:1 onto the virtual keys
        var data = wheel ? (uint)(short)hi : m.Msg is WM_XBUTTONDOWN or WM_XBUTTONUP or WM_XBUTTONDBLCLK ? (uint)hi : 0u;
        var keys = (CoreWebView2MouseEventVirtualKeys)(m.WParam.ToInt64() & 0x7F);
        _cc.SendMouseInput(kind, keys, data, pt);
    }

    void Sample()
    {
        _self.Refresh();
        var now = DateTime.UtcNow; var cpu = _self.TotalProcessorTime;
        var wallMs = (now - _lastWall).TotalMilliseconds;
        var pct = (cpu - _lastCpu).TotalMilliseconds / wallMs * 100;
        _lastCpu = cpu; _lastWall = now;
        // Host process first, then every msedgewebview2.exe child summed.
        _lastSample = $"{pct:F1},{_self.WorkingSet64 / 1048576.0:F0},{_fps:F0},{SampleWebView(wallMs)}";
        if (_log is null) return;
        if (_log.BaseStream.Length > MaxLogBytes) { _log.WriteLine($"{now:O},LOG_FULL,sampler stopped"); _perf.Stop(); return; }
        _log.WriteLine($"{now:O},{_lastSample}");
    }

    // shortcut: a process that starts between two samples is counted from its next sample, so its first interval is missed.
    string SampleWebView(double wallMs)
    {
        double cpuMs = 0, wsMb = 0, privMb = 0; int count = 0;
        var seen = new HashSet<int>();
        // only this app's WebView2 processes (same user data folder), not every msedgewebview2.exe on the PC
        IReadOnlyList<CoreWebView2ProcessInfo> infos;
        try { infos = _env?.GetProcessInfos() ?? []; }
        catch (COMException) { infos = []; } // the browser process is restarting; this sample counts none
        foreach (var info in infos)
        {
            Process? p = null;
            try
            {
                p = Process.GetProcessById(info.ProcessId);
                var t = p.TotalProcessorTime;
                if (_webCpu.TryGetValue(p.Id, out var prev)) cpuMs += (t - prev).TotalMilliseconds;
                _webCpu[p.Id] = t; seen.Add(p.Id);
                wsMb += p.WorkingSet64 / 1048576.0; privMb += p.PrivateMemorySize64 / 1048576.0; count++;
            }
            // a process that exited between listing and reading has no CPU time left to read
            catch (Exception e) when (e is ArgumentException or InvalidOperationException or System.ComponentModel.Win32Exception) { }
            finally { p?.Dispose(); }
        }
        foreach (var gone in _webCpu.Keys.Except(seen).ToList()) _webCpu.Remove(gone);
        return $"{cpuMs / wallMs * 100:F1},{wsMb:F0},{privMb:F0},{count}";
    }

    // --- minimal DirectComposition COM calls by vtable slot (IDCompositionDevice: 3 Commit, 6 CreateTargetForHwnd, 7 CreateVisual; target: 3 SetRoot) ---
    static Guid IID_IDCompositionDevice = new("C37EA93A-E7AA-450D-B16F-9746CB0407F3");
    [DllImport("dcomp.dll")] static extern int DCompositionCreateDevice(IntPtr dxgi, ref Guid iid, out IntPtr device);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] static extern bool SetLayeredWindowAttributes(IntPtr h, uint key, byte alpha, uint flags);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr SetWinEventHook(uint min, uint max, IntPtr module, WinEventProc proc, uint pid, uint thread, uint flags);
    [DllImport("user32.dll")] static extern bool UnhookWinEvent(IntPtr hook);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc proc, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] static extern int GetWindowLong(IntPtr h, int index);
    [DllImport("user32.dll")] static extern int SetWindowLong(IntPtr h, int index, int value);
    [DllImport("user32.dll")] static extern bool GetLayeredWindowAttributes(IntPtr h, out uint key, out byte alpha, out uint flags);
    delegate bool EnumWindowsProc(IntPtr h, IntPtr lParam);
    const int GWL_EXSTYLE = -20;
    delegate int Commit(IntPtr self);
    delegate int CreateTargetForHwnd(IntPtr self, IntPtr hwnd, bool topmost, out IntPtr target);
    delegate int CreateVisual(IntPtr self, out IntPtr visual);
    delegate int SetRoot(IntPtr self, IntPtr visual);
    static T Vcall<T>(IntPtr obj, int slot) where T : Delegate => Marshal.GetDelegateForFunctionPointer<T>(Marshal.ReadIntPtr(Marshal.ReadIntPtr(obj), slot * IntPtr.Size));
    static void Check(int hr, string what) { if (hr < 0) throw new InvalidOperationException($"{what} failed: 0x{hr:X8}"); }

    const string Page = """
        <!doctype html><meta charset=utf-8><style>
        html,body{margin:0;background:transparent;overflow:hidden;color:#7fe9ff;font:14px Consolas,monospace}
        #m{position:absolute;left:__HX__px;top:__HY__px;width:__HW__px;height:__HH__px;border:1px solid #1fb5d4;background:rgba(2,16,24,.55);box-sizing:border-box;padding:12px}
        #ring{position:absolute;right:20px;bottom:20px;width:80px;height:80px;border:3px solid #1fb5d4;border-top-color:transparent;border-radius:50%;animation:s 2s linear infinite}
        @keyframes s{to{transform:rotate(360deg)}}</style>
        <div id=m>SPACESHIP<br>transparent: desktop shows through<br>click-through outside this box<br><button id=b>click me (counts)</button> <span id=c>0</span><div id=ring></div></div>
        <script>let n=0;b.onclick=()=>c.textContent=++n;let f=0,t=performance.now();
        (function loop(){f++;const now=performance.now();if(now-t>=1000){chrome.webview.postMessage(String(f*1000/(now-t)));f=0;t=now}requestAnimationFrame(loop)})()</script>
        """;
}
