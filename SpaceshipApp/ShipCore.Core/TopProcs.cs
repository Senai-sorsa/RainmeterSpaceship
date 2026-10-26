using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The procs.top message: the five busiest processes for the targeter, as Target.ini's UsageMonitor measures
/// (mTop1..5 Alias=CPU Rollup=1 with its Blacklist, cpu divided by the thread count; mTargetRam Alias=RAM by name).</summary>
public static class TopProcs
{
    static readonly HashSet<string> Blacklist = new(["_Total", "Idle", "System", "Memory Compression", "Registry"], StringComparer.OrdinalIgnoreCase);
    static readonly Regex Suffix = new(@"#\d+$");

    /// <summary>PDH instances (chrome, chrome#1, …) summed by name, blacklist dropped, top n by CPU. ram is bytes.</summary>
    public static IReadOnlyList<(string Name, double Cpu, double Ram)> Top(
        IEnumerable<(string Instance, double Value)> cpu, IEnumerable<(string Instance, double Value)> ram, int threads, int n = 5)
    {
        static Dictionary<string, double> Roll(IEnumerable<(string Instance, double Value)> xs)
        {
            var d = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
            foreach (var (inst, v) in xs)
            {
                var name = Suffix.Replace(inst, "");
                if (!Blacklist.Contains(name) && double.IsFinite(v)) d[name] = d.GetValueOrDefault(name) + v;
            }
            return d;
        }
        var r = Roll(ram);
        return Roll(cpu).OrderByDescending(kv => kv.Value).Take(n)
            .Select(kv => (kv.Key, kv.Value / Math.Max(1, threads), r.GetValueOrDefault(kv.Key))).ToList();
    }

    public static string ToJson(IReadOnlyList<(string Name, double Cpu, double Ram)> top) =>
        JsonSerializer.Serialize(new { type = "procs.top", top = top.Select(p => new { name = p.Name, cpu = Math.Round(p.Cpu, 1), ram = Math.Round(p.Ram) }) });
}
