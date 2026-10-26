using System.Text.Json;

namespace ShipCore.Core.Tests;

public class AppStatesTests
{
    [Fact]
    public void ProcsAreLowerCasedWithExeAndOddOnesDropped()
    {
        var ini = "[Chrome]\r\nProc=chrome.exe\r\nProc=\r\nProc=RASAero II.exe\r\nProc=Discord\r\nProc=..\\evil.exe\r\nProc=chrome.exe\r\nTarget=x.exe\r\n";
        Assert.Equal(["chrome.exe", "rasaero ii.exe", "discord.exe"], AppStates.Procs(ini));
    }

    [Fact]
    public void WindowBeatsBackgroundBeatsNotRunning()
    {
        var json = AppStates.ToJson(["chrome.exe", "everything.exe", "xfoil.exe"],
            new HashSet<string> { "chrome.exe" }, new HashSet<string> { "chrome.exe", "everything.exe" });
        var s = JsonDocument.Parse(json).RootElement;
        Assert.Equal("apps.state", s.GetProperty("type").GetString());
        var st = s.GetProperty("states");
        Assert.Equal(2, st.GetProperty("chrome.exe").GetInt32());
        Assert.Equal(1, st.GetProperty("everything.exe").GetInt32());
        Assert.Equal(0, st.GetProperty("xfoil.exe").GetInt32());
    }
}
