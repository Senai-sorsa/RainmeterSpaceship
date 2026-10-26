using System.Text.Json;

namespace ShipCore.Core.Tests;

public class StatusScriptsTests
{
    static JsonElement Parse(string kind, string output) => JsonDocument.Parse(StatusScripts.ToJson(kind, output)!).RootElement;

    [Fact]
    public void UpkeepWithAntivirus()
    {
        var m = Parse("upkeep", "3|12|WINDOWS DEFENDER|ON\r\n");
        Assert.Equal("status.update", m.GetProperty("type").GetString());
        Assert.Equal(3, m.GetProperty("updates").GetInt32());
        Assert.Equal(12, m.GetProperty("upgrades").GetInt32());
        Assert.Equal("WINDOWS DEFENDER", m.GetProperty("av").GetString());
        Assert.True(m.GetProperty("avOn").GetBoolean());
    }

    [Fact]
    public void UpkeepWithoutAntivirusAndUnknownCounts()
    {
        var m = Parse("upkeep", "-1|-1|NONE");
        Assert.Equal(-1, m.GetProperty("updates").GetInt32());
        Assert.Equal("NONE", m.GetProperty("av").GetString());
        Assert.Equal(JsonValueKind.Null, m.GetProperty("avOn").ValueKind);
    }

    [Fact]
    public void DevTakesTheLastLine()
    {
        var m = Parse("dev", "a warning line\n2|1|RUNNING|-1\n\n");
        Assert.Equal(2, m.GetProperty("wsl").GetInt32());
        Assert.Equal(1, m.GetProperty("llm").GetInt32());
        Assert.Equal("RUNNING", m.GetProperty("tailscale").GetString());
        Assert.Equal(-1, m.GetProperty("docker").GetInt32());
    }

    [Theory]
    [InlineData("dev", "")]
    [InlineData("dev", "1|2|3")]
    [InlineData("upkeep", "1|2")]
    [InlineData("other", "1|2|3|4")]
    public void WrongShapeIsNull(string kind, string output) => Assert.Null(StatusScripts.ToJson(kind, output));

    [Fact]
    public void UntrustedFieldsAreTamed()
    {
        var m = Parse("dev", "x|99999999|<b>run</b>|3");
        Assert.Equal(-1, m.GetProperty("wsl").GetInt32());
        Assert.Equal(-1, m.GetProperty("llm").GetInt32());
        Assert.Equal(JsonValueKind.Null, m.GetProperty("tailscale").ValueKind);
    }
}
