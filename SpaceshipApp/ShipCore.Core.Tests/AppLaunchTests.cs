namespace ShipCore.Core.Tests;

public class AppLaunchTests
{
    const string Ini = "[App.term]\nTarget=start:Terminal || cmd:wt.exe\nProc=WindowsTerminal\n[App.files]\nTarget=cmd:explorer.exe\n"
        + "[App.bad]\nTarget=cmd:powershell -c evil\n[App.code]\nTarget=%LOCALAPPDATA%\\Code\\Code.exe || C:\\Code.exe\n[App.none]\nTarget=start:Nothing\n";
    static readonly List<string[]> Start = [["Windows Terminal", "Microsoft.WindowsTerminal_8wekyb3d8bbwe!App"], ["Windows Terminal Preview", "x!y"]];
    static LaunchPlan? Plan(string id, Func<string, bool>? exists = null) =>
        AppLaunch.Plan(Ini, Start, id, exists ?? (_ => false), s => s.Replace("%LOCALAPPDATA%", "C:\\L"));

    [Fact] public void StartTargetOpensTheAppsFolderEntry() =>
        Assert.Equal(new LaunchPlan("explorer.exe", "shell:AppsFolder\\Microsoft.WindowsTerminal_8wekyb3d8bbwe!App", "WindowsTerminal"), Plan("term"));
    [Fact] public void BareExeCmdRuns() => Assert.Equal(new LaunchPlan("explorer.exe", "", ""), Plan("files"));
    [Fact] public void CmdWithArgumentsIsRefused() => Assert.Null(Plan("bad"));
    [Fact] public void FileTargetTakesTheFirstThatExists() =>
        Assert.Equal(new LaunchPlan("C:\\Code.exe", "", "Code.exe"), Plan("code", p => p == "C:\\Code.exe"));
    [Fact] public void MissingAndUnknownAreNull()
    {
        Assert.Null(Plan("none"));
        Assert.Null(Plan("code"));
        Assert.Null(Plan("nope"));
        Assert.Null(Plan("..\\x"));
    }
}
