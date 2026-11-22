using System.Globalization;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The registry values HWiNFO writes for its gadget (HKCU\Software\HWiNFO64\VSB, value name ValueRaw&lt;index&gt;). Null when HWiNFO is not running or is not reporting that sensor.</summary>
public interface IHwinfoRegistry
{
    string? ReadValueRaw(int index);
    /// <summary>The sensor labels by index (value names Label&lt;index&gt;), read in one go; empty when HWiNFO is not reporting.</summary>
    IReadOnlyDictionary<int, string> ReadLabels() => new Dictionary<int, string>();
}

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

    // controller.lua MAP: label patterns (lower case, plain find) per HW_ name, in priority order
    private static readonly (string Name, string[] Patterns)[] Patterns =
    [
        ("HW_CpuTemp", ["tctl", "cpu package temp", "cpu temperature", "cpu (tdie)"]),
        ("HW_GpuTemp", ["gpu temperature", "gpu core temp"]),
        ("HW_CpuPower", ["cpu package power", "cpu ppt", "package power"]),
        ("HW_GpuPower", ["total board power", "gpu power", "gpu board power"]),
        ("HW_Fan1", ["cpu fan", "fan1", "fan 1"]),
        ("HW_Fan2", ["gpu fan", "fan2", "fan 2"]),
        ("HW_GpuClock", ["gpu clock", "gpu core clock"]),
        ("HW_ChargeRate", ["charge rate"]),
        ("HW_RemainCap", ["remaining capacity"]),
        ("HW_FullCap", ["full charged capacity", "full charge capacity"]),
        ("HW_Wear", ["wear level"]),
        ("HW_SsdTemp", ["drive temperature", "ssd temperature"]),
    ];

    /// <summary>The skin's DETECT match (controller.lua OnHwScan), kept in memory: per name, the first pattern that some label
    /// contains wins, lowest index first. Names with no match are left out.</summary>
    public static Dictionary<string, int> AutoBind(IReadOnlyDictionary<int, string> labels)
    {
        var map = new Dictionary<string, int>();
        var ordered = labels.OrderBy(l => l.Key).Select(l => (l.Key, Label: l.Value.ToLowerInvariant())).ToList();
        foreach (var (name, pats) in Patterns)
            foreach (var pat in pats)
            {
                var hit = ordered.FindIndex(l => l.Label.Contains(pat, StringComparison.Ordinal));
                if (hit >= 0) { map[name] = ordered[hit].Key; break; }
            }
        return map;
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
