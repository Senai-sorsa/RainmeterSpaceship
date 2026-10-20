using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

public sealed record KeySpec(string Key, string File, string Kind, double Min, double Max, double Step,
    IReadOnlyList<string> Options, string? Pattern, int MaxLen, string Default);

/// <summary>What the host may write, loaded from contract/config-keys.json (generated from the UI registry). Anything not listed is refused.</summary>
public sealed class ConfigSchema
{
    private readonly Dictionary<string, KeySpec> _keys;
    public IReadOnlySet<string> Actions { get; }
    public IReadOnlyDictionary<string, KeySpec> Keys => _keys;

    private ConfigSchema(Dictionary<string, KeySpec> keys, HashSet<string> actions) { _keys = keys; Actions = actions; }

    public static ConfigSchema Parse(string json)
    {
        using var doc = JsonDocument.Parse(json);
        var keys = new Dictionary<string, KeySpec>(StringComparer.Ordinal);
        foreach (var k in doc.RootElement.GetProperty("keys").EnumerateArray())
        {
            var c = k.GetProperty("control");
            var kind = c.GetProperty("kind").GetString()!;
            double N(string n) => c.TryGetProperty(n, out var v) ? v.GetDouble() : 0;
            var opts = c.TryGetProperty("options", out var o)
                ? o.EnumerateArray().Select(x => x.GetProperty("value").GetString()!).ToList() : new List<string>();
            var key = k.GetProperty("key").GetString()!;
            keys[key] = new KeySpec(key, k.GetProperty("file").GetString()!, kind, N("min"), N("max"), N("step"), opts,
                c.TryGetProperty("pattern", out var p) ? p.GetString() : null, (int)N("max"), k.GetProperty("default").GetString()!);
        }
        var actions = doc.RootElement.GetProperty("actions").EnumerateArray().Select(a => a.GetString()!).ToHashSet();
        return new ConfigSchema(keys, actions);
    }

    /// <summary>Null when the value is valid for the key's control; otherwise the reason. Mirrors validate() in the UI store.</summary>
    public string? Problem(string key, string value)
    {
        if (!_keys.TryGetValue(key, out var s)) return "key not allowed";
        // Never let a value break the .inc line it is written into, whatever the control says.
        if (value.Any(ch => ch < ' ' || ch == '\x7f')) return "control characters not allowed";
        switch (s.Kind)
        {
            case "toggle": return value is "0" or "1" ? null : "must be 0 or 1";
            case "select": return s.Options.Contains(value) ? null : "not an allowed option";
            case "slider":
            {
                if (!Regex.IsMatch(value, @"^-?[0-9]+(\.[0-9]+)?$") ||
                    !double.TryParse(value, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var n))
                    return "must be a number";
                if (n < s.Min || n > s.Max) return $"must be from {s.Min} to {s.Max}";
                var q = (n - s.Min) / s.Step;
                return Math.Abs(q - Math.Round(q)) < 1e-6 ? null : $"must step by {s.Step}";
            }
            case "text":
                if (value.Length > s.MaxLen) return $"at most {s.MaxLen} characters";
                return s.Pattern is not null && Regex.IsMatch(value, s.Pattern, RegexOptions.None, TimeSpan.FromMilliseconds(100)) ? null : "contains characters that are not allowed";
            case "color":
                if (value == "" && s.Default == "") return null; // empty = follow the theme
                return Regex.IsMatch(value, @"^[0-9]{1,3},[0-9]{1,3},[0-9]{1,3}(,[0-9]{1,3})?$") && value.Split(',').All(p => int.Parse(p) <= 255) ? null : "must be r,g,b or r,g,b,a (0-255)";
            default: return "not a setting";
        }
    }
}
