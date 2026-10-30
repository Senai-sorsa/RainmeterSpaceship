namespace ShipCore.Core;

/// <summary>Battery saver: on battery the background runners wait longer between their checks.</summary>
public static class PowerPolicy
{
    public const int BatteryFactor = 4;

    /// <param name="saverOn">The PowerSaver setting (on by default).</param>
    public static int Factor(bool saverOn, bool onBattery) => saverOn && onBattery ? BatteryFactor : 1;

    /// <summary>A period or interval stretched by the factor; a factor below 1 counts as 1.</summary>
    public static int Scale(int value, int factor) => (int)Math.Min(int.MaxValue, (long)value * Math.Max(1, factor));
}
