namespace ShipCore.Core;

public enum TrayCommand { Refresh, Quit }

/// <summary>Close, refresh and sign-out behaviour as plain logic. The host forwards WM_QUERYENDSESSION / WM_ENDSESSION / tray clicks here.</summary>
public sealed class Lifecycle
{
    public static readonly IReadOnlyList<(TrayCommand Id, string Label)> TrayMenu =
        new[] { (TrayCommand.Refresh, "Refresh"), (TrayCommand.Quit, "Quit") };

    private readonly Action _teardown;
    private readonly Action _refresh;
    private int _tornDown;
    public Lifecycle(Action teardown, Action refresh) { _teardown = teardown; _refresh = refresh; }

    /// <summary>Never blocks a shutdown or sign-out.</summary>
    public bool OnQueryEndSession() => true;

    /// <summary>Runs teardown once, whichever of quit or end-of-session gets here first.</summary>
    public void Teardown() { if (Interlocked.Exchange(ref _tornDown, 1) == 0) _teardown(); }

    public void OnEndSession(bool ending) { if (ending) Teardown(); }

    /// <returns>true when the app should exit now.</returns>
    public bool Handle(TrayCommand c)
    {
        switch (c)
        {
            case TrayCommand.Refresh: _refresh(); return false;
            case TrayCommand.Quit: Teardown(); return true;
            default: return false;
        }
    }
}
