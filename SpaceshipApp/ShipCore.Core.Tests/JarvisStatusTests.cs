using System.Text.Json;

namespace ShipCore.Core.Tests;

public class JarvisStatusTests
{
    static JsonElement Parse(string? text, long now) => JsonDocument.Parse(JarvisStatus.ToJson(text, now)).RootElement;

    [Fact]
    public void ReadsTheFileJarvisWrites()
    {
        var m = Parse("T 1000\nSTATE speaking\nLEVEL 0.642\nSAY Good evening\nERR \nPOP 1 open\nHUD 2 mood serious\n", 1003);
        Assert.Equal("jarvis.update", m.GetProperty("type").GetString());
        Assert.Equal("speaking", m.GetProperty("state").GetString());
        Assert.Equal(0.642, m.GetProperty("level").GetDouble());
        Assert.Equal("Good evening", m.GetProperty("say").GetString());
        Assert.Equal("", m.GetProperty("err").GetString());
    }

    [Theory]
    [InlineData(null, 0)]                                 // no file
    [InlineData("T 1000\nSTATE speaking\nLEVEL 1\n", 1009)] // older than 8 s
    public void MissingOrStaleIsOffline(string? text, long now)
    {
        var m = Parse(text, now);
        Assert.Equal("offline", m.GetProperty("state").GetString());
        Assert.Equal(0, m.GetProperty("level").GetDouble());
    }

    [Fact]
    public void UntrustedValuesAreTamed()
    {
        var m = Parse($"T 1000\r\nSTATE <script>\r\nLEVEL 7\r\nSAY a\u0007b{new string('x', 900)}\r\n", 1000);
        Assert.Equal("idle", m.GetProperty("state").GetString());
        Assert.Equal(1, m.GetProperty("level").GetDouble());
        Assert.StartsWith("abx", m.GetProperty("say").GetString());
        Assert.Equal(JarvisStatus.MaxText, m.GetProperty("say").GetString()!.Length);
        Assert.Equal(0, Parse("T 1000\nLEVEL NaN\n", 1000).GetProperty("level").GetDouble());
    }
}
