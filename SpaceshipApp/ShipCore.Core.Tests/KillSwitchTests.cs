namespace ShipCore.Core.Tests;

public class KillSwitchTests
{
    [Fact]
    public void FirstPressKillsOnceAndRepeatPressesDoNothing()
    {
        // Fake kill action only: the real process-tree kill is never reachable from a test.
        int kills = 0;
        var kill = new KillSwitch(() => kills++);
        Assert.True(kill.Fire());
        Assert.False(kill.Fire());
        Assert.Equal(1, kills);
    }
}
