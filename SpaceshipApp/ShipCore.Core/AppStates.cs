using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The apps.state message: for each Apps.ini Proc, 2 = it has an app window, 1 = running without one (tray, service),
/// 0 = not running. lib.lua's appState over the skin helper's windows.txt, sent only when it changes.</summary>
public static class AppStates
{
    static readonly Regex Exe = new(@"^[a-z0-9 _.()+-]{1,64}\.exe$");

    /// <summary>The Proc= names of Apps.ini, lower-cased with .exe, as windows.txt writes them. Odd names are dropped.</summary>
    public static IReadOnlyList<string> Procs(string ini) => ini.Split('\n')
        .Select(l => l.Trim())
        .Where(l => l.StartsWith("Proc=", StringComparison.Ordinal))
        .Select(l => l[5..].Trim().ToLowerInvariant())
        .Select(p => p.EndsWith(".exe", StringComparison.Ordinal) ? p : p + ".exe")
        .Where(p => Exe.IsMatch(p)).Distinct().ToList();

    public static string ToJson(IEnumerable<string> procs, IReadOnlySet<string> windows, IReadOnlySet<string> running) =>
        JsonSerializer.Serialize(new { type = "apps.state", states = procs.ToDictionary(p => p, p => windows.Contains(p) ? 2 : running.Contains(p) ? 1 : 0) });
}
