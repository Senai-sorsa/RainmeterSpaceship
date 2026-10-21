using System.Text.Json;

namespace ShipCore.Core.Tests;

// Fake only: FakeDial records the calls. Nothing here reaches a real brightness, audio, power or display API.
public sealed class DialGateTests : IDisposable
{
    private readonly FakeDial _dial = new();
    private readonly List<string> _asked = new();
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "shipcore-dial-" + Guid.NewGuid().ToString("N"));

    public DialGateTests() => Directory.CreateDirectory(_dir);
    public void Dispose() => Directory.Delete(_dir, true);

    private DialGate Gate(bool yes = true) => new(_dial, id => { _asked.Add(id); return Task.FromResult(yes); });
    private static JsonElement V(string json) => JsonDocument.Parse(json).RootElement.Clone();

    [Theory] [InlineData("brightness", 0)] [InlineData("volume", 50)] [InlineData("mic", 100)]
    public async Task PercentControlsRunAtOnceWithoutAConfirm(string control, int pct)
    {
        var r = await Gate().SetAsync(control, V(pct.ToString()));
        Assert.True(r.Ran);
        Assert.Equal(new[] { $"{control} {pct}" }, _dial.Calls);
        Assert.Empty(_asked);
    }

    [Theory] [InlineData(-1)] [InlineData(101)] [InlineData(1000)]
    public async Task APercentOutsideZeroToHundredNeverReachesWindows(int pct)
    {
        var r = await Gate().SetAsync("volume", V(pct.ToString()));
        Assert.False(r.Ran);
        Assert.Empty(_dial.Calls);
    }

    [Theory] [InlineData("\"50\"")] [InlineData("50.5")] [InlineData("null")] [InlineData("true")]
    public async Task APercentThatIsNotAWholeNumberIsRefused(string json)
    {
        Assert.False((await Gate().SetAsync("brightness", V(json))).Ran);
        Assert.Empty(_dial.Calls);
    }

    [Theory] [InlineData("quiet")] [InlineData("balance")] [InlineData("performance")]
    public async Task APowerModeNeedsAYesThenRunsTheNamedMode(string mode)
    {
        Assert.False((await Gate(yes: false).SetAsync("power", V($"\"{mode}\""))).Ran);
        Assert.Empty(_dial.Calls);

        Assert.True((await Gate().SetAsync("power", V($"\"{mode}\""))).Ran);
        Assert.Equal(new[] { $"power {mode}" }, _dial.Calls);
        Assert.Equal(2, _asked.Count); // one ask refused above, one ask confirmed here
    }

    [Theory] [InlineData("godmode")] [InlineData("")] [InlineData("balance /s")] [InlineData("Quiet")]
    public async Task AnUnknownPowerModeIsRefusedBeforeTheAskOrAnyCall(string mode)
    {
        Assert.False((await Gate().SetAsync("power", V($"\"{mode}\""))).Ran);
        Assert.Empty(_asked);
        Assert.Empty(_dial.Calls);
    }

    [Fact]
    public async Task ARefreshRateNeedsAYesAndOnlyTheTwoListedRates()
    {
        Assert.True((await Gate().SetAsync("refresh", V("\"165\""))).Ran);
        Assert.Equal(new[] { "refresh 165" }, _dial.Calls);
        Assert.False((await Gate().SetAsync("refresh", V("\"144\""))).Ran);
        Assert.False((await Gate(yes: false).SetAsync("refresh", V("\"60\""))).Ran);
        Assert.Equal(new[] { "refresh 165" }, _dial.Calls);
    }

    [Theory] [InlineData("shutdown")] [InlineData("launch")] [InlineData("")]
    public async Task AnUnknownControlIsRefusedAndAsksNobody(string control)
    {
        Assert.False((await Gate().SetAsync(control, V("50"))).Ran);
        Assert.Empty(_asked);
        Assert.Empty(_dial.Calls);
    }

    [Fact]
    public async Task AWindowsFailureIsReportedAsNotRunWithItsReason()
    {
        _dial.Fail = new InvalidOperationException("display does not offer 165 Hz");
        var r = await Gate().SetAsync("refresh", V("\"165\""));
        Assert.False(r.Ran);
        Assert.Contains("display does not offer 165 Hz", r.Reason);
    }

    [Fact]
    public async Task TheRouterAnswersADialSetWithItsIdAndResult()
    {
        var schema = Repo.Schema();
        var router = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(new FakePower(), new FakeShell()), _ => Task.FromResult(true), null, Gate());
        var r = await router.HandleAsync("{\"type\":\"dial.set\",\"id\":9,\"control\":\"mic\",\"value\":40}");
        Assert.Null(r.Problem);
        var reply = JsonDocument.Parse(r.Reply!).RootElement;
        Assert.Equal("dial.result", reply.GetProperty("type").GetString());
        Assert.Equal(9, reply.GetProperty("id").GetInt64());
        Assert.True(reply.GetProperty("ran").GetBoolean());
        Assert.Equal(new[] { "mic 40" }, _dial.Calls);
    }

    [Fact]
    public async Task ADialSetWithNoDialWiredIsRefused()
    {
        var schema = Repo.Schema();
        var router = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(new FakePower(), new FakeShell()), _ => Task.FromResult(true));
        var r = await router.HandleAsync("{\"type\":\"dial.set\",\"id\":1,\"control\":\"volume\",\"value\":10}");
        Assert.Contains("\"ran\":false", r.Reply);
        Assert.Empty(_dial.Calls);
    }
}

sealed class FakeDial : IDialActions
{
    public List<string> Calls { get; } = new();
    public Exception? Fail { get; set; }
    private void Record(string call) { if (Fail is not null) throw Fail; Calls.Add(call); }
    public void Brightness(int percent) => Record($"brightness {percent}");
    public void Volume(int percent) => Record($"volume {percent}");
    public void Mic(int percent) => Record($"mic {percent}");
    public void PowerMode(string mode) => Record($"power {mode}");
    public void Refresh(int hz) => Record($"refresh {hz}");
}
