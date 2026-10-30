namespace ShipCore.Core.Tests;

public class JarvisSupervisorTests
{
    static readonly Func<bool> On = () => true;

    [Fact]
    public void NeverSeenOnlineIsNotRestarted()
    {
        var s = new JarvisSupervisor();
        for (long t = 0; t < 100; t++) Assert.False(s.Tick(true, t, On));
    }

    [Fact]
    public void CrashIsRestartedAfterBackoffOfTwoThenFiveThenFifteenSeconds()
    {
        var s = new JarvisSupervisor();
        s.Tick(false, 0, On);
        Assert.False(s.Tick(true, 100, On));           // goes offline: the wait starts
        Assert.False(s.Tick(true, 101, On));
        Assert.True(s.Tick(true, 102, On));            // 2 s
        Assert.False(s.Tick(true, 103, On));
        Assert.False(s.Tick(true, 107, On));
        Assert.True(s.Tick(true, 108, On));            // 5 s after the wait began at 103
        Assert.False(s.Tick(true, 109, On));
        Assert.False(s.Tick(true, 123, On));
        Assert.True(s.Tick(true, 124, On));            // 15 s
    }

    [Fact]
    public void QuitStaysDownUntilStartedAgain()
    {
        var s = new JarvisSupervisor();
        s.Tick(false, 0, On);
        s.Quit();
        for (long t = 1; t < 60; t++) Assert.False(s.Tick(true, t, On));
        s.Started();
        s.Tick(false, 60, On);
        s.Tick(true, 61, On);
        Assert.True(s.Tick(true, 63, On));
    }

    [Fact]
    public void GivesUpAfterFiveTriesInTenMinutesAndOnlineClearsIt()
    {
        var s = new JarvisSupervisor();
        s.Tick(false, 0, On);
        int starts = 0;
        for (long t = 1; t < 300; t++) if (s.Tick(true, t, On)) starts++;
        Assert.Equal(5, starts);
        Assert.True(s.GaveUp);
        s.Tick(false, 301, On);                         // it came back by itself
        Assert.False(s.GaveUp);
    }

    [Fact]
    public void DisabledSettingStartsNothing()
    {
        var s = new JarvisSupervisor();
        s.Tick(false, 0, On);
        s.Tick(true, 1, () => false);
        Assert.False(s.Tick(true, 3, () => false));
    }
}
