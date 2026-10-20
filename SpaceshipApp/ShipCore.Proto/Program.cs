using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Web.WebView2.Core;
using ShipCore.Core;

// P-D prototype: one transparent top-level window (WS_EX_NOREDIRECTIONBITMAP) hosting a composition-mode WebView2 via DirectComposition.
// Question it answers: does a transparent, click-through, animated WebView2 sit over the desktop at an acceptable cost? See docs/P-D-PROTOTYPE.md.
// Never topmost, no hooks, no injection. Right-click the tray icon > Quit, or press Esc while the demo panel is focused.
static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new Overlay(args.Contains("--autostart")));
    }
}

sealed class Overlay : Form
{
    const int WS_EX_NOREDIRECTIONBITMAP = 0x00200000, WS_EX_TOOLWINDOW = 0x80, WS_EX_NOACTIVATE = 0x08000000;
    const int WM_NCHITTEST = 0x84, HTTRANSPARENT = -1, HTCLIENT = 1;
    const int WM_MOUSEMOVE = 0x200, WM_LBUTTONDOWN = 0x201, WM_LBUTTONUP = 0x202, WM_MOUSEWHEEL = 0x20A, WM_MOUSELEAVE = 0x2A3;
    const int WM_QUERYENDSESSION = 0x11, WM_ENDSESSION = 0x16;

    // The only region that takes the mouse; everything else falls through to the desktop and the apps under it.
    static readonly Rectangle Hit = new(80, 80, 360, 220);

    CoreWebView2Environment? _env;
    CoreWebView2CompositionController? _cc;
    IntPtr _dcompDevice, _dcompTarget, _dcompVisual;
    readonly NotifyIcon _tray = new();
    readonly Lifecycle _life;
    readonly System.Windows.Forms.Timer _perf = new() { Interval = 5000 };
    readonly Process _self = Process.GetCurrentProcess();
    TimeSpan _lastCpu; DateTime _lastWall = DateTime.UtcNow;
    double _fps;
    StreamWriter? _log;

    public Overlay(bool autostart)
    {
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        Bounds = Screen.PrimaryScreen!.Bounds;
        TopMost = false; // never above other apps (exam browsers, games)

        _life = new Lifecycle(Teardown, () => _cc?.CoreWebView2.Reload(), () => Process.Start(new ProcessStartInfo("Rainmeter.exe") { UseShellExecute = true }));
        var menu = new ContextMenuStrip();
        foreach (var (id, label) in Lifecycle.TrayMenu) menu.Items.Add(label, null, (_, _) => { if (_life.Handle(id)) Application.Exit(); });
        _tray.Icon = SystemIcons.Application; _tray.Text = "Spaceship P-D prototype"; _tray.ContextMenuStrip = menu; _tray.Visible = true;

        var dir = Path.Combine(Path.GetTempPath(), "spaceship-pd");
        Directory.CreateDirectory(dir);
        _log = new StreamWriter(Path.Combine(dir, $"perf-{DateTime.Now:yyyyMMdd-HHmmss}.csv")) { AutoFlush = true };
        _log.WriteLine("utc,cpu_percent_of_one_core,working_set_mb,js_fps");
        _lastCpu = _self.TotalProcessorTime;
        _perf.Tick += (_, _) => Sample();
        _perf.Start();
    }

    protected override CreateParams CreateParams
    {
        get { var p = base.CreateParams; p.ExStyle |= WS_EX_NOREDIRECTIONBITMAP | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE; return p; }
    }
    protected override bool ShowWithoutActivation => true;

    protected override async void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        SetWindowPos(Handle, (IntPtr)1 /*HWND_BOTTOM*/, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010); // SWP_NOSIZE|NOMOVE|NOACTIVATE
        try { await InitWebViewAsync(); }
        catch (Exception ex) { MessageBox.Show("P-D FAIL (record this): " + ex.Message); Application.Exit(); }
    }

    async Task InitWebViewAsync()
    {
        _env = await CoreWebView2Environment.CreateAsync(null, Path.Combine(Path.GetTempPath(), "spaceship-pd", "wv2"));
        _cc = await _env.CreateCoreWebView2CompositionControllerAsync(Handle);
        _cc.Bounds = new Rectangle(0, 0, ClientSize.Width, ClientSize.Height);
        _cc.DefaultBackgroundColor = Color.Transparent;
        _cc.IsVisible = true;

        // DirectComposition: a visual tree rooted on this window; WebView2 renders into _dcompVisual.
        Check(DCompositionCreateDevice(IntPtr.Zero, ref IID_IDCompositionDevice, out _dcompDevice), "DCompositionCreateDevice");
        Check(Vcall<CreateTargetForHwnd>(_dcompDevice, 6)(_dcompDevice, Handle, true, out _dcompTarget), "CreateTargetForHwnd");
        Check(Vcall<CreateVisual>(_dcompDevice, 7)(_dcompDevice, out _dcompVisual), "CreateVisual");
        Check(Vcall<SetRoot>(_dcompTarget, 3)(_dcompTarget, _dcompVisual), "SetRoot");
        _cc.RootVisualTarget = _dcompVisual;
        Check(Vcall<Commit>(_dcompDevice, 3)(_dcompDevice), "Commit");

        _cc.CursorChanged += (_, _) => Cursor = Cursors.Default; // prototype: cursor shape not forwarded yet
        _cc.CoreWebView2.WebMessageReceived += (_, a) => { if (double.TryParse(a.TryGetWebMessageAsString(), System.Globalization.CultureInfo.InvariantCulture, out var f)) _fps = f; };
        _cc.CoreWebView2.ProcessFailed += (_, a) => _log?.WriteLine($"{DateTime.UtcNow:O},PROCESS_FAILED,{a.ProcessFailedKind},");
        _cc.CoreWebView2.NavigateToString(Page);
    }

    protected override void WndProc(ref Message m)
    {
        switch (m.Msg)
        {
            case WM_QUERYENDSESSION: m.Result = _life.OnQueryEndSession() ? (IntPtr)1 : IntPtr.Zero; return;
            case WM_ENDSESSION: _life.OnEndSession(m.WParam != IntPtr.Zero); m.Result = IntPtr.Zero; return;
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
        // Host process only; WebView2's own processes (msedgewebview2.exe) must be added from Task Manager / typeperf, see the doc.
        _log?.WriteLine($"{now:O},{pct:F1},{_self.WorkingSet64 / 1048576.0:F0},{_fps:F0}");
    }

    void Teardown()
    {
        _perf.Stop(); _tray.Visible = false; _log?.Dispose(); _log = null;
        try { _cc?.Close(); } catch { /* shutting down */ }
    }

    protected override void OnFormClosed(FormClosedEventArgs e) { _life.Teardown(); base.OnFormClosed(e); }

    // --- minimal DirectComposition COM calls by vtable slot (IDCompositionDevice: 3 Commit, 6 CreateTargetForHwnd, 7 CreateVisual; target: 3 SetRoot) ---
    static Guid IID_IDCompositionDevice = new("C37EA93A-E7AA-450D-B16F-9746CB0407F3");
    [DllImport("dcomp.dll")] static extern int DCompositionCreateDevice(IntPtr dxgi, ref Guid iid, out IntPtr device);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    delegate int Commit(IntPtr self);
    delegate int CreateTargetForHwnd(IntPtr self, IntPtr hwnd, bool topmost, out IntPtr target);
    delegate int CreateVisual(IntPtr self, out IntPtr visual);
    delegate int SetRoot(IntPtr self, IntPtr visual);
    static T Vcall<T>(IntPtr obj, int slot) where T : Delegate => Marshal.GetDelegateForFunctionPointer<T>(Marshal.ReadIntPtr(Marshal.ReadIntPtr(obj), slot * IntPtr.Size));
    static void Check(int hr, string what) { if (hr < 0) throw new InvalidOperationException($"{what} failed: 0x{hr:X8}"); }

    const string Page = """
        <!doctype html><meta charset=utf-8><style>
        html,body{margin:0;background:transparent;overflow:hidden;color:#7fe9ff;font:14px Consolas,monospace}
        #m{position:absolute;left:80px;top:80px;width:360px;height:220px;border:1px solid #1fb5d4;background:rgba(2,16,24,.55);box-sizing:border-box;padding:12px}
        #ring{position:absolute;right:20px;bottom:20px;width:80px;height:80px;border:3px solid #1fb5d4;border-top-color:transparent;border-radius:50%;animation:s 2s linear infinite}
        @keyframes s{to{transform:rotate(360deg)}}</style>
        <div id=m>P-D PROTOTYPE<br>transparent: desktop shows through<br>click-through outside this box<br><button id=b>click me (counts)</button> <span id=c>0</span><div id=ring></div></div>
        <script>let n=0;b.onclick=()=>c.textContent=++n;let f=0,t=performance.now();
        (function loop(){f++;const now=performance.now();if(now-t>=1000){chrome.webview.postMessage(String(f*1000/(now-t)));f=0;t=now}requestAnimationFrame(loop)})()</script>
        """;
}
