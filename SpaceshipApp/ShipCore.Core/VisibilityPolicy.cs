namespace ShipCore.Core;

public enum Visibility { Show, Hide, Suspend }
public sealed record VisibilityDecision(Visibility Visibility, string Reason);

/// <summary>Pure decision from a snapshot: stay out of the way of fullscreen apps and of exam browsers. No window handles, no timers.</summary>
public sealed class VisibilityPolicy
{
    // The desktop itself and the taskbar are never "a fullscreen app", whatever their bounds say.
    private static readonly HashSet<string> Shell = new(StringComparer.OrdinalIgnoreCase)
        { "Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd" };

    private readonly HashSet<string> _exam;

    /// <param name="examProcesses">Process names (with or without .exe) that make the HUD suspend itself. Configured by the user.</param>
    public VisibilityPolicy(IEnumerable<string> examProcesses) =>
        _exam = examProcesses.Select(Norm).Where(n => n.Length > 0).ToHashSet(StringComparer.OrdinalIgnoreCase);

    private static string Norm(string p) { p = p.Trim(); return p.EndsWith(".exe", StringComparison.OrdinalIgnoreCase) ? p[..^4] : p; }

    public VisibilityDecision Decide(WindowSnapshot s)
    {
        var hit = s.RunningProcesses.FirstOrDefault(p => _exam.Contains(Norm(p)));
        if (hit is not null) return new(Visibility.Suspend, "exam process running: " + Norm(hit));
        if (s.Notification is NotificationState.Busy or NotificationState.RunningD3DFullScreen or NotificationState.PresentationMode)
            return new(Visibility.Hide, "windows reports a fullscreen or presentation app");
        var f = s.Foreground;
        if (f is null || f.IsOurs || Shell.Contains(f.ClassName)) return new(Visibility.Show, "desktop or shell in front");
        // 1 px of slack: frames are rounded; a maximised window with a taskbar does not cover the monitor, so it stays visible.
        return f.Bounds.Contains(s.Monitor, 1) ? new(Visibility.Hide, "foreground window covers the monitor") : new(Visibility.Show, "no fullscreen window");
    }
}
