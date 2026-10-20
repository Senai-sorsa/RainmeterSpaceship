namespace ShipCore.Core;

public sealed record GateResult(bool Ran, string Reason);

/// <summary>The only road from a message to an OS action. The id must be on the list and, for power actions, a person must confirm; model or WebView text alone never does anything.</summary>
public sealed class ActionGate
{
    private readonly IPowerActions _power;
    private readonly IShell _shell;
    public ActionGate(IPowerActions power, IShell shell) { _power = power; _shell = shell; }

    /// <param name="confirm">Asks the person (a dialog the host owns). Called only for power actions.</param>
    public async Task<GateResult> PowerAsync(string id, Func<string, Task<bool>> confirm)
    {
        Action? run = id switch { "shutdown" => _power.Shutdown, "restart" => _power.Restart, "sleep" => _power.Sleep, "lock" => _power.Lock, _ => null };
        if (run is null) return new(false, "not an allowed power action");
        if (!await confirm(id)) return new(false, "not confirmed");
        run();
        return new(true, "ran");
    }

    public GateResult Flow(string flow)
    {
        if (flow is not ("gmail" or "calendars" or "obsidian")) return new(false, "unknown flow");
        _shell.OpenFlow(flow);
        return new(true, "ran");
    }
}
