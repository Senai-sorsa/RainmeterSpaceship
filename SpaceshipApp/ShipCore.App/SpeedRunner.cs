using System.Diagnostics;
using System.Globalization;
using ShipCore.Core;

// The NET boxes' click (sphere.lua / sysinfo.lua -> ShipCore.exe speedtest): Ookla's speedtest.exe where ShipCore looks for it
// (WinGet links, PATH, WinGet packages), one test at a time, the result saved as LinkDownMbps / LinkUpMbps.
// shortcut: no automatic test every AutoSpeedTestHours (ShipCore's quiet-network timer), and LastSpeedTest is not saved (not a settings key); add both if missed.
sealed class SpeedRunner(Func<string, string, bool> save, Action<string> post) : IDisposable
{
    static readonly TimeSpan Timeout = TimeSpan.FromSeconds(120);
    readonly RunnerLifetime _life = new(); // shutdown: ends a running test's process tree, and nothing is saved or posted after it
    bool _busy;

    /// <summary>The last message, for a page that just loaded.</summary>
    public string? Last { get; private set; }

    static string? Exe()
    {
        var la = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var c = new List<string> { Path.Combine(la, "Microsoft", "WinGet", "Links", "speedtest.exe") };
        foreach (var d in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            if (Path.IsPathFullyQualified(d)) c.Add(Path.Combine(d, "speedtest.exe"));
        var pk = Path.Combine(la, "Microsoft", "WinGet", "Packages");
        try { if (Directory.Exists(pk)) c.AddRange(Directory.GetDirectories(pk, "Ookla.Speedtest*").Select(d => Path.Combine(d, "speedtest.exe"))); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
        return c.FirstOrDefault(File.Exists);
    }

    /// <summary>Called on the UI thread; a click while a test runs is ignored, as in the skin.</summary>
    public async void Run()
    {
        if (_busy || _life.Disposed) return;
        _busy = true;
        Send("testing");
        try { var (state, why) = await Task.Run(Test); Send(state, why); }
        finally { _busy = false; }
    }

    void Send(string state, string why = "")
    {
        if (_life.Disposed) return;
        Last = SpeedTest.Message(state, why);
        _life.Post(post, Last);
    }

    (string, string) Test()
    {
        var exe = Exe();
        if (exe is null) return ("error", "speedtest not installed");
        var info = new ProcessStartInfo(exe) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true };
        foreach (var a in new[] { "--format=json", "--accept-license", "--accept-gdpr" }) info.ArgumentList.Add(a);
        try
        {
            using var p = Process.Start(info) ?? throw new InvalidOperationException("did not start");
            // Dispose ends the tree started here (and only it); WaitForExit then returns and nothing is saved.
            using var stop = _life.Token.Register(() => { try { p.Kill(entireProcessTree: true); } catch (Exception) { } }); // already gone, or not killable: nothing to do, and Dispose must not throw
            var output = p.StandardOutput.ReadToEndAsync();
            if (!p.WaitForExit(Timeout)) { p.Kill(entireProcessTree: true); return ("error", "timed out"); } // only the tree started here
            if (_life.Disposed) return ("error", "stopped");
            if (SpeedTest.Parse(output.Result) is not { } r) return ("error", "no result");
            string Mbps(double v) => Math.Clamp(Math.Round(v), 0, 10000).ToString(CultureInfo.InvariantCulture);
            return save("LinkDownMbps", Mbps(r.Down)) && save("LinkUpMbps", Mbps(r.Up)) ? ("done", "") : ("error", "could not save");
        }
        catch (Exception e) when (e is System.ComponentModel.Win32Exception or InvalidOperationException or IOException) { return ("error", "did not run"); }
    }

    public void Dispose() => _life.Dispose();
}
