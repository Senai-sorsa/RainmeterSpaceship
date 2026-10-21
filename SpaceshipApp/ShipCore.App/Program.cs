using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Web.WebView2.Core;
using ShipCore.Core;

// Standalone Spaceship app: one transparent window over the desktop, sized to the work area (it stops at the top of the taskbar),
// hosting a composition-mode WebView2 through DirectComposition. Ctrl+Alt+1 stops the app and everything it started.
// Never topmost, no hooks, no injection. Tray menu: Start, Stop, Quit.
static class Program
{
    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();
        var kill = new KillSwitch(() => Process.GetCurrentProcess().Kill(entireProcessTree: true));
        var hotkey = new HotkeyThread(() => kill.Fire());
        Application.Run(new Overlay(hotkey.Registered));
    }
}

// Ctrl+Alt+1 on its own thread, so it still works when the window is frozen.
sealed class HotkeyThread
{
    const uint MOD_ALT = 0x1, MOD_CONTROL = 0x2, MOD_NOREPEAT = 0x4000, VK_1 = 0x31, WM_HOTKEY = 0x0312;
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
        Registered = RegisterHotKey(IntPtr.Zero, ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_1);
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
    const int WM_NCHITTEST = 0x84, HTTRANSPARENT = -1, HTCLIENT = 1;
    const int WM_MOUSEMOVE = 0x200, WM_LBUTTONDOWN = 0x201, WM_LBUTTONUP = 0x202, WM_MOUSEWHEEL = 0x20A;
    const int WM_QUERYENDSESSION = 0x11, WM_ENDSESSION = 0x16;

    // The only region that takes the mouse; everything else falls through to the desktop and the apps under it.
    static readonly Rectangle Hit = new(80, 80, 360, 220);
    readonly Rectangle _home;

    CoreWebView2Environment? _env;
    CoreWebView2CompositionController? _cc;
    IntPtr _dcompDevice, _dcompTarget, _dcompVisual;
    readonly NotifyIcon _tray = new();
    readonly System.Windows.Forms.Timer _perf = new() { Interval = 5000 };
    readonly Process _self = Process.GetCurrentProcess();
    TimeSpan _lastCpu; DateTime _lastWall = DateTime.UtcNow;
    double _fps;
    bool _running, _starting; // _running = the user asked for it; _starting = a web view is being created
    int _failures; // web view restarts since the last good page load
    const int MaxRestarts = 3;
    StreamWriter? _log;
    readonly int _uiThread = Environment.CurrentManagedThreadId;

    // Core logic. Null router = no skin folder or contract found: the page gets no settings and nothing is written.
    readonly MessageRouter? _router;
    readonly VisibilityPolicy _policy;
    readonly Win32Snapshots _snapshots;
    readonly System.Windows.Forms.Timer _visibility = new() { Interval = 3000 };
    readonly AutoStart _autostart = new(new RunKeyStore());
    readonly Lifecycle _life;
    readonly JarvisPipe _jarvis = new(new SystemClock());

    public Overlay(bool hotkeyRegistered)
    {
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        _home = HomeScreen().Bounds; // the full display, taskbar included: the desktop layer lets the taskbar draw over it
        Bounds = _home;
        TopMost = false; // never above other apps (exam browsers, games)

        var schemaPath = FindUp(Path.Combine("contract", "config-keys.json"));
        var resources = FindUp(Path.Combine("Skins", "Spaceship", "@Resources"));
        if (schemaPath is not null && resources is not null)
        {
            var schema = ConfigSchema.Parse(File.ReadAllText(schemaPath));
            // Shortcut: power actions and flows are not wired (the schema lists no power action, and flows need P-F). The gate refuses by throwing, which is logged.
            var unwired = new UnwiredHost();
            _router = new MessageRouter(schema, new ConfigStore(resources, schema), new ActionGate(unwired, unwired), ConfirmAsync);
        }
        var examPath = FindUp(Path.Combine("contract", "exam-browsers.json"));
        _policy = new VisibilityPolicy(examPath is null ? Array.Empty<string>() : ExamBrowserList.ProcessNames(File.ReadAllText(examPath)));
        _snapshots = new Win32Snapshots(() => _home);
        _life = new Lifecycle(Stop, () => Restart(false), () => { }); // Switch to Rainmeter is P-H; the tray menu does not offer it yet

        var menu = new ContextMenuStrip();
        menu.Items.Add("Start", null, (_, _) => Start());
        menu.Items.Add("Stop", null, (_, _) => Stop());
        var auto = new ToolStripMenuItem("Start with Windows") { CheckOnClick = true, Checked = _autostart.IsEnabled };
        auto.Click += (_, _) =>
        {
            if (!auto.Checked) { _autostart.Disable(); return; }
            var problem = _autostart.Enable(Environment.ProcessPath ?? "");
            if (problem is null) return;
            auto.Checked = false;
            _tray.ShowBalloonTip(5000, "Spaceship", problem, ToolTipIcon.Warning);
        };
        menu.Items.Add(auto);
        menu.Items.Add("Quit", null, (_, _) => Quit());
        _tray.Icon = SystemIcons.Application; _tray.Text = "Spaceship"; _tray.ContextMenuStrip = menu; _tray.Visible = true;
        if (!hotkeyRegistered) _tray.ShowBalloonTip(5000, "Spaceship", "Ctrl+Alt+1 is taken by another app, so the kill switch is off.", ToolTipIcon.Warning);
        _visibility.Tick += (_, _) => ApplyVisibility();
        _visibility.Start();

        var dir = Path.Combine(Path.GetTempPath(), "spaceship-app");
        Directory.CreateDirectory(dir);
        var old = new DirectoryInfo(dir).GetFiles("perf-*.csv").Select(f => (f.FullName, f.LastWriteTime));
        foreach (var path in HostRules.ExpiredLogs(old, DateTime.Now, TimeSpan.FromDays(7))) File.Delete(path);
        _log = new StreamWriter(Path.Combine(dir, $"perf-{DateTime.Now:yyyyMMdd-HHmmss}.csv")) { AutoFlush = true };
        _log.WriteLine("utc,cpu_percent_of_one_core,working_set_mb,js_fps");
        _lastCpu = _self.TotalProcessorTime;
        _perf.Tick += (_, _) => Sample();
        _perf.Start();
        _jarvis.Start();
    }

    protected override CreateParams CreateParams
    {
        get { var p = base.CreateParams; p.ExStyle |= WS_EX_NOREDIRECTIONBITMAP | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE; return p; }
    }
    protected override bool ShowWithoutActivation => true;

    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        AttachToDesktopLayer();
        Start();
    }

    // Rainmeter's "On desktop" layer: parent to WorkerW, which sits under the desktop icons and under every normal window.
    // The taskbar is a separate top-level window above it, so the taskbar draws over this window.
    void AttachToDesktopLayer()
    {
        var worker = DesktopWorker();
        if (worker == IntPtr.Zero)
        {
            // fallback: bottom of the z-order (not verified to stay under the taskbar)
            SetWindowPos(Handle, (IntPtr)1 /*HWND_BOTTOM*/, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010); // SWP_NOSIZE|NOMOVE|NOACTIVATE
            return;
        }
        SetParent(Handle, worker);
        var at = _home.Location;
        ScreenToClient(worker, ref at);
        SetBounds(at.X, at.Y, _home.Width, _home.Height);
    }

    static IntPtr DesktopWorker()
    {
        var progman = FindWindow("Progman", null);
        SendMessageTimeout(progman, 0x052C, IntPtr.Zero, IntPtr.Zero, 0, 1000, out _); // asks the shell to create WorkerW
        var worker = IntPtr.Zero;
        EnumWindows((top, _) =>
        {
            if (FindWindowEx(top, IntPtr.Zero, "SHELLDLL_DefView", null) != IntPtr.Zero)
                worker = FindWindowEx(IntPtr.Zero, top, "WorkerW", null);
            return true;
        }, IntPtr.Zero);
        return worker;
    }

    // The display whose size matches HomeSize in Settings.inc (2560x1600); the primary display if none does.
    static Screen HomeScreen()
    {
        var screens = Screen.AllScreens;
        var index = HostRules.PickHomeDisplay(screens.Select(s => (s.Bounds.Width, s.Bounds.Height)).ToList(), (2560, 1600));
        return index >= 0 ? screens[index] : Screen.PrimaryScreen!;
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
        _cc.CoreWebView2.NavigationStarting += (_, a) => a.Cancel = a.Uri != "about:blank";
        _cc.CoreWebView2.NewWindowRequested += (_, a) => a.Handled = true;
        _cc.CoreWebView2.NavigationCompleted += (_, a) => { if (a.IsSuccess) _failures = 0; };
        _cc.CoreWebView2.NavigateToString(PageHtml());
    }

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

    // Renderer exit: reload. Browser exit: a fresh environment. Unresponsive: WebView2 may recover, so only log it.
    void OnProcessFailed(CoreWebView2ProcessFailedEventArgs a)
    {
        _log?.WriteLine($"{DateTime.UtcNow:O},PROCESS_FAILED,{a.ProcessFailedKind}");
        switch (a.ProcessFailedKind)
        {
            // Deferred: the web view cannot be closed from inside its own event.
            case CoreWebView2ProcessFailedKind.RenderProcessExited: BeginInvoke(new Action(() => Restart(false))); break;
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
        _life.Teardown(); // runs Stop once, whichever of quit or sign-out gets here first
        _visibility.Stop(); _perf.Stop(); _tray.Dispose(); _log?.Dispose(); _log = null; _jarvis.Dispose();
        Application.Exit();
    }

    protected override void WndProc(ref Message m)
    {
        switch (m.Msg)
        {
            case WM_QUERYENDSESSION: m.Result = _life.OnQueryEndSession() ? (IntPtr)1 : IntPtr.Zero; return; // never block sign-out
            case WM_ENDSESSION: _life.OnEndSession(m.WParam != IntPtr.Zero); if (m.WParam != IntPtr.Zero) Quit(); m.Result = IntPtr.Zero; return;
            case WM_NCHITTEST:
            {
                var p = PointToClient(new Point((short)(m.LParam.ToInt64() & 0xFFFF), (short)((m.LParam.ToInt64() >> 16) & 0xFFFF)));
                m.Result = (IntPtr)(Hit.Contains(p) ? HTCLIENT : HTTRANSPARENT); // transparent = the click goes to whatever is underneath
                return;
            }
            case WM_MOUSEMOVE: case WM_LBUTTONDOWN: case WM_LBUTTONUP: case WM_MOUSEWHEEL:
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
            _ => CoreWebView2MouseEventKind.Wheel,
        };
        var data = m.Msg == WM_MOUSEWHEEL ? (uint)(short)((m.WParam.ToInt64() >> 16) & 0xFFFF) : 0u;
        _cc.SendMouseInput(kind, CoreWebView2MouseEventVirtualKeys.None, data, pt);
    }

    void Sample()
    {
        _self.Refresh();
        var now = DateTime.UtcNow; var cpu = _self.TotalProcessorTime;
        var pct = (cpu - _lastCpu).TotalMilliseconds / (now - _lastWall).TotalMilliseconds * 100;
        _lastCpu = cpu; _lastWall = now;
        // Host process only; WebView2's own processes (msedgewebview2.exe) are not included.
        _log?.WriteLine($"{now:O},{pct:F1},{_self.WorkingSet64 / 1048576.0:F0},{_fps:F0}");
    }

    // --- minimal DirectComposition COM calls by vtable slot (IDCompositionDevice: 3 Commit, 6 CreateTargetForHwnd, 7 CreateVisual; target: 3 SetRoot) ---
    static Guid IID_IDCompositionDevice = new("C37EA93A-E7AA-450D-B16F-9746CB0407F3");
    [DllImport("dcomp.dll")] static extern int DCompositionCreateDevice(IntPtr dxgi, ref Guid iid, out IntPtr device);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr FindWindow(string cls, string? name);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr FindWindowEx(IntPtr parent, IntPtr after, string cls, string? name);
    [DllImport("user32.dll")] static extern IntPtr SendMessageTimeout(IntPtr h, uint msg, IntPtr w, IntPtr l, uint flags, uint timeout, out IntPtr result);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
    [DllImport("user32.dll")] static extern IntPtr SetParent(IntPtr child, IntPtr parent);
    [DllImport("user32.dll")] static extern bool ScreenToClient(IntPtr h, ref Point p);
    delegate bool EnumWindowsProc(IntPtr h, IntPtr lParam);
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
