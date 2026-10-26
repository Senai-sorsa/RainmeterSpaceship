using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The reticle's to-do mode (target.lua parseTodos): open "- [ ]" items of the ObsidianTodo note, soonest due first.</summary>
public static class TodoNote
{
    public const int MaxBytes = 1 << 20, MaxItems = 4, MaxText = 120;
    static readonly Regex Item = new(@"^\s*[-*+]\s+\[(.)\]\s+(.*)$");
    static readonly Regex[] DueDate = [new(@"📅\s*([0-9]{4})-([0-9]{2})-([0-9]{2})"), new(@"due::\s*([0-9]{4})-([0-9]{2})-([0-9]{2})")];
    static readonly Regex[] DueTime = [new(@"@([0-9]{1,2}):([0-9]{2})"), new(@"⏰\s*([0-9]{1,2}):([0-9]{2})"), new(@"due::\s*[0-9]{4}-[0-9]{2}-[0-9]{2}[T ]([0-9]{2}):([0-9]{2})")];
    // display text: drop Dataview fields, emoji with their dates, task-plugin symbols, @times and tags
    static readonly Regex[] Strip = [new(@"\[[A-Za-z0-9_-]+::[^\]]*\]"), new(@"[\uD800-\uDBFF][\uDC00-\uDFFF]\s*[0-9-]*"), new(@"[⌀-⏿]\s*[0-9:-]*"), new(@"@[0-9]{1,2}:[0-9]{2}"), new(@"#[A-Za-z0-9_/-]+")];
    static readonly Regex Spaces = new(@"\s+");

    public record Todo(string Text, long? Due, bool Timed);

    public static List<Todo> Parse(string text, TimeZoneInfo tz)
    {
        var list = new List<(Todo T, int Order)>();
        var order = 0;
        foreach (var line in text.Split('\n'))
        {
            var m = Item.Match(line.TrimEnd('\r'));
            if (!m.Success || m.Groups[1].Value != " ") continue;
            var rest = m.Groups[2].Value;
            order++;
            var d = DueDate.Select(r => r.Match(rest)).FirstOrDefault(x => x.Success);
            var t = DueTime.Select(r => r.Match(rest)).FirstOrDefault(x => x.Success);
            long? due = null;
            if (d is not null)
            {
                try
                {
                    var local = new DateTime(int.Parse(d.Groups[1].Value), int.Parse(d.Groups[2].Value), int.Parse(d.Groups[3].Value),
                        t is null ? 23 : int.Parse(t.Groups[1].Value), t is null ? 59 : int.Parse(t.Groups[2].Value), 0, DateTimeKind.Unspecified);
                    due = new DateTimeOffset(TimeZoneInfo.ConvertTimeToUtc(local, tz)).ToUnixTimeSeconds();
                }
                catch (ArgumentException) { } // no such date or time (31 Feb, 25:00, a DST gap): no due
            }
            var shown = Strip.Aggregate(rest, (s, r) => r.Replace(s, ""));
            shown = Spaces.Replace(shown, " ").Trim();
            if (shown.Length > MaxText) shown = shown[..MaxText];
            if (shown != "") list.Add((new Todo(shown, due, t is not null), order));
        }
        return [.. list.OrderBy(x => x.T.Due is null).ThenBy(x => x.T.Due ?? 0).ThenBy(x => x.Order).Select(x => x.T)];
    }

    /// <summary>todo.update: the open count and the first few items. null text (no note, or the mode is off) sends none.</summary>
    public static string ToJson(string? text, TimeZoneInfo tz)
    {
        var all = text is null ? [] : Parse(text, tz);
        return JsonSerializer.Serialize(new
        {
            type = "todo.update", count = all.Count,
            items = all.Take(MaxItems).Select(x => new { text = x.Text, due = x.Due, timed = x.Timed }),
        });
    }
}
