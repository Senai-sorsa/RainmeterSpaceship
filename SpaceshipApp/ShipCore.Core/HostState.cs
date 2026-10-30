using System.Text.Json;

namespace ShipCore.Core;

/// <summary>Setup flag, About-me text and whether the user stopped the HUD, for the page and the tray. Kept in the app's own data folder, never in the skin. With no path it is memory only.</summary>
public sealed class HostState
{
    private const int MaxAboutMe = 4000;
    private readonly string? _path;
    private readonly object _lock = new();

    public HostState(string? path)
    {
        _path = path;
        Load();
    }

    public bool SetupDone { get; private set; }
    public string AboutMe { get; private set; } = "";
    /// <summary>The user chose Stop from the tray: the next launch stays stopped until Start.</summary>
    public bool Stopped { get; private set; }

    public void SetSetupDone(bool done) { lock (_lock) { SetupDone = done; Save(); } }

    public void SetStopped(bool stopped) { lock (_lock) { Stopped = stopped; Save(); } }

    public void SetAboutMe(string text) { lock (_lock) { AboutMe = text; Save(); } }

    private void Load()
    {
        if (_path is null || !File.Exists(_path)) return;
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(_path));
            var root = doc.RootElement;
            SetupDone = root.TryGetProperty("setupDone", out var s) && s.ValueKind == JsonValueKind.True;
            Stopped = root.TryGetProperty("stopped", out var st) && st.ValueKind == JsonValueKind.True;
            if (root.TryGetProperty("aboutMe", out var a) && a.ValueKind == JsonValueKind.String && a.GetString()!.Length <= MaxAboutMe)
                AboutMe = a.GetString()!;
        }
        catch (Exception e) when (e is JsonException or IOException or UnauthorizedAccessException)
        {
            // Unreadable file: start empty. The next save replaces it.
        }
    }

    private void Save()
    {
        if (_path is null) return;
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(_path)!);
            var tmp = _path + ".tmp";
            File.WriteAllText(tmp, JsonSerializer.Serialize(new { setupDone = SetupDone, aboutMe = AboutMe, stopped = Stopped }));
            File.Move(tmp, _path, overwrite: true);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // Not saved: this run keeps the value in memory, as the mock host does when storage is blocked.
        }
    }
}
