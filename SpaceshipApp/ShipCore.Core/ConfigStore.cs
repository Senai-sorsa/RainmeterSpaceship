using System.Text;

namespace ShipCore.Core;

public sealed record SetResult(bool Ok, string? Error = null);

/// <summary>Reads and writes single Key=Value lines of the skin's Settings.inc / State.inc / Offsets.inc. Only keys in the schema, only valid values, atomic replace, everything else in the file kept byte for byte.</summary>
public sealed class ConfigStore
{
    private readonly string _dir;
    private readonly ConfigSchema _schema;
    private readonly object _lock = new();

    /// <param name="resourcesDir">The skin's @Resources folder.</param>
    public ConfigStore(string resourcesDir, ConfigSchema schema) { _dir = resourcesDir; _schema = schema; }

    private string PathOf(KeySpec s) => Path.Combine(_dir, s.File);

    public Dictionary<string, string> Get(IEnumerable<string> keys)
    {
        var res = new Dictionary<string, string>();
        lock (_lock)
        {
            var cache = new Dictionary<string, Dictionary<string, string>>();
            foreach (var k in keys)
            {
                if (!_schema.Keys.TryGetValue(k, out var s)) continue;
                if (!cache.TryGetValue(s.File, out var vals)) cache[s.File] = vals = Parse(ReadFile(s));
                if (vals.TryGetValue(k, out var v)) res[k] = v;
            }
        }
        return res;
    }

    public SetResult Set(string key, string value)
    {
        if (!_schema.Keys.TryGetValue(key, out var s)) return new(false, "key not allowed");
        var bad = _schema.Problem(key, value);
        if (bad is not null) return new(false, bad);
        lock (_lock)
        {
            try
            {
                var path = PathOf(s);
                var text = ReadFile(s);
                var nl = text.Contains("\r\n") ? "\r\n" : "\n";
                var lines = text.Length == 0 ? new List<string>() : text.Split(nl).ToList();
                var prefix = key + "=";
                var i = lines.FindLastIndex(l => l.StartsWith(prefix, StringComparison.Ordinal));
                if (i >= 0) lines[i] = prefix + value;
                else
                {
                    // absent (optional key): add it to the end of [Variables], or to the file end when there is no such section
                    var at = lines.FindIndex(l => l.Trim() == "[Variables]");
                    if (at < 0) { lines.Add(prefix + value); }
                    else
                    {
                        var end = lines.FindIndex(at + 1, l => l.TrimStart().StartsWith('[')); // next section
                        end = end < 0 ? lines.Count : end;
                        while (end > at + 1 && lines[end - 1].Trim() == "") end--;
                        lines.Insert(end, prefix + value);
                    }
                }
                WriteAtomic(path, string.Join(nl, lines));
                return new(true);
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException)
            {
                return new(false, "could not write " + s.File);
            }
        }
    }

    private string ReadFile(KeySpec s) => File.Exists(PathOf(s)) ? File.ReadAllText(PathOf(s), new UTF8Encoding(false)) : "";

    private static Dictionary<string, string> Parse(string text)
    {
        var d = new Dictionary<string, string>();
        foreach (var raw in text.Split('\n'))
        {
            var l = raw.TrimEnd('\r').TrimStart('﻿');
            if (l.Length == 0 || l[0] is ';' or '[') continue;
            var eq = l.IndexOf('=');
            if (eq > 0) d[l[..eq].Trim()] = l[(eq + 1)..]; // later duplicate wins, like Rainmeter
        }
        return d;
    }

    /// <summary>Temp file in the same folder, then replace: a crash leaves the old file or the new one, never half of one. The BOM, if any, is kept.</summary>
    private static void WriteAtomic(string path, string text)
    {
        var bom = File.Exists(path) && File.ReadAllBytes(path) is [0xEF, 0xBB, 0xBF, ..];
        var tmp = path + ".tmp" + Environment.ProcessId;
        try
        {
            File.WriteAllText(tmp, text, new UTF8Encoding(bom));
            File.Move(tmp, path, overwrite: true);
        }
        finally { if (File.Exists(tmp)) File.Delete(tmp); }
    }
}
