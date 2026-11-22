using ShipCore.Core;

// The reticle's to-do mode: reads the ObsidianTodo note (read-only) every 5 s while the HUD is shown, like target.lua,
// but parses only when the note's write time or size changed. A todo.update goes to the page when the list changes.
sealed class TodoRunner(Func<(string? Path, bool On)> setting, Func<bool> shown, Action<string> post) : IDisposable
{
    readonly System.Windows.Forms.Timer _tick = new() { Interval = 5000 };
    (string?, DateTime, long) _stamp;
    string? _sent;

    public void Start()
    {
        _tick.Tick += (_, _) => { if (shown()) Read(); };
        _tick.Start();
        Read();
    }

    /// <summary>The last message, for a page that just loaded.</summary>
    public string? Last => _sent;

    void Read()
    {
        var (path, on) = setting();
        string? text = null;
        // Only a rooted .md note; anything else reads as no note.
        if (on && !string.IsNullOrWhiteSpace(path) && Path.IsPathFullyQualified(path = path.Trim().Trim('"'))
            && path.EndsWith(".md", StringComparison.OrdinalIgnoreCase))
        {
            try
            {
                var info = new FileInfo(path);
                if (info.Exists && info.Length <= TodoNote.MaxBytes)
                {
                    var stamp = (path, info.LastWriteTimeUtc, info.Length);
                    if (stamp == _stamp) return;
                    _stamp = stamp;
                    using var f = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
                    text = new StreamReader(f).ReadToEnd();
                }
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException) { _stamp = default; }
        }
        if (text is null) _stamp = default;
        var json = TodoNote.ToJson(text, TimeZoneInfo.Local);
        if (json == _sent) return;
        _sent = json;
        post(json);
    }

    public void Dispose() { _tick.Stop(); _tick.Dispose(); }
}
