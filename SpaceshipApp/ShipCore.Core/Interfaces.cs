namespace ShipCore.Core;

// Everything the Windows host implements and the tests replace with fakes. Nothing in Core touches the OS.
public interface IClock { DateTimeOffset Now { get; } }
public interface IPowerActions { void Shutdown(); void Restart(); void Sleep(); void Lock(); }
public interface IShell { void OpenFlow(string flow); }
public interface IWindowSnapshotSource { WindowSnapshot Take(); }

public readonly record struct Rect(int Left, int Top, int Right, int Bottom)
{
    public bool Contains(Rect o, int tolerance = 0) =>
        Left <= o.Left + tolerance && Top <= o.Top + tolerance && Right >= o.Right - tolerance && Bottom >= o.Bottom - tolerance;
}

public sealed record WindowInfo(string ClassName, string Process, Rect Bounds, bool IsOurs);

/// <summary>Windows' own "is something fullscreen" answer (SHQueryUserNotificationState).</summary>
public enum NotificationState { NotPresent, Busy, RunningD3DFullScreen, PresentationMode, AcceptsNotifications, QuietTime, App }

public sealed record WindowSnapshot(WindowInfo? Foreground, Rect Monitor, NotificationState Notification, IReadOnlyList<string> RunningProcesses);
