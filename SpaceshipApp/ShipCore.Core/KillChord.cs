namespace ShipCore.Core;

/// <summary>The one chord that stops the app and everything it started. Plain values, so tests can check them without registering a hotkey.</summary>
public static class KillChord
{
    public const uint Alt = 0x1, Control = 0x2, Shift = 0x4;
    public const uint Key = 0x31; // the '1' key
    public const uint Modifiers = Control | Alt | Shift;
    public const string Label = "Ctrl+Alt+Shift+1";
}
