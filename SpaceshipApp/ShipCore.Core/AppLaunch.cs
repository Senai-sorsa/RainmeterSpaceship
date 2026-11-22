using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>What app.launch runs: a file (opened through the shell, so .lnk works) or explorer with shell:AppsFolder, plus the
/// Proc to bring to the front when it already has a window.</summary>
public sealed record LaunchPlan(string File, string Args, string Proc);

/// <summary>apps.lua A.resolve and A.launch, from the host's own copy of Apps.ini: the page names an app id and nothing else, so
/// it can never choose what runs. cmd: targets run only as a bare exe name or an ms-settings: page.</summary>
public static class AppLaunch
{
    public static readonly Regex Id = new(@"^[A-Za-z0-9_.-]{1,64}$");
    static readonly Regex BareExe = new(@"^[A-Za-z0-9_.-]{1,64}\.exe$", RegexOptions.IgnoreCase);
    static readonly Regex Settings = new(@"^ms-settings:[a-z0-9-]{0,64}$");
    public static readonly Regex AppId = new(@"^[A-Za-z0-9_.!{}\\ ~-]{1,256}$");

    /// <param name="start">Data\StartApps.txt as [name, AppID] pairs (AppsFeed reads it the same way).</param>
    public static LaunchPlan? Plan(string ini, IReadOnlyList<string[]> start, string id, Func<string, bool> exists, Func<string, string> expand)
    {
        if (!Id.IsMatch(id)) return null;
        string? targets = null, proc = "";
        var inApp = false;
        foreach (var raw in ini.Split('\n'))
        {
            var line = raw.Trim();
            if (line.StartsWith('[') && line.EndsWith(']')) { inApp = line == $"[App.{id}]"; continue; }
            if (!inApp) continue;
            var eq = line.IndexOf('=');
            if (eq <= 0 || line.StartsWith(';')) continue;
            var key = line[..eq].Trim();
            if (key == "Target") targets = line[(eq + 1)..].Trim();
            else if (key == "Proc") proc = line[(eq + 1)..].Trim();
        }
        if (targets is null) return null;
        foreach (var part in targets.Split("||"))
        {
            var t = part.Trim();
            if (t.Length == 0) continue;
            if (t.StartsWith("start:", StringComparison.Ordinal))
            {
                var e = FindStart(start, t[6..].Trim());
                if (e is not null) return AppId.IsMatch(e) ? new("explorer.exe", $"shell:AppsFolder\\{e}", proc) : null;
            }
            else if (t.StartsWith("cmd:", StringComparison.Ordinal))
            {
                var c = t[4..].Trim();
                return BareExe.IsMatch(c) || Settings.IsMatch(c) ? new(c, "", proc) : null;
            }
            else
            {
                string p;
                try { p = expand(t); if (!exists(p)) continue; }
                catch (Exception ex) when (ex is ArgumentException or IOException or UnauthorizedAccessException or NotSupportedException) { continue; }
                return new(p, "", proc.Length > 0 ? proc : Path.GetFileName(p).EndsWith(".exe", StringComparison.OrdinalIgnoreCase) ? Path.GetFileName(p) : "");
            }
        }
        return null;
    }

    // apps.lua findStart: an exact name, else the shortest name starting with q, else the shortest containing it (no case)
    static string? FindStart(IReadOnlyList<string[]> start, string q)
    {
        q = q.ToLowerInvariant();
        foreach (var e in start) if (e[0].ToLowerInvariant() == q) return e[1];
        foreach (var contains in new[] { false, true })
        {
            string[]? best = null;
            foreach (var e in start)
            {
                var n = e[0].ToLowerInvariant();
                if ((contains ? n.Contains(q, StringComparison.Ordinal) : n.StartsWith(q, StringComparison.Ordinal)) && (best is null || e[0].Length < best[0].Length)) best = e;
            }
            if (best is not null) return best[1];
        }
        return null;
    }
}
