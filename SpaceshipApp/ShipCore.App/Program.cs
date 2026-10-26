using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Web.WebView2.Core;
using ShipCore.Core;

// Standalone Spaceship app: one transparent window on the desktop layer, sized to the home display (the taskbar draws over it),
// hosting a composition-mode WebView2 through DirectComposition. Ctrl+Alt+Shift+1 stops the app and everything it started.
// Never topmost, no input hooks, no injection (one out-of-context foreground WinEvent). Tray menu: Start, Stop, Quit.
static class Program
{
    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();
        // A second copy would fight the first for the desktop layer and the kill chord, so it exits quietly.
        using var single = new Mutex(true, @"Local\CSpace.SingleInstance", out var first);
        if (!first) return;
        var marker = new RunMarker(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Spaceship", "running.marker"));
        var lastRunUnclean = marker.LastRunEndedUncleanly();
        marker.MarkRunning(DateTimeOffset.Now);
        // The kill chord is a deliberate stop, so it clears the marker before the process goes.
        var kill = new KillSwitch(() => { marker.MarkCleanExit(); Process.GetCurrentProcess().Kill(entireProcessTree: true); });
        var hotkey = new HotkeyThread(() => kill.Fire());
        Application.Run(new Overlay(hotkey.Registered, marker, lastRunUnclean));
    }
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
    readonly int _uiThread = Environment.CurrentManagedThreadId;

    // Core logic. Null router = no skin folder or contract found: the page gets no settings and nothing is written.
    readonly MessageRouter? _router;
    SettingsStore? _settings;
    IReadOnlyList<string> _hwKeys = Array.Empty<string>();
    // The loopback stays stopped until a setting starts it (F3 Audio), so the spectrum is null and no audio device is opened.
    readonly WasapiLoopback _loopback = new();
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

    public Overlay(bool hotkeyRegistered, RunMarker marker, bool lastRunUnclean)
    {
        _marker = marker;
        _sampler = new(new WindowsMetrics(), new WindowsHwinfoRegistry(), new WindowsNetwork(), _loopback, new WindowsProcessNames());
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        Text = "CSpace";
        TopMost = false; // never above other apps (exam browsers, games)

        var schemaPath = FindUp(Path.Combine("contract", "config-keys.json"));
        var resources = FindUp(Path.Combine("Skins", "Spaceship", "@Resources"));
        if (resources is not null) _jarvisFile = Path.Combine(resources, "Data", "jarvis.txt");
        if (resources is not null) _status = new StatusRunner(Path.Combine(resources, "Scripts"), () => Visible, Post, m => _log?.WriteLine($"{DateTime.UtcNow:O},{m}"));
        _net = new NetRunner(() => _settings?.Get(["PingHost"]).GetValueOrDefault("PingHost"), () => Visible, Post);
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
            _hwKeys = schema.Keys.Keys.Where(k => k.StartsWith("HW_", StringComparison.Ordinal)).ToList();
            // One-time import from the skin, only on the first run; a dry run is SkinImport.Build alone.
            if (!File.Exists(settingsPath) && resources is not null)
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
        _snapshots = new Win32Snapshots(() => _home);
        _life = new Lifecycle(Stop, () => Restart(false));

        var menu = new ContextMenuStrip();
        menu.Items.Add("Start", null, (_, _) => Start());
        menu.Items.Add("Stop", null, (_, _) => Stop());
        // Autostart is deferred by the user: the menu can only remove a Run entry an earlier build wrote, never add one.
        if (_autostart.IsEnabled)
        {
            var auto = new ToolStripMenuItem("Stop starting with Windows");
            auto.Click += (_, _) => { _autostart.Disable(); menu.Items.Remove(auto); };
            menu.Items.Add(auto);
        }
        menu.Items.Add("Quit", null, (_, _) => Quit());
        _tray.Icon = AppIcon(); _tray.Text = "CSpace"; _tray.ContextMenuStrip = menu; _tray.Visible = true;
        if (!hotkeyRegistered) _tray.ShowBalloonTip(5000, "Spaceship", $"{KillChord.Label} is taken by another app, so the kill switch is off.", ToolTipIcon.Warning);
        if (lastRunUnclean) _tray.ShowBalloonTip(5000, "Spaceship", "The last run did not exit cleanly. Its log is in the temp folder under spaceship-app.", ToolTipIcon.Warning);
        _visibility.Tick += (_, _) => ApplyVisibility();
        _visibility.Start();
        // A new foreground app (a game, an exam browser) is checked at once; the 3 s poll stays for fullscreen toggles inside one app.
        _onForeground = (_, _, _, _, _, _, _) => ApplyVisibility();
        _foregroundHook = SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, IntPtr.Zero, _onForeground, 0, 0, WINEVENT_OUTOFCONTEXT);

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
            _env ??= await CoreWebView2Environment.CreateAsync(null, Path.Combine(Path.GetTempPath(), "spaceship-app", "wv2"));
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
        _cc.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false; // right click belongs to the HUD (Top steps back)

        // DirectComposition: a visual tree rooted on this window; WebView2 renders into _dcompVisual.
        Check(DCompositionCreateDevice(IntPtr.Zero, ref IID_IDCompositionDevice, out _dcompDevice), "DCompositionCreateDevice");
        Check(Vcall<CreateTargetForHwnd>(_dcompDevice, 6)(_dcompDevice, Handle, true, out _dcompTarget), "CreateTargetForHwnd");
        Check(Vcall<CreateVisual>(_dcompDevice, 7)(_dcompDevice, out _dcompVisual), "CreateVisual");
        Check(Vcall<SetRoot>(_dcompTarget, 3)(_dcompTarget, _dcompVisual), "SetRoot");
        _cc.RootVisualTarget = Marshal.GetObjectForIUnknown(_dcompVisual); // the wrapper needs a COM object, not a raw pointer
        Check(Vcall<Commit>(_dcompDevice, 3)(_dcompDevice), "Commit");

        _cc.CursorChanged += (_, _) => Cursor = Cursors.Default; // cursor shape not forwarded yet
        _cc.CoreWebView2.WebMessageReceived += (_, a) => OnWebMessage(a);
        _cc.CoreWebView2.ProcessFailed += (_, a) => OnProcessFailed(a);
        // The page is the only thing this view may show: no links, no redirects, no popups.
        _cc.CoreWebView2.NavigationStarting += (_, a) => a.Cancel = a.Uri != "about:blank" && !a.Uri.StartsWith(UiOrigin, StringComparison.Ordinal);
        _cc.CoreWebView2.NewWindowRequested += (_, a) => a.Handled = true;
        _cc.CoreWebView2.NavigationCompleted += (_, a) => { if (a.IsSuccess) _failures = 0; _jarvisSent = null; foreach (var m in _status?.Last ?? []) Post(m); foreach (var m in _net.Last) Post(m); if (_todo.Last is { } t) Post(t); }; // a new page gets the JARVIS and status state again
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
        if (++_failures > MaxRestarts) { _log?.WriteLine($"{DateTime.UtcNow:O},GIVING_UP,{_failures}"); Stop(); return; }
        ReleaseWebView();
        if (freshEnvironment) _env = null;
        Start();
    }

    // Shows the window only while the policy allows it; a fullscreen app or an exam browser sends it away.
    void ApplyVisibility()
    {
        if (!_running || _cc is null) return;
        var decision = _policy.Decide(_snapshots.Take());
        if (decision.Visibility == Visibility.Show) { if (!Visible) Show(); }
        else if (Visible) Hide();
    }

    // One system.metrics frame per second, only while the window is shown; a failed read is logged and skipped.
    void PushMetrics()
    {
        if (_cc?.CoreWebView2 is null || !Visible) return;
        try
        {
            var settings = _settings?.Get(_hwKeys) ?? new Dictionary<string, string>();
            _cc.CoreWebView2.PostWebMessageAsJson(SystemSampler.ToJson(_sampler.Sample(settings, ++_metricsSeq)));
        }
        catch (Exception e) { _log?.WriteLine($"{DateTime.UtcNow:O},METRICS_FAILED,{e.GetType().Name}"); }
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

    // Power and flow actions need a person to say yes; the schema lists none of them, so this is only reached through the gate.
    Task<bool> ConfirmAsync(string id) =>
        Task.FromResult(MessageBox.Show(this, $"Allow the {id} action?", "Spaceship", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes);

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
        if (_foregroundHook != IntPtr.Zero) UnhookWinEvent(_foregroundHook);
        _visibility.Stop(); _perf.Stop(); _metricsTimer.Stop(); _jarvisTimer.Stop(); _status?.Dispose(); _net.Dispose(); _todo.Dispose(); _cursor.Stop(); _loopback.Dispose(); _tray.Dispose(); _log?.Dispose(); _log = null; _jarvis.Dispose();
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
            case WM_DISPLAYCHANGE: BeginInvoke(new Action(Rehome)); break; // after Windows finishes moving the screens
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
            case WM_MOUSEMOVE: case WM_LBUTTONUP: case WM_MOUSEWHEEL:
            case WM_RBUTTONDOWN: case WM_RBUTTONUP: case WM_MBUTTONDOWN: case WM_MBUTTONUP:
                ForwardMouse(m); return;
        }
        base.WndProc(ref m);
    }

    void ForwardMouse(Message m)
    {
        if (_cc is null) return;
        var lp = m.LParam.ToInt64();
        var pt = new Point((short)(lp & 0xFFFF), (short)((lp >> 16) & 0xFFFF));
        if (m.Msg == WM_MOUSEWHEEL) pt = PointToClient(pt); // wheel coordinates are screen-relative
        var kind = m.Msg switch
        {
            WM_MOUSEMOVE => CoreWebView2MouseEventKind.Move,
            WM_LBUTTONDOWN => CoreWebView2MouseEventKind.LeftButtonDown,
            WM_LBUTTONUP => CoreWebView2MouseEventKind.LeftButtonUp,
            WM_RBUTTONDOWN => CoreWebView2MouseEventKind.RightButtonDown,
            WM_RBUTTONUP => CoreWebView2MouseEventKind.RightButtonUp,
            WM_MBUTTONDOWN => CoreWebView2MouseEventKind.MiddleButtonDown,
            WM_MBUTTONUP => CoreWebView2MouseEventKind.MiddleButtonUp,
            _ => CoreWebView2MouseEventKind.Wheel,
        };
        var data = m.Msg == WM_MOUSEWHEEL ? (uint)(short)((m.WParam.ToInt64() >> 16) & 0xFFFF) : 0u;
        _cc.SendMouseInput(kind, CoreWebView2MouseEventVirtualKeys.None, data, pt);
    }

    void Sample()
    {
        _self.Refresh();
        var now = DateTime.UtcNow; var cpu = _self.TotalProcessorTime;
        var wallMs = (now - _lastWall).TotalMilliseconds;
        var pct = (cpu - _lastCpu).TotalMilliseconds / wallMs * 100;
        _lastCpu = cpu; _lastWall = now;
        // Host process first, then every msedgewebview2.exe child summed.
        _log?.WriteLine($"{now:O},{pct:F1},{_self.WorkingSet64 / 1048576.0:F0},{_fps:F0},{SampleWebView(wallMs)}");
    }

    // shortcut: a process that starts between two samples is counted from its next sample, so its first interval is missed.
    string SampleWebView(double wallMs)
    {
        double cpuMs = 0, wsMb = 0, privMb = 0; int count = 0;
        var seen = new HashSet<int>();
        foreach (var p in Process.GetProcessesByName("msedgewebview2"))
        {
            try
            {
                var t = p.TotalProcessorTime;
                if (_webCpu.TryGetValue(p.Id, out var prev)) cpuMs += (t - prev).TotalMilliseconds;
                _webCpu[p.Id] = t; seen.Add(p.Id);
                wsMb += p.WorkingSet64 / 1048576.0; privMb += p.PrivateMemorySize64 / 1048576.0; count++;
            }
            // a process that exited between listing and reading has no CPU time left to read
            catch (Exception e) when (e is InvalidOperationException or System.ComponentModel.Win32Exception) { }
            finally { p.Dispose(); }
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
