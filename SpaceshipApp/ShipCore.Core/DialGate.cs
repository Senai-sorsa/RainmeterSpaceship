using System.Text.Json;

namespace ShipCore.Core;

/// <summary>The systems dial's writes to Windows. Every value is checked here before anything runs. Power mode and refresh rate also need a yes from the person on the host's own dialog.</summary>
public sealed class DialGate
{
    public static readonly string[] Modes = { "quiet", "balance", "performance" };
    public static readonly string[] Rates = { "60", "165" };
    private static readonly string[] Percent = { "brightness", "volume", "mic" };

    private readonly IDialActions _actions;
    private readonly Func<string, Task<bool>> _confirm;
    private readonly SemaphoreSlim _one = new(1, 1); // one write at a time, in click order

    /// <param name="confirm">Asks the person before a power mode or refresh change. Never called for a percent control.</param>
    public DialGate(IDialActions actions, Func<string, Task<bool>> confirm) { _actions = actions; _confirm = confirm; }

    public async Task<GateResult> SetAsync(string control, JsonElement value)
    {
        if (Array.IndexOf(Percent, control) >= 0)
        {
            if (!Whole(value, out var pct)) return new(false, "percent must be a whole number from 0 to 100");
            return await Try(() =>
            {
                if (control == "brightness") _actions.Brightness(pct);
                else if (control == "volume") _actions.Volume(pct);
                else _actions.Mic(pct);
            });
        }
        switch (control)
        {
            case "power":
            {
                if (value.ValueKind != JsonValueKind.String || Array.IndexOf(Modes, value.GetString()) < 0) return new(false, "not a power mode");
                var mode = value.GetString()!;
                if (!await _confirm($"power mode {mode}")) return new(false, "not confirmed");
                return await Try(() => _actions.PowerMode(mode));
            }
            case "refresh":
            {
                if (value.ValueKind != JsonValueKind.String || Array.IndexOf(Rates, value.GetString()) < 0) return new(false, "not a refresh rate");
                var hz = int.Parse(value.GetString()!);
                if (!await _confirm($"refresh rate {hz} Hz")) return new(false, "not confirmed");
                return await Try(() => _actions.Refresh(hz));
            }
            default: return new(false, "not a dial control");
        }
    }

    static bool Whole(JsonElement v, out int n)
    {
        n = 0;
        return v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out n) && n >= 0 && n <= 100;
    }

    // A failed Windows call throws; it is reported as not run, with the reason, and nothing is retried.
    // It runs off the caller's thread (the host's UI thread), so a slow tool cannot freeze the HUD.
    async Task<GateResult> Try(Action run)
    {
        await _one.WaitAsync();
        try { await Task.Run(run); return new(true, "ran"); }
        catch (Exception e) { return new(false, "failed: " + e.Message); }
        finally { _one.Release(); }
    }
}
