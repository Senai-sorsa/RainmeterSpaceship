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
        string state = "idle", say = "", err = "", pop = "";
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
                case "POP": pop = Clean(v); break; // "<n> open|close": JARVIS asking for the log pop-up
            }
        }
        if (!States.Contains(state)) state = "idle";
        if (text is null || nowS - t > StaleSeconds) { state = "offline"; level = 0; }
        return JsonSerializer.Serialize(new { type = "jarvis.update", state, level = Math.Round(Math.Clamp(level, 0, 1), 3), say, err, pop });
    }

    public const int MaxLog = 65536;

    /// <summary>The log pop-up's jarvis.log message (jarvislog.lua): the end of Data\jarvis_log.txt, the reply being written (jarvis_live.txt),
    /// and whether jarvis_env.txt says MUTED 1. Missing files read as "". Control characters other than newlines are dropped.</summary>
    public static string LogJson(string? log, string? live, string? env) => JsonSerializer.Serialize(new
    {
        type = "jarvis.log", log = Lines(log), live = Lines(live), muted = (env ?? "").Contains("MUTED 1", StringComparison.Ordinal),
    });

    static string Lines(string? s) => new((s ?? "").Where(ch => ch == '\n' || !char.IsControl(ch)).ToArray());

    /// <summary>The last <paramref name="cap"/> bytes of a UTF-8 file from the start of a whole line (the log only grows; the window shows its end).</summary>
    public static string Tail(Stream f, int cap = MaxLog)
    {
        if (f.Length > cap) f.Seek(-cap, SeekOrigin.End);
        var text = new StreamReader(f, System.Text.Encoding.UTF8).ReadToEnd();
        if (f.Length <= cap) return text;
        var nl = text.IndexOf('\n');
        return nl < 0 ? "" : text[(nl + 1)..];
    }

    static string Clean(string s)
    {
        var c = new string(s.Where(ch => !char.IsControl(ch)).ToArray());
        return c.Length > MaxText ? c[..MaxText] : c;
    }
}
