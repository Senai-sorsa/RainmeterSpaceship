using System.Text.Json;

namespace ShipCore.Core.Tests;

public class HostPipeWireTests
{
    private static JsonElement Fixture() =>
        JsonDocument.Parse(File.ReadAllText(Path.Combine(Repo.Root, "contract", "fixtures", "host-pipe.json"))).RootElement.Clone();

    [Fact]
    public void PipeNamesMatchTheSharedFixture()
    {
        foreach (var c in Fixture().GetProperty("pipe_names").EnumerateArray())
            Assert.True(c.GetProperty("valid").GetBoolean() == HostPipeWire.PipeNameOk(c.GetProperty("name").GetString()!), c.GetProperty("name").GetString());
    }

    [Fact]
    public void HellosMatchTheSharedFixture()
    {
        foreach (var c in Fixture().GetProperty("hellos").EnumerateArray())
            Assert.True(c.GetProperty("valid").GetBoolean() == (HostPipeWire.ParseHello(c.GetProperty("line").GetString()!) is not null), c.GetProperty("name").GetString());
    }

    [Fact]
    public void SessionFileRoundTripsAndRefusesABadPipeName()
    {
        var name = "SpaceshipHost-Senai-0123456789abcdef0123456789abcdef";
        var parsed = HostPipeWire.ParseSession(HostPipeWire.SessionJson(new SessionFile(name, "n", "s", 7)));
        Assert.Equal(new SessionFile(name, "n", "s", 7), parsed);
        Assert.Null(HostPipeWire.ParseSession("{\"pipe\":\"..\\\\x\",\"nonce\":\"n\",\"session\":\"s\",\"pid\":7}"));
        Assert.Null(HostPipeWire.ParseSession("{\"nonce\":\"n\",\"session\":\"s\",\"pid\":7}"));
        Assert.Null(HostPipeWire.ParseSession("not json"));
        Assert.Contains("\"pipe\":", HostPipeWire.SessionJson(new SessionFile(name, "n", "s", 7)));
    }
}
