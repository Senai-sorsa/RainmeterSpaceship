using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>Runs Legion Toolkit's own CLI: llt.exe feature set &lt;feature&gt; &lt;value&gt;. Returns the exit code; throws when llt.exe is not installed.</summary>
public interface ILltRunner { int Set(string feature, string value); }

/// <summary>The top console's Legion Toolkit buttons (console.lua -> llt.ps1). The page names one of four features and a value;
/// the value must be one the settings list for that feature (LltHybrid*, LltPowerModes, LltRefreshRates, LltBattery*), and both
/// the feature name and the value are plain words, so nothing else reaches llt.exe. Discrete-only (MUX, a reboot) asks the person first.</summary>
public sealed class LltGate(ILltRunner runner, Func<string, Task<bool>> confirm)
{
    public static readonly string[] Features = ["hybrid", "power", "refresh", "battery"];
    public static readonly Regex Word = new(@"^[A-Za-z0-9-]{1,32}$");
    public static readonly string[] Keys = ["LltHybridFeature", "LltHybridECO", "LltHybridHYBRID", "LltHybridAUTO", "LltHybridDGPU",
        "LltPowerFeature", "LltPowerModes", "LltRefreshFeature", "LltRefreshRates", "LltBatteryFeature", "LltBatteryConserve", "LltBatteryNormal"];
    static readonly Dictionary<string, string> Defaults = new()
    {
        ["LltHybridFeature"] = "hybrid-mode", ["LltHybridECO"] = "on-igpu-only", ["LltHybridHYBRID"] = "on", ["LltHybridAUTO"] = "on-auto", ["LltHybridDGPU"] = "off",
        ["LltPowerFeature"] = "power-mode", ["LltPowerModes"] = "quiet,balance,performance", ["LltRefreshFeature"] = "refresh-rate", ["LltRefreshRates"] = "60,165",
        ["LltBatteryFeature"] = "battery", ["LltBatteryConserve"] = "conservation", ["LltBatteryNormal"] = "normal",
    };
    readonly SemaphoreSlim _one = new(1, 1); // one switch at a time, in click order

    /// <param name="value">hybrid: ECO / HYBRID / AUTO / DGPU (mapped through LltHybrid&lt;MODE&gt;); the others: the Legion Toolkit value itself.</param>
    public async Task<GateResult> SetAsync(string feature, string value, IReadOnlyDictionary<string, string> settings)
    {
        string S(string k) => settings.TryGetValue(k, out var v) && !string.IsNullOrWhiteSpace(v) ? v.Trim() : Defaults[k];
        var allowed = feature switch
        {
            "hybrid" => value is "ECO" or "HYBRID" or "AUTO" or "DGPU" ? [S("LltHybrid" + value)] : [],
            "power" => S("LltPowerModes").Split(',', StringSplitOptions.TrimEntries),
            "refresh" => S("LltRefreshRates").Split(',', StringSplitOptions.TrimEntries),
            "battery" => [S("LltBatteryConserve"), S("LltBatteryNormal")],
            _ => (string[]?)null,
        };
        if (allowed is null) return new(false, "not a Legion Toolkit feature");
        var arg = feature == "hybrid" ? allowed.FirstOrDefault() : allowed.FirstOrDefault(a => a.Equals(value, StringComparison.OrdinalIgnoreCase));
        var name = S("Llt" + char.ToUpperInvariant(feature[0]) + feature[1..] + "Feature");
        if (arg is null || !Word.IsMatch(arg)) return new(false, "not an allowed value");
        if (!Word.IsMatch(name)) return new(false, "bad feature name in settings");
        if (feature == "hybrid" && value == "DGPU" && !await confirm("discrete GPU only (needs a reboot)")) return new(false, "not confirmed");
        await _one.WaitAsync();
        try
        {
            var code = await Task.Run(() => runner.Set(name, arg));
            return code == 0 ? new(true, "ran") : new(false, $"exit {code}");
        }
        catch (Exception e) { return new(false, "failed: " + e.Message); }
        finally { _one.Release(); }
    }
}
