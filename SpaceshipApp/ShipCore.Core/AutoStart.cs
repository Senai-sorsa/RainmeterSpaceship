using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The current user's Run key only (HKCU\Software\Microsoft\Windows\CurrentVersion\Run). The Windows host implements this; there is deliberately no way to name another hive or key.</summary>
public interface IRunKey { string? Get(string name); void Set(string name, string value); void Delete(string name); }

/// <summary>Opt-in start at sign-in. No admin, no HKLM, no Winlogon, no scheduled task. Off until the user turns it on.</summary>
public sealed class AutoStart
{
    public const string ValueName = "SpaceshipHud";
    public const string Argument = "--autostart";
    private static readonly Regex ExePath = new(@"^[A-Za-z]:\\[^""\r\n<>|*?]{1,240}\.exe$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
    private readonly IRunKey _key;
    public AutoStart(IRunKey key) => _key = key;

    public bool IsEnabled => _key.Get(ValueName) is not null;

    /// <returns>null on success, otherwise why not.</returns>
    public string? Enable(string exePath)
    {
        if (!ExePath.IsMatch(exePath)) return "the program path must be an absolute .exe path without quotes";
        _key.Set(ValueName, $"\"{exePath}\" {Argument}");
        return null;
    }

    public void Disable() { if (IsEnabled) _key.Delete(ValueName); }
}
