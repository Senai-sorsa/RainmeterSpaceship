using System.Diagnostics;
using ShipCore.Core;

// llt.ps1's switch without PowerShell: Legion Toolkit's own llt.exe from its install folders (status.ps1's Resolve-Llt list), started
// directly with each argument passed as one argument. LltGate has already checked the feature name and the value.
sealed class LltRunner : ILltRunner
{
    static readonly TimeSpan Timeout = TimeSpan.FromSeconds(30);

    static string? Exe() => new[]
    {
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "LenovoLegionToolkit", "llt.exe"),
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "LenovoLegionToolkit", "llt.exe"),
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "LenovoLegionToolkit", "llt.exe"),
    }.FirstOrDefault(File.Exists);

    public int Set(string feature, string value)
    {
        var exe = Exe() ?? throw new FileNotFoundException("Legion Toolkit not installed");
        var info = new ProcessStartInfo(exe) { UseShellExecute = false, CreateNoWindow = true };
        foreach (var a in new[] { "feature", "set", feature, value }) info.ArgumentList.Add(a);
        using var p = Process.Start(info) ?? throw new InvalidOperationException("llt did not start");
        if (!p.WaitForExit(Timeout)) { p.Kill(entireProcessTree: true); throw new TimeoutException("llt"); } // only the tree started here
        return p.ExitCode;
    }
}
