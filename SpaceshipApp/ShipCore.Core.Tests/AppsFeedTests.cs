using System.Text.Json;

namespace ShipCore.Core.Tests;

public class AppsFeedTests
{
    [Fact]
    public void SendsTheIniTheStartListAndOnlyTheFileTargetsThatExist()
    {
        const string ini = "[App.a]\nTarget=start:A || C:\\a.exe\n[App.b]\nTarget=cmd:explorer.exe\n[App.c]\nTarget=%PF%\\c.exe || C:\\gone.exe\n";
        var json = AppsFeed.ToJson(ini, "Alpha|id.a\r\nnot a line\nBeta|x|y\n", p => p is "C:\\a.exe" or "D:\\c.exe", p => p.Replace("%PF%", "D:"));
        var r = JsonDocument.Parse(json).RootElement;
        Assert.Equal("apps.catalog", r.GetProperty("type").GetString());
        Assert.Equal(ini, r.GetProperty("ini").GetString());
        Assert.Equal(new[] { "Alpha", "id.a" }, r.GetProperty("start")[0].EnumerateArray().Select(e => e.GetString()));
        Assert.Equal("x|y", r.GetProperty("start")[1][1].GetString());
        Assert.Equal(2, r.GetProperty("start").GetArrayLength());
        Assert.Equal(new[] { "%PF%\\c.exe", "C:\\a.exe" }, r.GetProperty("exists").EnumerateArray().Select(e => e.GetString()));
    }
}
