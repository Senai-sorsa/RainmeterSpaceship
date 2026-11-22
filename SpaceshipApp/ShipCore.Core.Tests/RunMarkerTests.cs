namespace ShipCore.Core.Tests;

public sealed class RunMarkerTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "shipcore-" + Guid.NewGuid().ToString("N"));
    private string Path_ => Path.Combine(_dir, "running.marker");

    public void Dispose() { if (Directory.Exists(_dir)) Directory.Delete(_dir, true); }

    [Fact]
    public void NoMarkerMeansTheLastRunWasClean()
    {
        Assert.False(new RunMarker(Path_).LastRunEndedUncleanly());
    }

    [Fact]
    public void AMarkerLeftBehindMeansTheLastRunWasUnclean()
    {
        var first = new RunMarker(Path_);
        Assert.True(first.MarkRunning(DateTimeOffset.Now));
        // no MarkCleanExit: the process went away
        Assert.True(new RunMarker(Path_).LastRunEndedUncleanly());
    }

    [Fact]
    public void ACleanExitRemovesTheMarkerAndRepeatIsHarmless()
    {
        var m = new RunMarker(Path_);
        m.MarkRunning(DateTimeOffset.Now);
        m.MarkCleanExit();
        m.MarkCleanExit();
        Assert.False(new RunMarker(Path_).LastRunEndedUncleanly());
    }
}
