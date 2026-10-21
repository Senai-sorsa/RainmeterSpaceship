using System.Text;
using System.Text.Json;

namespace ShipCore.Core;

/// <summary>The host's own settings: one versioned JSON file under %LOCALAPPDATA%\Spaceship. Writes are schema-checked and atomic, and keys this build does not know are kept. A file that cannot be parsed is never overwritten.</summary>
public sealed class SettingsStore : IConfigStore
{
    private const int Version = 1;
    private readonly string _path;
    private readonly ConfigSchema _schema;
    private readonly object _lock = new();

    public SettingsStore(string path, ConfigSchema schema) { _path = path; _schema = schema; }

    public Dictionary<string, string> Get(IEnumerable<string> keys)
    {
        var res = new Dictionary<string, string>();
        lock (_lock)
        {
            var all = Load(out _);
            foreach (var k in keys)
                if (_schema.Keys.ContainsKey(k) && all.TryGetValue(k, out var v)) res[k] = v;
        }
        return res;
    }

    public SetResult Set(string key, string value)
    {
        if (!_schema.Keys.ContainsKey(key)) return new(false, "key not allowed");
        var bad = _schema.Problem(key, value);
        if (bad is not null) return new(false, bad);
        lock (_lock)
        {
            var all = Load(out var error);
            if (error is not null) return new(false, error);
            all[key] = value;
            return Save(all);
        }
    }

    /// <summary>Adds the valid values this file does not have yet, in one write. Existing values win. Writes the file even when there is nothing to add, so the import runs once.</summary>
    public SetResult Import(IReadOnlyDictionary<string, string> values)
    {
        lock (_lock)
        {
            var all = Load(out var error);
            if (error is not null) return new(false, error);
            foreach (var (k, v) in values)
                if (_schema.Keys.ContainsKey(k) && !all.ContainsKey(k) && _schema.Problem(k, v) is null) all[k] = v;
            return Save(all);
        }
    }

    /// <summary>The stored values; empty when the file is missing or unreadable. The error is set only for an unreadable file.</summary>
    private Dictionary<string, string> Load(out string? error)
    {
        error = null;
        var values = new Dictionary<string, string>(StringComparer.Ordinal);
        if (!File.Exists(_path)) return values;
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(_path, Encoding.UTF8));
            if (doc.RootElement.GetProperty("version").GetInt32() != Version) throw new FormatException("version");
            foreach (var p in doc.RootElement.GetProperty("values").EnumerateObject())
                values[p.Name] = p.Value.GetString() ?? throw new FormatException("value");
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or FormatException or InvalidOperationException or IOException)
        {
            values.Clear();
            error = "settings file is unreadable; fix or remove " + _path;
        }
        return values;
    }

    private SetResult Save(Dictionary<string, string> values)
    {
        try { WriteAtomic(values); return new(true); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { return new(false, "could not write settings"); }
    }

    /// <summary>Temp file in the same folder, then replace: a crash leaves the old file or the new one, never half of one.</summary>
    private void WriteAtomic(Dictionary<string, string> values)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_path)!);
        var json = JsonSerializer.Serialize(
            new { version = Version, values = new SortedDictionary<string, string>(values, StringComparer.Ordinal) },
            new JsonSerializerOptions { WriteIndented = true });
        var tmp = _path + ".tmp" + Environment.ProcessId;
        try
        {
            File.WriteAllText(tmp, json, new UTF8Encoding(false));
            File.Move(tmp, _path, overwrite: true);
        }
        finally { if (File.Exists(tmp)) File.Delete(tmp); }
    }
}
