namespace ShipCore.Core.Tests;

public class IcsTests
{
    static readonly DateTime From = new(2026, 10, 26, 0, 0, 0, DateTimeKind.Utc), To = From.AddDays(21);

    const string Weekly = "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:w1\r\nSUMMARY:Physics\\, lab\r\nDTSTART:20261019T150000Z\r\nDTEND:20261019T160000Z\r\n" +
        "RRULE:FREQ=WEEKLY;BYDAY=MO,WE\r\nEXDATE:20261028T150000Z\r\nBEGIN:VALARM\r\nSUMMARY:ignored\r\nEND:VALARM\r\nEND:VEVENT\r\n" +
        "BEGIN:VEVENT\r\nUID:c1\r\nSTATUS:CANCELLED\r\nSUMMARY:Gone\r\nDTSTART:20261027T150000Z\r\nEND:VEVENT\r\n" +
        "BEGIN:VEVENT\r\nUID:d1\r\nSUMMARY:Holiday\r\nDTSTART;VALUE=DATE:20261030\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n";

    [Fact]
    public void ExpandsAWeeklyRuleSkipsTheExdateTheCancelledEventAndTheAlarm()
    {
        var ev = Ics.Parse(Weekly, "School", From, To);
        var physics = ev.Where(e => e.Title == "Physics, lab").Select(e => e.StartUtc).ToList();
        // Mon 26, Wed 28 (excluded), Mon 2, Wed 4, Mon 9, Wed 11; Mon 16 15:00Z is past To (16th 00:00Z)
        Assert.Equal(new[] { 26, 2, 4, 9, 11 }, physics.Select(d => d.Day));
        Assert.All(physics, d => Assert.Equal(15, d.Hour));
        Assert.DoesNotContain(ev, e => e.Title is "Gone" or "ignored");
        var hol = Assert.Single(ev, e => e.Title == "Holiday");
        Assert.True(hol.AllDay);
        Assert.Equal(TimeSpan.FromDays(1), hol.EndUtc - hol.StartUtc);
    }

    [Fact]
    public void WritesCalendarTxtSoonestFirstWithoutPastEventsOrSeparators()
    {
        var now = From.AddHours(15.5);
        var text = Ics.Text([new(From.AddDays(1), From.AddDays(1).AddHours(1), false, "A", "Later"),
                             new(From, From.AddHours(1), false, "A", "Over"),
                             new(From.AddHours(15), From.AddHours(16), false, "Sch|ool", "Now\nhere")], 2, 1, now);
        Assert.Equal($"T {Ics.Unix(now)}\nC 2 1\nE {Ics.Unix(From.AddHours(15))}|{Ics.Unix(From.AddHours(16))}|0|Sch ool|Now here\n" +
                     $"E {Ics.Unix(From.AddDays(1))}|{Ics.Unix(From.AddDays(1).AddHours(1))}|0|A|Later\n", text);
    }

    [Fact]
    public void ReadsSourcesAndFetchesOnlyWebUrls()
    {
        var s = Ics.Sources("1\tSchool\twebcal://x/a.ics\n0\tOld\thttps://y/b.ics\nbad line\n");
        Assert.Equal([new Ics.Source(true, "School", "webcal://x/a.ics"), new Ics.Source(false, "Old", "https://y/b.ics")], s);
        Assert.Equal("https://x/a.ics", Ics.FetchUri("webcal://x/a.ics")!.ToString());
        Assert.Null(Ics.FetchUri("file:///C:/secret.ics"));
        Assert.Null(Ics.FetchUri("not a url"));
    }
}
