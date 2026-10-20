namespace ShipCore.Core.Tests;

sealed class FakeRunKey : IRunKey
{
    public Dictionary<string, string> Values { get; } = new();
    public string? Get(string n) => Values.TryGetValue(n, out var v) ? v : null;
    public void Set(string n, string v) => Values[n] = v;
    public void Delete(string n) => Values.Remove(n);
}

public class HostLogicTests
{
    private static string Json() => File.ReadAllText(Path.Combine(Repo.Root, "contract", "exam-browsers.json"));

    [Fact]
    public void ExamListLoadsAndEveryNameSuspendsTheHud()
    {
        var names = ExamBrowserList.ProcessNames(Json());
        Assert.Contains("LockDown.exe", names);
        Assert.DoesNotContain(names, n => n.Contains("zoom", StringComparison.OrdinalIgnoreCase)); // normal calls must not suspend the HUD
        var p = new VisibilityPolicy(names);
        foreach (var n in names)
            Assert.Equal(Visibility.Suspend, p.Decide(new WindowSnapshot(null, new Rect(0, 0, 10, 10), NotificationState.AcceptsNotifications, new[] { n })).Visibility);
    }

    [Fact] public void UserExtrasAreAddedAndDuplicatesDropped() =>
        Assert.Equal(1, ExamBrowserList.ProcessNames(Json(), new[] { "mine.exe", "MINE.EXE", " " }).Count(n => n.Equals("mine.exe", StringComparison.OrdinalIgnoreCase)));

    [Fact]
    public void AutoStartIsOffUntilEnabledAndWritesOnlyOneQuotedValue()
    {
        var k = new FakeRunKey();
        var a = new AutoStart(k);
        Assert.False(a.IsEnabled);
        Assert.Null(a.Enable(@"C:\Program Files\Ship\Ship.exe"));
        Assert.Equal("\"C:\\Program Files\\Ship\\Ship.exe\" --autostart", k.Values[AutoStart.ValueName]);
        Assert.True(a.IsEnabled);
        a.Disable();
        Assert.Empty(k.Values);
    }

    [Theory]
    [InlineData("ship.exe")] [InlineData(@"C:\a""b.exe")] [InlineData(@"C:\a.bat")] [InlineData("C:\\a.exe\r\nx")] [InlineData(@"\\server\share\a.exe")] [InlineData("")]
    public void AutoStartRefusesOddPaths(string path)
    {
        var k = new FakeRunKey();
        Assert.NotNull(new AutoStart(k).Enable(path));
        Assert.Empty(k.Values);
    }

    [Fact]
    public void ShutdownIsNeverBlockedAndTeardownRunsOnce()
    {
        int down = 0, refresh = 0, rm = 0;
        var l = new Lifecycle(() => down++, () => refresh++, () => rm++);
        Assert.True(l.OnQueryEndSession());
        l.OnEndSession(false);
        Assert.Equal(0, down);
        l.OnEndSession(true);
        Assert.False(l.Handle(TrayCommand.Refresh));
        Assert.True(l.Handle(TrayCommand.Quit));
        Assert.Equal(1, down); Assert.Equal(1, refresh); Assert.Equal(0, rm);
    }

    [Fact]
    public void SwitchToRainmeterTearsDownThenLaunchesRainmeter()
    {
        var order = new List<string>();
        var l = new Lifecycle(() => order.Add("down"), () => { }, () => order.Add("rainmeter"));
        Assert.True(l.Handle(TrayCommand.SwitchToRainmeter));
        Assert.Equal(new[] { "down", "rainmeter" }, order);
        Assert.Equal(new[] { "Refresh", "Switch to Rainmeter", "Quit" }, Lifecycle.TrayMenu.Select(m => m.Label));
    }
}
