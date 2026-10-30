using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The apps' own icons: the queue Scripts\app-icons.ps1 reads (apps.lua A.writeIconQueue over A.loadAll's apps) and the
/// icons.list message that tells the page which icon files the host serves.</summary>
public static class AppIcons
{
    static readonly Regex Name = new(@"^[A-Za-z0-9_.-]{1,70}$");
    // apps.ts JUNK: Start-menu entries that are not apps
    static readonly string[] Junk = ["uninstall", "readme", "read me", "help", "documentation", "website", "release notes", "license",
        "manual", "changelog", "what's new", "support", "faq", "troubleshoot", "repair"];

    /// <summary>icons.list: the file stems of Icons\*.png that are safe names, sorted, and a version (the newest write time).</summary>
    public static string ListJson(IEnumerable<string> stems, long v) =>
        JsonSerializer.Serialize(new { type = "icons.list", ids = stems.Where(s => Name.IsMatch(s)).Distinct(StringComparer.Ordinal).Order(StringComparer.Ordinal), v });

    /// <summary>IconQueue.txt lines ("id|path"): catalog apps by their launch plan (shell:AppsFolder or a local file), then every
    /// other Start-menu app under the s_ id the page gives it (apps.ts addInstalled). cmd: targets and unsafe ids or paths are left out.</summary>
    public static List<string> Queue(string ini, IReadOnlyList<string[]> start, Func<string, bool> exists, Func<string, string> expand)
    {
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var raw in ini.Split('\n'))
        {
            var line = raw.Trim();
            if (line.StartsWith("[App.", StringComparison.Ordinal) && line.EndsWith(']')) ids.Add(line[5..^1]);
        }
        var lines = new List<string>();
        var claimed = new HashSet<string>(StringComparer.Ordinal);
        void Add(string id, string path)
        {
            if (AppLaunch.Id.IsMatch(id) && path.Length > 0 && !path.Any(c => c == '|' || char.IsControl(c))) lines.Add($"{id}|{path}");
        }
        foreach (var id in ids.Order(StringComparer.Ordinal))
        {
            var plan = AppLaunch.Plan(ini, start, id, exists, expand);
            if (plan is null) continue;
            if (plan.File == "explorer.exe" && plan.Args.StartsWith(@"shell:AppsFolder\", StringComparison.Ordinal)) { claimed.Add(plan.Args[17..]); Add(id, plan.Args); }
            else if (Path.IsPathFullyQualified(plan.File) && !plan.File.StartsWith(@"\\", StringComparison.Ordinal)) Add(id, plan.File);
        }
        var used = new HashSet<string>(StringComparer.Ordinal);
        foreach (var e in start)
        {
            var lname = e[0].ToLowerInvariant();
            if (Junk.Any(j => lname.Contains(j, StringComparison.Ordinal)) || !used.Add(e[1]) || claimed.Contains(e[1])) continue;
            var sb = new StringBuilder("s_");
            foreach (var c in lname) if (c is >= 'a' and <= 'z' or >= '0' and <= '9') sb.Append(c);
            var b = sb.ToString(); var sid = b = b[..Math.Min(b.Length, 42)];
            for (var n = 2; ids.Contains(sid); n++) sid = b + n;
            ids.Add(sid);
            if (AppLaunch.AppId.IsMatch(e[1])) Add(sid, $@"shell:AppsFolder\{e[1]}");
        }
        return lines;
    }
}
