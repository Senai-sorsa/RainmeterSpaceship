using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>Shape check for messages from the WebView (untrusted). Same verdicts as src/host/contract.ts; contract/fixtures/ui-to-host.json is the shared test.</summary>
public static class Protocol
{
    private static readonly Regex Key = new(@"^[A-Za-z][A-Za-z0-9_]{0,63}$", RegexOptions.Compiled);
    private static readonly HashSet<string> Flows = new() { "gmail", "calendars", "obsidian" };
    // status.refresh kinds: the status scripts (StatusScripts.Kinds), the mail check and the calendar fetch
    public static readonly HashSet<string> RefreshKinds = new() { "llt", "upkeep", "dev", "mail", "calendar" };
    // target.open names: each maps to one fixed page or program in the host (Program.OpenTarget), never to text from the UI
    public static readonly HashSet<string> Targets = new() { "taskmgr", "taskperf", "todo", "sound", "display", "power", "mute", "prev", "playpause", "next",
        "terminal", "powershell", "about", "outlookcal", "gcal", "gmail", "update", "defender", "network", "wifi", "spx", "ollama", "tailscale", "drive", "battery", "audionext", "jarvislog" };

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
            case "dial.set": return DialSetProblem(m);
            case "hit.regions": return HitRegionsProblem(m);
            case "app.launch": return Str(m, "id", out var app) && AppLaunch.Id.IsMatch(app) ? null : "bad app id";
            case "target.open": return Str(m, "what", out var w) && Targets.Contains(w) ? null : "bad target";
            case "llt.set":
                if (!Str(m, "feature", out var lf) || Array.IndexOf(LltGate.Features, lf) < 0) return "bad feature";
                if (!Str(m, "value", out var lv) || !LltGate.Word.IsMatch(lv)) return "bad value";
                return m.TryGetProperty("id", out var lid) && lid.ValueKind == JsonValueKind.Number && lid.TryGetInt64(out var ln) && ln >= 0
                    && lid.GetRawText().IndexOfAny(new[] { '.', 'e', 'E' }) < 0 ? null : "bad id";
            // the block to read again (status_block.lua / console.lua right-click); no kind = the console's status.ps1
            case "status.refresh": return !m.TryGetProperty("kind", out _) || Str(m, "kind", out var rk) && RefreshKinds.Contains(rk) ? null : "bad kind";
            case "speed.run": return null;
            default: return "unknown type";
        }
    }

    // Up to 64 [x, y, w, h] whole numbers in window pixels; a rect is never empty and stays inside +-16384.
    private static string? HitRegionsProblem(JsonElement m)
    {
        if (!m.TryGetProperty("keyboard", out var k) || k.ValueKind is not (JsonValueKind.True or JsonValueKind.False)) return "bad keyboard";
        if (!m.TryGetProperty("rects", out var rs) || rs.ValueKind != JsonValueKind.Array || rs.GetArrayLength() > HitRegions.MaxRects) return "bad rects";
        foreach (var r in rs.EnumerateArray())
        {
            if (r.ValueKind != JsonValueKind.Array || r.GetArrayLength() != 4) return "bad rects";
            var n = new int[4];
            for (var i = 0; i < 4; i++)
                if (r[i].ValueKind != JsonValueKind.Number || r[i].GetRawText().IndexOfAny(new[] { '.', 'e', 'E' }) >= 0 || !r[i].TryGetInt32(out n[i])) return "bad rects";
            if (n[0] < -HitRegions.MaxCoord || n[1] < -HitRegions.MaxCoord || n[0] > HitRegions.MaxCoord || n[1] > HitRegions.MaxCoord
                || n[2] < 1 || n[3] < 1 || n[2] > HitRegions.MaxCoord || n[3] > HitRegions.MaxCoord) return "bad rects";
        }
        return null;
    }

    private static readonly HashSet<string> DialControls = new() { "brightness", "volume", "mic", "power", "refresh" };

    // Shape only: a percent is a whole number 0..100, a power mode and a refresh rate are names from DialGate. DialGate checks them again.
    private static string? DialSetProblem(JsonElement m)
    {
        if (!Str(m, "control", out var c) || !DialControls.Contains(c)) return "bad control";
        if (!m.TryGetProperty("id", out var id) || id.ValueKind != JsonValueKind.Number || !id.TryGetInt64(out var n) || n < 0
            || id.GetRawText().IndexOfAny(new[] { '.', 'e', 'E' }) >= 0) return "bad id";
        if (!m.TryGetProperty("value", out var v)) return "bad value";
        return c switch
        {
            "power" => v.ValueKind == JsonValueKind.String && Array.IndexOf(DialGate.Modes, v.GetString()) >= 0 ? null : "bad value",
            "refresh" => v.ValueKind == JsonValueKind.String && Array.IndexOf(DialGate.Rates, v.GetString()) >= 0 ? null : "bad value",
            _ => v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out var p) && p >= 0 && p <= 100 ? null : "bad value",
        };
    }

    private static bool Str(JsonElement o, string name, out string value)
    {
        value = "";
        if (!o.TryGetProperty(name, out var e) || e.ValueKind != JsonValueKind.String) return false;
        value = e.GetString()!;
        return true;
    }
}
