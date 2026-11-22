namespace ShipCore.Core;

/// <summary>Reads the "GPU Engine(*)\Utilization Percentage" counter: one value per instance name. The Windows host implements it with PDH; tests use a fake. Empty when the counter is unavailable.</summary>
public interface IGpuCounters { IReadOnlyList<(string Instance, double Percent)> Read(); }

public static class GpuLoad
{
    /// <summary>
    /// The busiest engine, 0 to 100, the way Task Manager counts it: the per-process instances
    /// (pid_N_luid_..._engtype_X) are summed per engine (the part from "luid_" on), and the highest engine wins.
    /// Null when there are no instances.
    /// </summary>
    public static double? Busiest(IReadOnlyList<(string Instance, double Percent)> instances)
    {
        if (instances.Count == 0) return null;
        var sums = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        foreach (var (name, pct) in instances)
        {
            if (!double.IsFinite(pct) || pct < 0) continue;
            var i = name.IndexOf("luid_", StringComparison.OrdinalIgnoreCase);
            var engine = i >= 0 ? name[i..] : name;
            sums[engine] = sums.GetValueOrDefault(engine) + pct;
        }
        return sums.Count == 0 ? null : Math.Clamp(sums.Values.Max(), 0, 100);
    }
}
