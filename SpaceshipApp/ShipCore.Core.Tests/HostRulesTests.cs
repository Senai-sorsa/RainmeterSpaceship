namespace ShipCore.Core.Tests;

public class HostRulesTests
{
    [Fact]
    public void HomeDisplayIsTheFirstExactSizeMatch()
    {
        var displays = new[] { (1920, 1080), (2560, 1600), (2560, 1600) };
        Assert.Equal(1, HostRules.PickHomeDisplay(displays, (2560, 1600)));
        Assert.Equal(-1, HostRules.PickHomeDisplay(displays, (3840, 2160)));
    }

    [Theory]
    [InlineData("2560x1600", 2560, 1600)]
    [InlineData("", 2560, 1600)]
    [InlineData("2560", 2560, 1600)]
    [InlineData("0x1600", 2560, 1600)]
    [InlineData("abcx12", 2560, 1600)]
    public void ParseSizeFallsBackUnlessTheTextIsWxH(string text, int w, int h)
    {
        Assert.Equal((w, h), HostRules.ParseSize(text, (2560, 1600)));
    }

    [Fact]
    public void OnlyLogsOlderThanTheKeepWindowAreExpired()
    {
        var now = new DateTime(2026, 10, 20, 12, 0, 0);
        var files = new[]
        {
            ("old.csv", now.AddDays(-8)),
            ("recent.csv", now.AddDays(-1)),
            ("edge.csv", now.AddDays(-7)), // exactly the window is kept
        };
        Assert.Equal(new[] { "old.csv" }, HostRules.ExpiredLogs(files, now, TimeSpan.FromDays(7)));
    }

    [Fact]
    public void NextDeviceWrapsAndStartsAtTheFirst()
    {
        string[] ids = ["a", "b", "c"];
        Assert.Equal("b", HostRules.NextDevice(ids, "a"));
        Assert.Equal("a", HostRules.NextDevice(ids, "c"));
        Assert.Equal("a", HostRules.NextDevice(ids, null));
        Assert.Equal("a", HostRules.NextDevice(ids, "gone"));
        Assert.Null(HostRules.NextDevice([], "a"));
    }
}
