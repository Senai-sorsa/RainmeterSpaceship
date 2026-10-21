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
}
