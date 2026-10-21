using System.Text.Json;

namespace ShipCore.Core.Tests;

public sealed class MessageRouterTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "shipcore-" + Guid.NewGuid().ToString("N"));
    private readonly FakeShell _shell = new();
    private readonly FakePower _power = new();
    private readonly MessageRouter _router;

    public MessageRouterTests()
    {
        Directory.CreateDirectory(_dir);
        File.WriteAllText(Path.Combine(_dir, "Settings.inc"), "[Variables]\r\nScale=0.67\r\n");
        var schema = Repo.Schema();
        _router = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(_power, _shell), _ => Task.FromResult(true));
    }
    public void Dispose() => Directory.Delete(_dir, true);

    private static JsonElement Json(string s) => JsonDocument.Parse(s).RootElement;

    [Fact]
    public async Task ConfigSetWritesTheKeyAndReportsOk()
    {
        var r = await _router.HandleAsync("{\"type\":\"config.set\",\"key\":\"Scale\",\"value\":\"0.8\",\"id\":7}");
        Assert.Null(r.Problem);
        var reply = Json(r.Reply!);
        Assert.Equal("config.result", reply.GetProperty("type").GetString());
        Assert.Equal(7, reply.GetProperty("id").GetInt64());
        Assert.True(reply.GetProperty("ok").GetBoolean());
        Assert.Contains("Scale=0.8", File.ReadAllText(Path.Combine(_dir, "Settings.inc")));
    }

    [Fact]
    public async Task ConfigSetOnAKeyOutsideTheSchemaIsRefusedAndWritesNothing()
    {
        var before = File.ReadAllText(Path.Combine(_dir, "Settings.inc"));
        var r = await _router.HandleAsync("{\"type\":\"config.set\",\"key\":\"NoSuchKey\",\"value\":\"1\",\"id\":1}");
        Assert.False(Json(r.Reply!).GetProperty("ok").GetBoolean());
        Assert.Equal(before, File.ReadAllText(Path.Combine(_dir, "Settings.inc")));
    }

    [Fact]
    public async Task ConfigSetWithAnInvalidValueIsRefused()
    {
        var r = await _router.HandleAsync("{\"type\":\"config.set\",\"key\":\"Scale\",\"value\":\"9\",\"id\":2}");
        Assert.False(Json(r.Reply!).GetProperty("ok").GetBoolean());
    }

    [Fact]
    public async Task ConfigGetReturnsOnlyKnownKeys()
    {
        var r = await _router.HandleAsync("{\"type\":\"config.get\",\"keys\":[\"Scale\",\"NoSuchKey\"]}");
        var values = Json(r.Reply!).GetProperty("values");
        Assert.Equal("0.67", values.GetProperty("Scale").GetString());
        Assert.False(values.TryGetProperty("NoSuchKey", out _));
    }

    [Theory]
    [InlineData("{\"type\":\"action\",\"id\":\"format\"}")]
    [InlineData("{\"type\":\"action\",\"id\":\"shutdown /s\"}")]
    [InlineData("{\"type\":\"flow.open\",\"flow\":\"cmd\"}")]
    public async Task RefusedMessagesGiveAProblemAndNoEffect(string msg)
    {
        var r = await _router.HandleAsync(msg);
        Assert.NotNull(r.Problem);
        Assert.Null(r.Reply);
        Assert.Empty(_power.Calls);
        Assert.Empty(_shell.Flows);
    }

    [Fact]
    public async Task FlowOpenRunsTheAllowedFlow()
    {
        var r = await _router.HandleAsync("{\"type\":\"flow.open\",\"flow\":\"gmail\"}");
        Assert.True(Json(r.Reply!).GetProperty("ran").GetBoolean());
        Assert.Equal(new[] { "gmail" }, _shell.Flows);
    }

    [Fact]
    public async Task SchemaActionsThatAreNotPowerAreAcceptedButNotRun()
    {
        var r = await _router.HandleAsync("{\"type\":\"action\",\"id\":\"apps.scan\"}");
        Assert.Null(r.Problem);
        Assert.Null(r.Reply);
        Assert.Empty(_power.Calls);
    }

    [Fact]
    public async Task MalformedJsonIsRefused()
    {
        var r = await _router.HandleAsync("{not json");
        Assert.Equal("not json", r.Problem);
    }
}
