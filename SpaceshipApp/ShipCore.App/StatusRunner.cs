using System.Diagnostics;
using ShipCore.Core;

// Runs the skin's query-only status scripts (Scripts\upkeep.ps1, Scripts\dev.ps1) on the skin's schedule, the way its
// RunCommand measures do: the first run 5 s after start, then every period while the HUD is shown. One run per script
// at a time; a run past its timeout has its own process tree ended. The output becomes a status.update message.
sealed class StatusRunner(string scriptsDir, Func<bool> shown, Action<string> post, Action<string> log) : IDisposable
{
    static readonly string PowerShell = Path.Combine(Environment.SystemDirectory, "WindowsPowerShell", "v1.0", "powershell.exe");
    static readonly TimeSpan Timeout = TimeSpan.FromSeconds(120);
    readonly System.Windows.Forms.Timer _tick = new() { Interval = 5000 };
    readonly Dictionary<string, DateTime> _due = StatusScripts.Kinds.Keys.ToDictionary(k => k, _ => DateTime.MinValue);
    readonly HashSet<string> _busy = [];
    readonly Dictionary<string, string> _last = [];

    public void Start()
    {
        _tick.Tick += (_, _) => Tick();
        _tick.Start();
    }

    /// <summary>The last message of each kind, for a page that just loaded.</summary>
    public IEnumerable<string> Last => _last.Values.ToList();

    /// <summary>Runs one kind on the next tick (status.refresh, and after a console switch); a run already going is followed by another.</summary>
    public void Soon(string kind) => _due[kind] = DateTime.MinValue;

    void Tick()
    {
        if (!shown()) return;
        foreach (var (kind, (script, period)) in StatusScripts.Kinds)
        {
            if (_busy.Contains(kind) || DateTime.UtcNow < _due[kind]) continue;
            _busy.Add(kind);
            _due[kind] = DateTime.UtcNow.AddSeconds(period);
            var path = Path.Combine(scriptsDir, script);
            Task.Run(() => RunScript(path)).ContinueWith(t =>
            {
                _busy.Remove(kind);
                if (t.Exception is { } e) { log($"STATUS_FAILED,{kind},{e.InnerException?.GetType().Name}"); return; }
                var json = StatusScripts.ToJson(kind, t.Result);
                if (json is null) { log($"STATUS_BAD_OUTPUT,{kind}"); return; }
                _last[kind] = json;
                post(json);
            }, TaskScheduler.FromCurrentSynchronizationContext());
        }
    }

    // A fixed interpreter (by full path, not PATH) and a fixed script under the skin folder; nothing from the page reaches the command line.
    internal static string RunScript(string path, TimeSpan? timeout = null)
    {
        if (!File.Exists(path)) throw new FileNotFoundException(path);
        var info = new ProcessStartInfo(PowerShell) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true };
        // RemoteSigned, not Bypass: local scripts run, downloaded ones don't; Bypass and -WindowStyle Hidden are what AV rules flag (CreateNoWindow already hides it).
        foreach (var a in new[] { "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "RemoteSigned", "-File", path }) info.ArgumentList.Add(a);
        using var p = Process.Start(info) ?? throw new InvalidOperationException("powershell did not start");
        var read = p.StandardOutput.ReadToEndAsync();
        if (!p.WaitForExit(timeout ?? Timeout))
        {
            p.Kill(entireProcessTree: true); // only the tree this runner started
            throw new TimeoutException(Path.GetFileName(path));
        }
        if (p.ExitCode != 0) throw new InvalidOperationException($"exit {p.ExitCode}");
        return read.Result;
    }

    public void Dispose() { _tick.Stop(); _tick.Dispose(); }
}
