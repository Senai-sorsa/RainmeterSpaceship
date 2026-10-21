using System.Globalization;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The registry values HWiNFO writes for its gadget (HKCU\Software\HWiNFO64\VSB, value name ValueRaw&lt;index&gt;). Null when HWiNFO is not running or is not reporting that sensor.</summary>
public interface IHwinfoRegistry { string? ReadValueRaw(int index); }

/// <summary>HWiNFO sensor values by the skin's names (HW_CpuTemp, ...). Each name maps to its sensor index in settings.json; a negative index means not mapped, and nothing is read for it.</summary>
public sealed class HwinfoSensors(IHwinfoRegistry registry, IReadOnlyDictionary<string, int> map)
{
    private static readonly Regex Number = new(@"-?\d+(\.\d+)?", RegexOptions.Compiled);

    /// <returns>The value, or null when the sensor is not mapped, HWiNFO is not reporting, or the text has no number.</returns>
    public double? Read(string name)
    {
        if (!map.TryGetValue(name, out var index) || index < 0) return null;
        return ParseNumber(registry.ReadValueRaw(index));
    }

    /// <summary>The first number in the text, read the way the skin reads it. Null when there is none or it is not finite.</summary>
    public static double? ParseNumber(string? raw)
    {
        if (raw is null) return null;
        var m = Number.Match(raw);
        return m.Success && double.TryParse(m.Value, NumberStyles.Float, CultureInfo.InvariantCulture, out var v) && double.IsFinite(v) ? v : null;
    }

    /// <summary>The HW_ entries of settings.json as sensor indexes. Entries that are not whole numbers are left out.</summary>
    public static Dictionary<string, int> MapFrom(IReadOnlyDictionary<string, string> settings)
    {
        var map = new Dictionary<string, int>();
        foreach (var (k, v) in settings)
            if (k.StartsWith("HW_", StringComparison.Ordinal) && int.TryParse(v, NumberStyles.Integer, CultureInfo.InvariantCulture, out var i)) map[k] = i;
        return map;
    }
}
