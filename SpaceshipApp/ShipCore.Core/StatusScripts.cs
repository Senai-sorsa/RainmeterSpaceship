using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The skin's query-only status scripts (Scripts\upkeep.ps1, Scripts\dev.ps1, Scripts\status.ps1), run on the skin's schedule, and the page message made from their one-line output.</summary>
public static class StatusScripts
{
    /// <summary>Script file, seconds between runs (status_block.lua: upkeep 3600, dev 120).</summary>
    public static readonly IReadOnlyDictionary<string, (string Script, int PeriodS)> Kinds = new Dictionary<string, (string, int)>
    {
        ["upkeep"] = ("upkeep.ps1", 3600),
        ["dev"] = ("dev.ps1", 120),
        // console.lua runs status.ps1 every 60 s; 120 s here, since the app does not switch modes itself (one PowerShell start fewer a minute)
        ["llt"] = ("status.ps1", 120),
    };

    static readonly Regex Word = new(@"^[A-Z0-9 ._-]{1,40}$");
    static readonly Regex Value = new(@"^[a-z0-9 ._-]{0,40}$");

    /// <summary>status.update for the script's last output line, or null if it is not the expected shape. Counts are -1 when unknown.</summary>
    public static string? ToJson(string kind, string? output)
    {
        if (kind == "llt") return LltJson(output);
        var line = (output ?? "").Split('\n').Select(l => l.Trim()).LastOrDefault(l => l != "") ?? "";
        var p = line.Split('|');
        int N(int i) => i < p.Length && int.TryParse(p[i], out var v) && v >= -1 && v < 100000 ? v : -1;
        string? W(int i) => i < p.Length && Word.IsMatch(p[i]) ? p[i] : null;
        switch (kind)
        {
            case "upkeep" when p.Length is 3 or 4:
                // updates|upgrades|NONE, or updates|upgrades|AV NAME|ON|OFF
                var avOn = p.Length == 4 ? p[3] == "ON" : (bool?)null;
                return JsonSerializer.Serialize(new { type = "status.update", kind, updates = N(0), upgrades = N(1), av = W(2), avOn });
            case "dev" when p.Length == 4:
                return JsonSerializer.Serialize(new { type = "status.update", kind, wsl = N(0), llm = N(1), tailscale = W(2), docker = N(3) });
            default:
                return null;
        }
    }

    // status.ps1: one key=value per line, lower-cased as console.lua's OnStatus does; an odd value becomes "" (unknown). It always prints dgpu.
    static string? LltJson(string? output)
    {
        var kv = new Dictionary<string, string>();
        foreach (var line in (output ?? "").Split('\n'))
            if (line.Trim().Split('=', 2) is [var k, var v]) kv[k] = v.ToLowerInvariant();
        if (!kv.ContainsKey("dgpu")) return null;
        string V(string k) => kv.TryGetValue(k, out var v) && Value.IsMatch(v) ? v : "";
        return JsonSerializer.Serialize(new { type = "status.update", kind = "llt", hybrid = V("hybrid"), power = V("power"), refresh = V("refresh"), battery = V("battery"), dgpu = V("dgpu") });
    }
}
