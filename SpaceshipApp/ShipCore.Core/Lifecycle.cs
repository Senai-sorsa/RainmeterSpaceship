namespace ShipCore.Core;

public enum TrayCommand { Refresh, Quit, SwitchToRainmeter }

/// <summary>Close, refresh and sign-out behaviour as plain logic. The host forwards WM_QUERYENDSESSION / WM_ENDSESSION / tray clicks here.</summary>
public sealed class Lifecycle
{
    public static readonly IReadOnlyList<(TrayCommand Id, string Label)> TrayMenu =
        new[] { (TrayCommand.Refresh, "Refresh"), (TrayCommand.SwitchToRainmeter, "Switch to Rainmeter"), (TrayCommand.Quit, "Quit") };

    private readonly Action _teardown;
    private readonly Action _refresh;
    private readonly Action _launchRainmeter;
    private int _tornDown;
    public Lifecycle(Action teardown, Action refresh, Action launchRainmeter) { _teardown = teardown; _refresh = refresh; _launchRainmeter = launchRainmeter; }

    /// <summary>Never blocks a shutdown or sign-out.</summary>
    public bool OnQueryEndSession() => true;

    /// <summary>Runs teardown once, whichever of quit, end-of-session or switch gets here first.</summary>
    public void Teardown() { if (Interlocked.Exchange(ref _tornDown, 1) == 0) _teardown(); }

    public void OnEndSession(bool ending) { if (ending) Teardown(); }

    /// <returns>true when the app should exit now.</returns>
    public bool Handle(TrayCommand c)
    {
        switch (c)
        {
            case TrayCommand.Refresh: _refresh(); return false;
            case TrayCommand.SwitchToRainmeter: Teardown(); _launchRainmeter(); return true;
            case TrayCommand.Quit: Teardown(); return true;
            default: return false;
        }
    }
}
