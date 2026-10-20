using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>Shape check for messages from the WebView (untrusted). Same verdicts as src/host/contract.ts; contract/fixtures/ui-to-host.json is the shared test.</summary>
public static class Protocol
{
    private static readonly Regex Key = new(@"^[A-Za-z][A-Za-z0-9_]{0,63}$", RegexOptions.Compiled);
    private static readonly HashSet<string> Flows = new() { "gmail", "calendars", "obsidian" };

    public static string? Problem(string json, ConfigSchema schema)
    {
        try { using var d = JsonDocument.Parse(json); return Problem(d.RootElement, schema); }
        catch (JsonException) { return "not json"; }
        catch (InvalidOperationException) { return "not a message"; } // e.g. a lone surrogate in a string
    }

    public static string? Problem(JsonElement m, ConfigSchema schema)
    {
        try { return Check(m, schema); }
        catch (Exception e) when (e is InvalidOperationException or FormatException or OverflowException) { return "not a message"; }
    }

    private static string? Check(JsonElement m, ConfigSchema schema)
    {
        if (m.ValueKind != JsonValueKind.Object || !Str(m, "type", out var type)) return "not a message";
        switch (type)
        {
            case "config.get":
                if (!m.TryGetProperty("keys", out var ks) || ks.ValueKind != JsonValueKind.Array || ks.GetArrayLength() > 500) return "bad keys";
                return ks.EnumerateArray().All(k => k.ValueKind == JsonValueKind.String && Key.IsMatch(k.GetString()!)) ? null : "bad keys";
            case "config.set":
                if (!Str(m, "key", out var key) || !Key.IsMatch(key)) return "bad key";
                if (!Str(m, "value", out var v) || v.Length > 256 || v.Any(c => c < ' ' || c == '\x7f')) return "bad value";
                return m.TryGetProperty("id", out var id) && id.ValueKind == JsonValueKind.Number && id.TryGetInt64(out var n) && n >= 0
                    && id.GetRawText().IndexOfAny(new[] { '.', 'e', 'E' }) < 0 ? null : "bad id";
            case "setup.get": case "aboutme.get": return null;
            case "setup.finish": return Str(m, "mode", out var mode) && mode is "defaults" or "custom" ? null : "bad mode";
            case "aboutme.set":
                return Str(m, "text", out var t) && t.Length <= 4000 && !t.Any(c => (c < ' ' && c is not ('\t' or '\n' or '\r')) || c == '\x7f') ? null : "bad text";
            case "action": return Str(m, "id", out var a) && schema.Actions.Contains(a) ? null : "action not allowed";
            case "flow.open": return Str(m, "flow", out var f) && Flows.Contains(f) ? null : "bad flow";
            default: return "unknown type";
        }
    }

    private static bool Str(JsonElement o, string name, out string value)
    {
        value = "";
        if (!o.TryGetProperty(name, out var e) || e.ValueKind != JsonValueKind.String) return false;
        value = e.GetString()!;
        return true;
    }
}
