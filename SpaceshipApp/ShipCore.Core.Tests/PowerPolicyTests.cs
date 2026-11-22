using ShipCore.Core;
using Xunit;

namespace ShipCore.Core.Tests;

public class PowerPolicyTests
{
    [Theory]
    [InlineData(true, true, 4)]
    [InlineData(true, false, 1)]
    [InlineData(false, true, 1)]
    [InlineData(false, false, 1)]
    public void OnlyBatteryWithTheSaverOnSlowsThingsDown(bool saver, bool battery, int expected) =>
        Assert.Equal(expected, PowerPolicy.Factor(saver, battery));

    [Fact]
    public void ScaleMultipliesAndNeverShrinksOrOverflows()
    {
        Assert.Equal(480000, PowerPolicy.Scale(120000, 4));
        Assert.Equal(60000, PowerPolicy.Scale(60000, 0));
        Assert.Equal(int.MaxValue, PowerPolicy.Scale(int.MaxValue, 4));
    }
}
