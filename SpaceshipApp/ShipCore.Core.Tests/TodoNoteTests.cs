namespace ShipCore.Core.Tests;

public class TodoNoteTests
{
    static readonly TimeZoneInfo Utc = TimeZoneInfo.Utc;
    static long At(int y, int mo, int d, int h, int mi) => new DateTimeOffset(y, mo, d, h, mi, 0, TimeSpan.Zero).ToUnixTimeSeconds();

    [Fact]
    public void OpenItemsSoonestFirstThenNoteOrder()
    {
        var note = "# Tasks\r\n- [ ] later thing \U0001F4C5 2026-11-02\r\n- [x] done \U0001F4C5 2026-10-01\n* [ ] undated one #home\n- [ ] call @14:30 [due:: 2026-10-30]\n+ [ ] undated two\n";
        var got = TodoNote.Parse(note, Utc);
        Assert.Equal(["call", "later thing", "undated one", "undated two"], got.Select(t => t.Text));
        Assert.Equal(At(2026, 10, 30, 14, 30), got[0].Due);
        Assert.True(got[0].Timed);
        Assert.Equal(At(2026, 11, 2, 23, 59), got[1].Due);
        Assert.False(got[1].Timed);
        Assert.Null(got[2].Due);
    }

    [Theory]
    [InlineData("- [ ] alarm ⏰ 9:05 \U0001F4C5 2026-10-30", "alarm", true)]
    [InlineData("- [ ] dataview due:: 2026-10-30T08:15", "dataview due:: 2026-10-30T08:15", true)] // bare fields stay in the text, as in target.lua
    [InlineData("- [ ] bad date \U0001F4C5 2026-02-31", "bad date", false)]
    public void DatesTimesAndCleanup(string line, string text, bool timed)
    {
        var t = Assert.Single(TodoNote.Parse(line, Utc));
        Assert.Equal(text, t.Text);
        Assert.Equal(timed, t.Timed);
    }

    [Fact]
    public void EmptyAfterCleanupIsSkippedAndLongTextIsCut()
    {
        Assert.Empty(TodoNote.Parse("- [ ] #tag @10:00", Utc));
        Assert.Equal(TodoNote.MaxText, TodoNote.Parse("- [ ] " + new string('a', 500), Utc)[0].Text.Length);
    }

    [Fact]
    public void MessageSendsTheCountAndTheFirstFour()
    {
        var json = TodoNote.ToJson(string.Join('\n', Enumerable.Range(1, 6).Select(i => $"- [ ] t{i}")), Utc);
        Assert.StartsWith("""{"type":"todo.update","count":6,"items":[{"text":"t1","due":null,"timed":false}""", json);
        Assert.DoesNotContain("t5", json);
        Assert.Equal("""{"type":"todo.update","count":0,"items":[]}""", TodoNote.ToJson(null, Utc));
    }
}
