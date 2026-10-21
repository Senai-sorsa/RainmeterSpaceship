namespace ShipCore.Core;

/// <summary>Runs the kill action on the first press only. The action stops the app and everything it started.</summary>
public sealed class KillSwitch
{
    private readonly Action _killTree;
    private int _fired;

    public KillSwitch(Action killTree) { _killTree = killTree; }

    /// <returns>true when this press ran the kill.</returns>
    public bool Fire()
    {
        if (Interlocked.Exchange(ref _fired, 1) != 0) return false;
        _killTree();
        return true;
    }
}
