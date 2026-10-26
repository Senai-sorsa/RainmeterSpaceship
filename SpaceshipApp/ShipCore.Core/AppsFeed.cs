using System.Text.Json;

namespace ShipCore.Core;

/// <summary>The apps.catalog message: Apps.ini as text, the Start-menu list (Data\StartApps.txt, Name|AppID lines) and which
/// file targets exist, so the page's catalog (apps.ts, a port of apps.lua) resolves the same targets as the skin. Read-only.</summary>
public static class AppsFeed
{
    /// <summary>Data\StartApps.txt (Name|AppID lines) as [name, AppID] pairs.</summary>
    public static List<string[]> Start(string startText)
    {
        var start = new List<string[]>();
        foreach (var line in startText.Split('\n'))
        {
            var bar = line.IndexOf('|');
            if (bar > 0) start.Add([line[..bar].Trim(), line[(bar + 1)..].Trim()]);
        }
        return start;
    }

    public static string ToJson(string ini, string startText, Func<string, bool> exists, Func<string, string> expand)
    {
        var start = Start(startText);
        var found = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var raw in ini.Split('\n'))
        {
            var line = raw.Trim();
            if (!line.StartsWith("Target=", StringComparison.Ordinal)) continue;
            foreach (var part in line[7..].Split("||"))
            {
                var t = part.Trim();
                if (t.Length == 0 || t.StartsWith("start:", StringComparison.Ordinal) || t.StartsWith("cmd:", StringComparison.Ordinal)) continue;
                // the page matches the target text as written in Apps.ini; %ProgramFiles% and the like are expanded only for the check
                try { if (exists(expand(t))) found.Add(t); } catch (Exception e) when (e is ArgumentException or IOException or UnauthorizedAccessException or NotSupportedException) { }
            }
        }
        return JsonSerializer.Serialize(new { type = "apps.catalog", ini, start, exists = found });
    }
}
