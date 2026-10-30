namespace ShipCore.Core.Tests;

public class LltGateTests
{
    sealed class FakeLlt(int code = 0) : ILltRunner
    {
        public readonly List<(string F, string V)> Calls = [];
        public int Set(string feature, string value) { Calls.Add((feature, value)); return code; }
    }

    static readonly Dictionary<string, string> None = [];

    [Theory]
    [InlineData("hybrid", "ECO", "hybrid-mode", "on-igpu-only")]
    [InlineData("hybrid", "AUTO", "hybrid-mode", "on-auto")]
    [InlineData("power", "Performance", "power-mode", "performance")]
    [InlineData("refresh", "165", "refresh-rate", "165")]
    [InlineData("battery", "conservation", "battery", "conservation")]
    public async Task MapsThroughTheSettingsDefaults(string feature, string value, string name, string arg)
    {
        var llt = new FakeLlt();
        var g = await new LltGate(llt, _ => throw new Exception("no confirm")).SetAsync(feature, value, None);
        Assert.True(g.Ran);
        Assert.Equal((name, arg), Assert.Single(llt.Calls));
    }

    [Theory]
    [InlineData("power", "extreme")]
    [InlineData("refresh", "240")]
    [InlineData("hybrid", "on")]
    [InlineData("battery", "rapid-charge")]
    [InlineData("fan", "max")]
    public async Task RefusesWhatTheSettingsDoNotList(string feature, string value)
    {
        var llt = new FakeLlt();
        Assert.False((await new LltGate(llt, _ => Task.FromResult(true)).SetAsync(feature, value, None)).Ran);
        Assert.Empty(llt.Calls);
    }

    [Fact]
    public async Task SettingsWithShellTextAreRefused()
    {
        var llt = new FakeLlt();
        var gate = new LltGate(llt, _ => Task.FromResult(true));
        Assert.False((await gate.SetAsync("power", "x&calc", new Dictionary<string, string> { ["LltPowerModes"] = "x&calc" })).Ran);
        Assert.False((await gate.SetAsync("power", "quiet", new Dictionary<string, string> { ["LltPowerFeature"] = "power-mode;calc" })).Ran);
        Assert.Empty(llt.Calls);
    }

    [Fact]
    public async Task DiscreteOnlyAsksFirst()
    {
        var llt = new FakeLlt();
        Assert.Equal("not confirmed", (await new LltGate(llt, _ => Task.FromResult(false)).SetAsync("hybrid", "DGPU", None)).Reason);
        Assert.Empty(llt.Calls);
        Assert.True((await new LltGate(llt, _ => Task.FromResult(true)).SetAsync("hybrid", "DGPU", None)).Ran);
        Assert.Equal(("hybrid-mode", "off"), Assert.Single(llt.Calls));
    }

    [Fact]
    public async Task ExitCodeAndMissingToolAreNotRun()
    {
        Assert.Equal("exit 3", (await new LltGate(new FakeLlt(3), _ => Task.FromResult(true)).SetAsync("refresh", "60", None)).Reason);
        var missing = new LltGate(new Throws(), _ => Task.FromResult(true));
        Assert.StartsWith("failed:", (await missing.SetAsync("refresh", "60", None)).Reason);
    }

    sealed class Throws : ILltRunner { public int Set(string f, string v) => throw new FileNotFoundException("Legion Toolkit not installed"); }
}
