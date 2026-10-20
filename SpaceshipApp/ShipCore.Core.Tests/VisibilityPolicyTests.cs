namespace ShipCore.Core.Tests;

public class VisibilityPolicyTests
{
    private static readonly Rect Screen = new(0, 0, 2560, 1600);
    private static WindowSnapshot Snap(WindowInfo? fg, NotificationState n = NotificationState.AcceptsNotifications, params string[] procs) => new(fg, Screen, n, procs);
    private static WindowInfo W(string cls, Rect b, bool ours = false, string proc = "app.exe") => new(cls, proc, b, ours);
    private readonly VisibilityPolicy _p = new(new[] { "LockDownBrowser.exe", "  examapp " });

    [Fact] public void NothingInFrontShows() => Assert.Equal(Visibility.Show, _p.Decide(Snap(null)).Visibility);

    [Theory]
    [InlineData("Progman")] [InlineData("WorkerW")] [InlineData("Shell_TrayWnd")] [InlineData("Shell_SecondaryTrayWnd")] [InlineData("progman")]
    public void ShellWindowsCoveringTheScreenAreNeverFullscreenApps(string cls) =>
        Assert.Equal(Visibility.Show, _p.Decide(Snap(W(cls, Screen))).Visibility);

    [Fact] public void OurOwnWindowNeverHidesUs() => Assert.Equal(Visibility.Show, _p.Decide(Snap(W("Ship", Screen, ours: true))).Visibility);

    [Fact] public void AGameCoveringTheMonitorHides() => Assert.Equal(Visibility.Hide, _p.Decide(Snap(W("UnrealWindow", Screen))).Visibility);

    [Fact] public void FrameRoundingOfOnePixelStillCounts() =>
        Assert.Equal(Visibility.Hide, _p.Decide(Snap(W("G", new Rect(1, 1, 2559, 1599)))).Visibility);

    [Fact] public void AMaximisedWindowAboveTheTaskbarDoesNotHide() =>
        Assert.Equal(Visibility.Show, _p.Decide(Snap(W("Chrome_WidgetWin_1", new Rect(0, 0, 2560, 1560)))).Visibility);

    [Fact] public void AWindowOnAnotherMonitorDoesNotHide() =>
        Assert.Equal(Visibility.Show, _p.Decide(Snap(W("G", new Rect(2560, 0, 5120, 1600)))).Visibility);

    [Theory]
    [InlineData(NotificationState.Busy)] [InlineData(NotificationState.RunningD3DFullScreen)] [InlineData(NotificationState.PresentationMode)]
    public void WindowsFullscreenStatesHide(NotificationState n) => Assert.Equal(Visibility.Hide, _p.Decide(Snap(null, n)).Visibility);

    [Theory]
    [InlineData("LockDownBrowser.exe")] [InlineData("lockdownbrowser")] [InlineData("EXAMAPP.EXE")]
    public void AnExamProcessSuspendsEvenWhenItIsNotInFront(string proc)
    {
        var d = _p.Decide(Snap(W("Other", new Rect(0, 0, 100, 100)), NotificationState.AcceptsNotifications, "explorer.exe", proc));
        Assert.Equal(Visibility.Suspend, d.Visibility);
        Assert.Contains("exam", d.Reason);
    }

    [Fact] public void SuspendBeatsEverythingElse() =>
        Assert.Equal(Visibility.Suspend, _p.Decide(Snap(W("Progman", Screen), NotificationState.Busy, "LockDownBrowser")).Visibility);

    [Fact] public void AnEmptyConfiguredListNeverSuspends() =>
        Assert.Equal(Visibility.Show, new VisibilityPolicy(new[] { "", "  " }).Decide(Snap(null, NotificationState.AcceptsNotifications, "", "x")).Visibility);
}
