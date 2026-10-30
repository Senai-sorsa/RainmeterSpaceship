using System.Text.Json;

namespace ShipCore.Core.Tests;

public class JarvisStatusTests
{
    static JsonElement Parse(string? text, long now, string note = "") => JsonDocument.Parse(JarvisStatus.ToJson(text, now, note)).RootElement;

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

    [Fact]
    public void PopAndLog()
    {
        Assert.Equal("3 open", Parse("T 1000\nPOP 3 open\n", 1000).GetProperty("pop").GetString());
        var m = JsonDocument.Parse(JarvisStatus.LogJson("U|1|hi\u0007\nJ|2|yo\n", null, "MUTED 1\n")).RootElement;
        Assert.Equal("jarvis.log", m.GetProperty("type").GetString());
        Assert.Equal("U|1|hi\nJ|2|yo\n", m.GetProperty("log").GetString());
        Assert.Equal("", m.GetProperty("live").GetString());
        Assert.True(m.GetProperty("muted").GetBoolean());
        Assert.False(JsonDocument.Parse(JarvisStatus.LogJson(null, null, null)).RootElement.GetProperty("muted").GetBoolean());
    }

    [Fact]
    public void CmdLinesAreTheSkinsLines()
    {
        Assert.Equal("WAKE 100 2", JarvisStatus.CmdLine("wake", null, 100, 2));
        Assert.Equal("WAKE 100 9", JarvisStatus.CmdLine("wake", null, 100, 40));
        Assert.Equal("CANCEL 100", JarvisStatus.CmdLine("cancel", "ignored", 100, 0));
        Assert.Equal("TRAINWAKE 100", JarvisStatus.CmdLine("train", null, 100, 0));
        Assert.Equal("ASK 100 what is the time", JarvisStatus.CmdLine("ask", "  what\nis\u0007the   time ", 100, 0));
        Assert.Null(JarvisStatus.CmdLine("ask", " \n ", 100, 0));
        Assert.Equal(4 + 4 + JarvisStatus.MaxAsk, JarvisStatus.CmdLine("ask", new string('a', 900), 100, 0)!.Length);
        Assert.Null(JarvisStatus.CmdLine("shutdown", null, 100, 0));
        Assert.Null(JarvisStatus.CmdLine("start", null, 100, 0));
    }

    [Fact]
    public void NotesAreAFixedList()
    {
        Assert.Equal("STARTING", Parse(null, 0, "STARTING").GetProperty("note").GetString());
        Assert.Equal("", Parse(null, 0, "HACKED").GetProperty("note").GetString());
        Assert.Equal("", Parse(null, 0).GetProperty("note").GetString());
    }

    [Fact]
    public void PythonIsTheSkinsOrder()
    {
        var venv = @"C:\L\SpaceshipHUD\venv\Scripts\pythonw.exe";
        var pyw = @"C:\L\Programs\Python\Launcher\pyw.exe";
        Assert.Equal(venv, JarvisStatus.PythonW(@"C:\L", @"C:\W", p => p == venv || p == pyw));
        Assert.Equal(pyw, JarvisStatus.PythonW(@"C:\L", @"C:\W", p => p == pyw));
        Assert.Null(JarvisStatus.PythonW(@"C:\L", @"C:\W", _ => false));
        Assert.Equal(@"C:\W\pyw.exe", JarvisStatus.PythonW("", @"C:\W", _ => true)); // no LOCALAPPDATA: never a relative path
        // JarvisPython: used when it is a local, existing pythonw/pyw; set but anything else is NO PYTHON, with no fallback
        Assert.Equal(venv, JarvisStatus.PythonW(@"C:\L", @"C:\W", _ => true, "  "));
        Assert.Equal(@"D:\Py\pythonw.exe", JarvisStatus.PythonW(@"C:\L", @"C:\W", _ => true, @"""D:\Py\pythonw.exe"""));
        Assert.Null(JarvisStatus.PythonW(@"C:\L", @"C:\W", _ => true, @"Py\pythonw.exe"));
        Assert.Null(JarvisStatus.PythonW(@"C:\L", @"C:\W", _ => true, @"\server\share\pythonw.exe"));
        Assert.Null(JarvisStatus.PythonW(@"C:\L", @"C:\W", _ => true, @"C:\Windows\System32\cmd.exe"));
        Assert.Null(JarvisStatus.PythonW(@"C:\L", @"C:\W", p => p == venv, @"D:\Py\pythonw.exe"));
    }

    [Fact]
    public void TailStartsOnAWholeLine()
    {
        var bytes = System.Text.Encoding.UTF8.GetBytes("U|1|aaaa\nJ|2|bb\n");
        Assert.Equal("J|2|bb\n", JarvisStatus.Tail(new MemoryStream(bytes), 10));
        Assert.Equal("U|1|aaaa\nJ|2|bb\n", JarvisStatus.Tail(new MemoryStream(bytes), 100));
    }
}
