namespace ShipCore.Core.Tests;

public class KillChordTests
{
    [Fact]
    public void TheChordIsCtrlAltShiftOneAndTheLabelSaysSo()
    {
        Assert.Equal(0x7u, KillChord.Modifiers);
        Assert.Equal(0x31u, KillChord.Key);
        Assert.Equal("Ctrl+Alt+Shift+1", KillChord.Label);
    }
}
