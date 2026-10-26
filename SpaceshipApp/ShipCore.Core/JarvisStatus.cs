using System.Text.Json;

namespace ShipCore.Core;

/// <summary>Reads JARVIS's Data\jarvis.txt (T, STATE, LEVEL, SAY, ERR lines) into the page's jarvis.update message, as Scripts\jarvis.lua readState does.</summary>
public static class JarvisStatus
{
    public const int MaxText = 400;
    const long StaleSeconds = 8;
    static readonly HashSet<string> States = ["idle", "listening", "thinking", "speaking"];

    /// <param name="text">The file's text, or null when it is missing. Untrusted: unknown states become idle, text is trimmed and stripped of control characters.</param>
    public static string ToJson(string? text, long nowS)
    {
        string state = "idle", say = "", err = "";
        double level = 0;
        long t = 0;
        foreach (var line in (text ?? "").Split('\n'))
        {
            var l = line.TrimEnd('\r');
            var sp = l.IndexOf(' ');
            var (k, v) = sp < 0 ? (l, "") : (l[..sp], l[(sp + 1)..]);
            switch (k)
            {
                case "T": long.TryParse(v.Split('.')[0], out t); break;
                case "STATE": state = v; break;
                case "LEVEL": if (!double.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out level) || !double.IsFinite(level)) level = 0; break;
                case "SAY": say = Clean(v); break;
                case "ERR": err = Clean(v); break;
            }
        }
        if (!States.Contains(state)) state = "idle";
        if (text is null || nowS - t > StaleSeconds) { state = "offline"; level = 0; }
        return JsonSerializer.Serialize(new { type = "jarvis.update", state, level = Math.Round(Math.Clamp(level, 0, 1), 3), say, err });
    }

    static string Clean(string s)
    {
        var c = new string(s.Where(ch => !char.IsControl(ch)).ToArray());
        return c.Length > MaxText ? c[..MaxText] : c;
    }
}
