using System.Text.Json;

namespace ShipCore.Core.Tests;

public class AppIconsTests
{
    const string Ini = "[App.code]\nTarget=start:Visual Studio Code\n[App.chrome]\nTarget=%PF%\\chrome.exe\n[App.calc]\nTarget=cmd:calc.exe\n[App.unc]\nTarget=\\\\srv\\x.exe\n";
    static readonly List<string[]> Start = AppsFeed.Start("Visual Studio Code|Code.App\nUninstall Foo|Foo.Un\nNotepad++|Npp.App\nNotepad|Np.App\nNotepad|Np.App\nBad|a|b\nAlso Code|Code.App\n");

    [Fact]
    public void QueueIsTheSkinsIconQueue()
    {
        var q = AppIcons.Queue(Ini, Start, p => p == @"C:\PF\chrome.exe" || p == @"\\srv\x.exe", s => s.Replace("%PF%", @"C:\PF"));
        Assert.Equal(new[]
        {
            @"chrome|C:\PF\chrome.exe",              // a local file target
            @"code|shell:AppsFolder\Code.App",        // a start: target, which claims its AppID
            @"s_notepad|shell:AppsFolder\Npp.App",    // Notepad++ -> s_notepad
            @"s_notepad2|shell:AppsFolder\Np.App",    // the next Notepad is deduped, the repeat AppID dropped
        }, q);
        // cmd: (calc), UNC, junk names, a claimed AppID and an AppID with '|' are left out
    }

    [Fact]
    public void ListKeepsSafeNamesSorted()
    {
        var m = JsonDocument.Parse(AppIcons.ListJson(["code", "chrome_glow", "../x", "chrome", "code", "a b"], 7)).RootElement;
        Assert.Equal("icons.list", m.GetProperty("type").GetString());
        Assert.Equal(new[] { "chrome", "chrome_glow", "code" }, m.GetProperty("ids").EnumerateArray().Select(e => e.GetString()));
        Assert.Equal(7, m.GetProperty("v").GetInt64());
    }
}
