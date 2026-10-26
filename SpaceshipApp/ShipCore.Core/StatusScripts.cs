using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The skin's query-only status scripts (Scripts\upkeep.ps1, Scripts\dev.ps1), run on the skin's schedule, and the page message made from their one-line output.</summary>
public static class StatusScripts
{
    /// <summary>Script file, seconds between runs (status_block.lua: upkeep 3600, dev 120).</summary>
    public static readonly IReadOnlyDictionary<string, (string Script, int PeriodS)> Kinds = new Dictionary<string, (string, int)>
    {
        ["upkeep"] = ("upkeep.ps1", 3600),
        ["dev"] = ("dev.ps1", 120),
    };

    static readonly Regex Word = new(@"^[A-Z0-9 ._-]{1,40}$");

    /// <summary>status.update for the script's last output line, or null if it is not the expected shape. Counts are -1 when unknown.</summary>
    public static string? ToJson(string kind, string? output)
    {
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
}
