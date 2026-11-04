namespace ShipCore.Core.Tests;

public class PowerPlansTests
{
    [Fact]
    public void Performance_is_the_windows_high_performance_plan()
    {
        Assert.Equal("8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", PowerPlans.Guids["performance"]);
        Assert.Equal("381b4222-f694-41f0-9685-ff5bb260df2e", PowerPlans.Guids["balance"]);
        Assert.Equal("a1841308-3541-4fab-bc81-f71556f20b4a", PowerPlans.Guids["quiet"]);
    }
}
