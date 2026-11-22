namespace ShipCore.Core.Tests;

public class ActionGateTests
{
    private readonly FakePower _power = new();
    private readonly FakeShell _shell = new();
    private ActionGate Gate() => new(_power, _shell);

    [Fact]
    public async Task APowerActionRunsOnlyAfterAPersonConfirms()
    {
        Assert.False((await Gate().PowerAsync("shutdown", _ => Task.FromResult(false))).Ran);
        Assert.Empty(_power.Calls);
        var asked = new List<string>();
        Assert.True((await Gate().PowerAsync("shutdown", id => { asked.Add(id); return Task.FromResult(true); })).Ran);
        Assert.Equal(new[] { "shutdown" }, _power.Calls);
        Assert.Equal(new[] { "shutdown" }, asked);
    }

    [Theory] [InlineData("format")] [InlineData("")] [InlineData("Shutdown")] [InlineData("shutdown /s")] [InlineData("rundll32")]
    public async Task UnknownPowerActionsNeverReachTheConfirmationOrTheOs(string id)
    {
        var called = false;
        Assert.False((await Gate().PowerAsync(id, _ => { called = true; return Task.FromResult(true); })).Ran);
        Assert.False(called);
        Assert.Empty(_power.Calls);
    }

    [Fact]
    public void OnlyTheThreeKnownFlowsOpen()
    {
        foreach (var f in new[] { "gmail", "calendars", "obsidian" }) Assert.True(Gate().Flow(f).Ran);
        foreach (var f in new[] { "https://evil.example", "", "cmd" }) Assert.False(Gate().Flow(f).Ran);
        Assert.Equal(new[] { "gmail", "calendars", "obsidian" }, _shell.Flows);
    }
}
