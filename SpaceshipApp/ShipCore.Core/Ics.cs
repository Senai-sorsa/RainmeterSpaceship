using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The skin's calendar feed (Scripts\ShipCore.cs, calendars section) ported as-is: iCalendar parsing with RRULE,
/// EXDATE and RECURRENCE-ID, and the Data\calendar.txt text the skin, JARVIS and the page read. Pure; the host fetches.</summary>
public static class Ics
{
    public sealed record Source(bool On, string Label, string Url);
    public sealed record Event(DateTime StartUtc, DateTime EndUtc, bool AllDay, string Label, string Title);

    /// <summary>The decrypted calendars.dat: "1|0 TAB label TAB url" lines.</summary>
    public static List<Source> Sources(string text)
    {
        var list = new List<Source>();
        foreach (var line in text.Split('\n'))
        {
            var p = line.Split('\t', 3);
            if (p.Length < 3 || p[2].Trim() == "") continue;
            list.Add(new Source(p[0] == "1", p[1], p[2].Trim()));
        }
        return list;
    }

    /// <summary>The URL to fetch, or null: webcal:// is https://, and only http(s) is fetched (no file:// or other schemes).</summary>
    public static Uri? FetchUri(string url)
    {
        if (url.StartsWith("webcal://", StringComparison.OrdinalIgnoreCase)) url = "https://" + url[9..];
        return Uri.TryCreate(url, UriKind.Absolute, out var u) && (u.Scheme == Uri.UriSchemeHttps || u.Scheme == Uri.UriSchemeHttp) ? u : null;
    }

    public static long Unix(DateTime utc) => (long)(utc - DateTime.UnixEpoch).TotalSeconds;

    /// <summary>calendar.txt: T now, C calendars errors, then up to 40 events not yet over, soonest first.</summary>
    public static string Text(List<Event> events, int on, int errors, DateTime nowUtc)
    {
        var sb = new StringBuilder();
        sb.Append("T ").Append(Unix(nowUtc)).Append('\n').Append("C ").Append(on).Append(' ').Append(errors).Append('\n');
        int n = 0;
        foreach (var e in events.OrderBy(e => e.StartUtc))
        {
            if (e.EndUtc < nowUtc) continue;
            sb.Append("E ").Append(Unix(e.StartUtc)).Append('|').Append(Unix(e.EndUtc)).Append('|').Append(e.AllDay ? 1 : 0).Append('|')
              .Append(Clean(e.Label)).Append('|').Append(Clean(e.Title)).Append('\n');
            if (++n >= 40) break;
        }
        return sb.ToString();
    }

    static string Clean(string s) => Regex.Replace(s ?? "", @"[|\r\n\t]", " ").Trim();

    // IANA zone names (what Google uses) -> Windows zone ids; .NET also resolves IANA ids itself, this keeps the skin's mapping first
    static readonly Dictionary<string, string> Zones = new(StringComparer.OrdinalIgnoreCase) {
        { "America/Chicago", "Central Standard Time" }, { "America/New_York", "Eastern Standard Time" },
        { "America/Denver", "Mountain Standard Time" }, { "America/Phoenix", "US Mountain Standard Time" },
        { "America/Los_Angeles", "Pacific Standard Time" }, { "America/Anchorage", "Alaskan Standard Time" },
        { "Pacific/Honolulu", "Hawaiian Standard Time" }, { "America/Detroit", "Eastern Standard Time" },
        { "America/Indiana/Indianapolis", "US Eastern Standard Time" }, { "America/Toronto", "Eastern Standard Time" },
        { "America/Mexico_City", "Central Standard Time (Mexico)" }, { "Europe/London", "GMT Standard Time" },
        { "Europe/Berlin", "W. Europe Standard Time" }, { "Europe/Paris", "Romance Standard Time" },
        { "Asia/Tokyo", "Tokyo Standard Time" }, { "Asia/Kolkata", "India Standard Time" }, { "Africa/Addis_Ababa", "E. Africa Standard Time" },
        { "UTC", "UTC" }, { "Etc/UTC", "UTC" }, { "GMT", "UTC" } };

    static TimeZoneInfo? Zone(string? tzid)
    {
        if (string.IsNullOrEmpty(tzid)) return null;
        tzid = tzid.Trim('"');
        foreach (var id in new[] { Zones.GetValueOrDefault(tzid), tzid })
        {
            if (id is null) continue;
            try { return TimeZoneInfo.FindSystemTimeZoneById(id); } catch (Exception e) when (e is TimeZoneNotFoundException or InvalidTimeZoneException) { }
        }
        return null; // unknown: treat as local time
    }

    sealed class Prop { public string Name = "", Value = ""; public Dictionary<string, string> P = new(StringComparer.OrdinalIgnoreCase); }

    static Prop? ParseLine(string line)
    {
        int colon = -1; bool q = false;
        for (int i = 0; i < line.Length; i++) { if (line[i] == '"') q = !q; else if (line[i] == ':' && !q) { colon = i; break; } }
        if (colon < 0) return null;
        var pr = new Prop { Value = line[(colon + 1)..] };
        var parts = line[..colon].Split(';');
        pr.Name = parts[0].ToUpperInvariant();
        for (int i = 1; i < parts.Length; i++) { int eq = parts[i].IndexOf('='); if (eq > 0) pr.P[parts[i][..eq]] = parts[i][(eq + 1)..]; }
        return pr;
    }

    // the wall-clock time and its zone (null zone + Utc kind for Z times, null zone + Unspecified for floating)
    static DateTime ParseTime(Prop pr, out bool allDay, out TimeZoneInfo? tz)
    {
        allDay = false; tz = null;
        var v = pr.Value.Trim();
        if (v.Length == 8 || pr.P.GetValueOrDefault("VALUE")?.ToUpperInvariant() == "DATE")
        {
            allDay = true;
            return DateTime.ParseExact(v[..8], "yyyyMMdd", CultureInfo.InvariantCulture);
        }
        bool utc = v.EndsWith('Z');
        var dt = DateTime.ParseExact(v.TrimEnd('Z')[..15], "yyyyMMdd'T'HHmmss", CultureInfo.InvariantCulture);
        if (utc) return DateTime.SpecifyKind(dt, DateTimeKind.Utc);
        tz = Zone(pr.P.GetValueOrDefault("TZID"));
        return dt;
    }

    static DateTime ToUtc(DateTime wall, TimeZoneInfo? tz, bool allDay)
    {
        if (wall.Kind == DateTimeKind.Utc) return wall;
        var w = DateTime.SpecifyKind(wall, DateTimeKind.Unspecified);
        if (allDay || tz is null) tz = TimeZoneInfo.Local;
        try { return TimeZoneInfo.ConvertTimeToUtc(w, tz); }
        catch (ArgumentException) { return TimeZoneInfo.ConvertTimeToUtc(w.AddHours(1), tz); } // skipped DST hour
    }

    static string Unescape(string s) => s.Replace("\\n", " ").Replace("\\N", " ").Replace("\\,", ",").Replace("\\;", ";").Replace("\\\\", "\\").Trim();

    sealed class Vevent
    {
        public string Uid = "", Summary = "", Status = ""; public string? RRule;
        public DateTime Start, End; public bool AllDay, HasEnd; public TimeZoneInfo? Tz; public TimeSpan? Duration;
        public List<DateTime> ExUtc = [];
        public DateTime? RecurrenceIdUtc;
    }

    public static List<Event> Parse(string ics, string label, DateTime fromUtc, DateTime toUtc)
    {
        var lines = new List<string>(); // unfold continuation lines
        foreach (var raw in ics.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n'))
        {
            if ((raw.StartsWith(' ') || raw.StartsWith('\t')) && lines.Count > 0) lines[^1] += raw[1..];
            else lines.Add(raw);
        }
        var evs = new List<Vevent>();
        Vevent? cur = null; int depth = 0;
        foreach (var line in lines)
        {
            if (line == "BEGIN:VEVENT") { cur = new Vevent(); depth = 0; continue; }
            if (cur is null) continue;
            if (line.StartsWith("BEGIN:")) { depth++; continue; } // VALARM etc.
            if (line.StartsWith("END:") && depth > 0) { depth--; continue; }
            if (line == "END:VEVENT") { evs.Add(cur); cur = null; continue; }
            if (depth > 0 || ParseLine(line) is not { } pr) continue;
            try
            {
                switch (pr.Name)
                {
                    case "UID": cur.Uid = pr.Value.Trim(); break;
                    case "SUMMARY": cur.Summary = Unescape(pr.Value); break;
                    case "STATUS": cur.Status = pr.Value.Trim().ToUpperInvariant(); break;
                    case "RRULE": cur.RRule = pr.Value.Trim(); break;
                    case "DTSTART": cur.Start = ParseTime(pr, out var ad, out var tz); cur.AllDay = ad; cur.Tz = tz; break;
                    case "DTEND": cur.End = ParseTime(pr, out _, out _); cur.HasEnd = true; break;
                    case "DURATION": cur.Duration = ParseDuration(pr.Value.Trim()); break;
                    case "EXDATE":
                        foreach (var v in pr.Value.Split(','))
                        {
                            var w = ParseTime(new Prop { Value = v, P = pr.P }, out var ad2, out var tz2);
                            cur.ExUtc.Add(ToUtc(w, tz2, ad2));
                        }
                        break;
                    case "RECURRENCE-ID": { var w = ParseTime(pr, out var ad3, out var tz3); cur.RecurrenceIdUtc = ToUtc(w, tz3, ad3); } break;
                }
            }
            catch (Exception e) when (e is FormatException or ArgumentException) { } // a bad line drops that property, as in the skin
        }
        var overridden = new HashSet<string>(); // (UID, original start) -> replaced
        foreach (var e in evs) if (e.RecurrenceIdUtc.HasValue) overridden.Add(e.Uid + "|" + Unix(e.RecurrenceIdUtc.Value));
        var outp = new List<Event>();
        foreach (var e in evs)
        {
            if (e.Start == DateTime.MinValue || e.Status == "CANCELLED") continue;
            var len = e.HasEnd ? e.End - e.Start : e.Duration ?? (e.AllDay ? TimeSpan.FromDays(1) : TimeSpan.Zero);
            if (e.HasEnd && e.End.Kind != e.Start.Kind) len = ToUtc(e.End, e.Tz, e.AllDay) - ToUtc(e.Start, e.Tz, e.AllDay);
            if (len < TimeSpan.Zero) len = TimeSpan.Zero;
            bool recurs = e.RRule is not null && !e.RecurrenceIdUtc.HasValue;
            foreach (var wall in recurs ? Expand(e, fromUtc - len, toUtc) : [e.Start])
            {
                var su = ToUtc(wall, e.Tz, e.AllDay);
                if (recurs && (overridden.Contains(e.Uid + "|" + Unix(su)) || e.ExUtc.Any(x => Math.Abs((x - su).TotalMinutes) < 1))) continue;
                var eu = e.AllDay ? ToUtc(wall + len, e.Tz, true) : su + len;
                if (eu < fromUtc || su > toUtc) continue;
                outp.Add(new Event(su, eu > su ? eu : su.AddMinutes(1), e.AllDay, label, e.Summary == "" ? "(no title)" : e.Summary));
            }
        }
        return outp;
    }

    static TimeSpan ParseDuration(string s)
    {
        var m = Regex.Match(s, @"^([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$");
        if (!m.Success) return TimeSpan.Zero;
        int G(int i) => m.Groups[i].Success ? int.Parse(m.Groups[i].Value, CultureInfo.InvariantCulture) : 0;
        var t = new TimeSpan(G(2) * 7 + G(3), G(4), G(5), G(6));
        return m.Groups[1].Value == "-" ? -t : t;
    }

    static readonly string[] DayCodes = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"];

    // RRULE expansion in the event's own wall-clock time (so a 9:00 class stays 9:00 across DST)
    static List<DateTime> Expand(Vevent e, DateTime fromUtc, DateTime toUtc)
    {
        var res = new List<DateTime>();
        var rule = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var part in e.RRule!.Split(';')) { int eq = part.IndexOf('='); if (eq > 0) rule[part[..eq]] = part[(eq + 1)..]; }
        if (!rule.TryGetValue("FREQ", out var freq)) return res;
        freq = freq.ToUpperInvariant();
        int interval = 1;
        if (rule.TryGetValue("INTERVAL", out var sv)) int.TryParse(sv, out interval);
        if (interval < 1) interval = 1;
        int count = -1; if (rule.TryGetValue("COUNT", out sv)) int.TryParse(sv, out count);
        DateTime? untilUtc = null;
        if (rule.TryGetValue("UNTIL", out sv))
        {
            try { var w = ParseTime(new Prop { Value = sv }, out var ad, out _); untilUtc = w.Kind == DateTimeKind.Utc ? w : ToUtc(ad ? w.AddDays(1).AddSeconds(-1) : w, e.Tz, false); }
            catch (Exception x) when (x is FormatException or ArgumentException) { }
        }
        var byDay = new List<DayOfWeek>(); var byDayNth = new List<KeyValuePair<int, DayOfWeek>>();
        if (rule.TryGetValue("BYDAY", out sv))
            foreach (var d in sv.Split(','))
            {
                var m = Regex.Match(d.Trim().ToUpperInvariant(), @"^([+-]?\d+)?(SU|MO|TU|WE|TH|FR|SA)$");
                if (!m.Success) continue;
                var dow = (DayOfWeek)Array.IndexOf(DayCodes, m.Groups[2].Value);
                if (m.Groups[1].Success) byDayNth.Add(new(int.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture), dow)); else byDay.Add(dow);
            }
        var byMonthDay = new List<int>();
        if (rule.TryGetValue("BYMONTHDAY", out sv)) foreach (var d in sv.Split(',')) if (int.TryParse(d, out var x)) byMonthDay.Add(x);

        var start = e.Start;
        int produced = 0, guard = 0;
        bool Emit(DateTime w)
        {
            if (w < start) return true;
            var u = ToUtc(w, e.Tz, e.AllDay);
            if (untilUtc.HasValue && u > untilUtc.Value) return false;
            produced++;
            if (count > 0 && produced > count) return false;
            if (u >= fromUtc && u <= toUtc) res.Add(w);
            return u <= toUtc; // past the window: stop
        }
        if (freq == "DAILY")
        {
            for (var d = start; guard++ < 5000; d = d.AddDays(interval))
            {
                if (byDay.Count > 0 && !byDay.Contains(d.DayOfWeek)) continue;
                if (!Emit(d)) break;
            }
        }
        else if (freq == "WEEKLY")
        {
            var days = byDay.Count > 0 ? byDay : [start.DayOfWeek];
            var weekStart = start.Date.AddDays(-(int)start.DayOfWeek); // Sunday-based weeks
            bool go = true;
            for (int w = 0; go && guard++ < 3000; w += interval)
                for (int di = 0; di < 7 && go; di++)
                {
                    var d = weekStart.AddDays(w * 7 + di);
                    if (days.Contains(d.DayOfWeek)) go = Emit(d + start.TimeOfDay);
                }
        }
        else if (freq == "MONTHLY")
        {
            bool go = true;
            for (int mo = 0; go && guard++ < 600; mo += interval)
            {
                var m0 = new DateTime(start.Year, start.Month, 1).AddMonths(mo);
                var cands = new List<DateTime>();
                int dim = DateTime.DaysInMonth(m0.Year, m0.Month);
                if (byDayNth.Count > 0)
                {
                    foreach (var kv in byDayNth)
                    {
                        var hits = Enumerable.Range(1, dim).Select(d => new DateTime(m0.Year, m0.Month, d)).Where(dd => dd.DayOfWeek == kv.Value).ToList();
                        int idx = kv.Key > 0 ? kv.Key - 1 : hits.Count + kv.Key;
                        if (idx >= 0 && idx < hits.Count) cands.Add(hits[idx]);
                    }
                }
                else
                {
                    foreach (var md in byMonthDay.Count > 0 ? byMonthDay : [start.Day]) { int d = md > 0 ? md : dim + md + 1; if (d >= 1 && d <= dim) cands.Add(new DateTime(m0.Year, m0.Month, d)); }
                }
                cands.Sort();
                foreach (var d in cands) { if (!go) break; go = Emit(d + start.TimeOfDay); }
            }
        }
        else if (freq == "YEARLY")
        {
            for (int y = 0; guard++ < 200; y += interval)
            {
                int yr = start.Year + y;
                if (start.Month == 2 && start.Day == 29 && !DateTime.IsLeapYear(yr)) continue;
                if (!Emit(new DateTime(yr, start.Month, start.Day) + start.TimeOfDay)) break;
            }
        }
        return res;
    }
}
