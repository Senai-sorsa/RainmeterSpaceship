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
        Assert.Equal("config.ack", reply.GetProperty("type").GetString());
        Assert.Equal("Scale", reply.GetProperty("key").GetString());
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

    [Fact]
    public async Task SetupFinishIsRememberedAcrossARestart()
    {
        var path = Path.Combine(_dir, "ui-state.json");
        var schema = Repo.Schema();
        var first = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(_power, _shell), _ => Task.FromResult(true), new HostState(path));
        Assert.False(Json((await first.HandleAsync("{\"type\":\"setup.get\"}")).Reply!).GetProperty("done").GetBoolean());
        Assert.True(Json((await first.HandleAsync("{\"type\":\"setup.finish\",\"mode\":\"defaults\"}")).Reply!).GetProperty("done").GetBoolean());

        var second = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(_power, _shell), _ => Task.FromResult(true), new HostState(path));
        Assert.True(Json((await second.HandleAsync("{\"type\":\"setup.get\"}")).Reply!).GetProperty("done").GetBoolean());
    }

    [Fact]
    public async Task SetupRerunReopensTheWizardWithoutClearingTheFlag()
    {
        var r = await _router.HandleAsync("{\"type\":\"action\",\"id\":\"setup.rerun\"}");
        Assert.False(Json(r.Reply!).GetProperty("done").GetBoolean());
    }

    [Fact]
    public async Task AboutMeIsSavedAndEchoed()
    {
        var r = await _router.HandleAsync("{\"type\":\"aboutme.set\",\"text\":\"I like tea\"}");
        Assert.Equal("I like tea", Json(r.Reply!).GetProperty("text").GetString());
        Assert.Equal("I like tea", Json((await _router.HandleAsync("{\"type\":\"aboutme.get\"}")).Reply!).GetProperty("text").GetString());
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
    public async Task HitRegionsUpdateTheRegionsAndSendNoReply()
    {
        var schema = Repo.Schema();
        var hits = new HitRegions();
        var router = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(_power, _shell), _ => Task.FromResult(true), hits: hits);
        var r = await router.HandleAsync("{\"type\":\"hit.regions\",\"rects\":[[10,20,30,40]],\"keyboard\":true}");
        Assert.Null(r.Problem);
        Assert.Null(r.Reply);
        Assert.True(hits.Contains(10, 20));
        Assert.True(hits.Contains(39, 59));
        Assert.False(hits.Contains(40, 20));
        Assert.False(hits.Contains(10, 60));
        Assert.True(hits.Keyboard);

        await router.HandleAsync("{\"type\":\"hit.regions\",\"rects\":[],\"keyboard\":false}");
        Assert.False(hits.Contains(10, 20));
        Assert.False(hits.Keyboard);
    }

    [Fact]
    public async Task TargetOpenPassesOnlyTheFixedTargets()
    {
        var schema = Repo.Schema();
        var opened = new List<string>();
        var router = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(_power, _shell), _ => Task.FromResult(true), open: opened.Add);
        Assert.Null((await router.HandleAsync("{\"type\":\"target.open\",\"what\":\"taskmgr\"}")).Problem);
        Assert.Null((await router.HandleAsync("{\"type\":\"target.open\",\"what\":\"todo\"}")).Problem);
        Assert.Null((await router.HandleAsync("{\"type\":\"target.open\",\"what\":\"mute\"}")).Problem);
        Assert.Null((await router.HandleAsync("{\"type\":\"target.open\",\"what\":\"terminal\"}")).Problem);
        Assert.NotNull((await router.HandleAsync("{\"type\":\"target.open\",\"what\":\"C:\\\\\"}")).Problem);
        Assert.NotNull((await router.HandleAsync("{\"type\":\"target.open\",\"what\":\"cmd.exe\"}")).Problem);
        Assert.NotNull((await router.HandleAsync("{\"type\":\"target.open\",\"what\":\"ms-settings:sound\"}")).Problem);
        Assert.Equal(["taskmgr", "todo", "mute", "terminal"], opened);
    }

    sealed class FakeLlt : ILltRunner
    {
        public readonly List<string> Calls = [];
        public int Set(string feature, string value) { Calls.Add(feature + " " + value); return 0; }
    }

    [Fact]
    public async Task LltSetRunsTheGateAndRefreshesTheStatus()
    {
        var schema = Repo.Schema();
        var llt = new FakeLlt();
        var refreshed = 0;
        var router = new MessageRouter(schema, new ConfigStore(_dir, schema), new ActionGate(_power, _shell), _ => Task.FromResult(true),
            llt: new LltGate(llt, _ => Task.FromResult(true)), refresh: () => refreshed++);
        var r = await router.HandleAsync("{\"type\":\"llt.set\",\"id\":4,\"feature\":\"refresh\",\"value\":\"60\"}");
        Assert.Contains("\"ran\":true", r.Reply);
        Assert.Contains("\"id\":4", r.Reply);
        Assert.Equal(["refresh-rate 60"], llt.Calls);
        Assert.Equal(1, refreshed);
        Assert.NotNull((await router.HandleAsync("{\"type\":\"llt.set\",\"id\":5,\"feature\":\"refresh\",\"value\":\"60 & calc\"}")).Problem);
        Assert.NotNull((await router.HandleAsync("{\"type\":\"llt.set\",\"id\":5,\"feature\":\"fan\",\"value\":\"max\"}")).Problem);
        Assert.Null((await router.HandleAsync("{\"type\":\"status.refresh\"}")).Problem);
        Assert.Equal(2, refreshed);
        Assert.Single(llt.Calls);
    }

    [Fact]
    public async Task MalformedJsonIsRefused()
    {
        var r = await _router.HandleAsync("{not json");
        Assert.Equal("not json", r.Problem);
    }
}
