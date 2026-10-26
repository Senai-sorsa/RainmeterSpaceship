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

    [Fact]
    public void LltReadsTheKeyValueLinesLowerCased()
    {
        var m = Parse("llt", "dgpu=on\r\nllt=found\r\nlltpath=C:\\x\\llt.exe\r\nhybrid=On-IGPU-Only\r\npower=Performance\r\nrefresh=165\r\nbattery=<b>bad</b>\r\n");
        Assert.Equal("llt", m.GetProperty("kind").GetString());
        Assert.Equal("on", m.GetProperty("dgpu").GetString());
        Assert.Equal("on-igpu-only", m.GetProperty("hybrid").GetString());
        Assert.Equal("performance", m.GetProperty("power").GetString());
        Assert.Equal("165", m.GetProperty("refresh").GetString());
        Assert.Equal("", m.GetProperty("battery").GetString());
        Assert.False(m.TryGetProperty("lltpath", out _));
    }

    [Fact]
    public void LltWithoutLegionToolkitStillSendsTheDgpuLight()
    {
        var m = Parse("llt", "dgpu=off\nllt=missing\n");
        Assert.Equal("off", m.GetProperty("dgpu").GetString());
        Assert.Equal("", m.GetProperty("power").GetString());
    }

    [Theory]
    [InlineData("llt", "llt=missing")]
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
