namespace ShipCore.Core;

/// <summary>A background runner's shutdown switch. Work in flight takes <see cref="Token"/>; results go out through <see cref="Post"/>,
/// which stops calling the page once the runner is disposed, so a late result never reaches a released WebView.</summary>
public sealed class RunnerLifetime : IDisposable
{
    // Never disposed: a CancellationTokenSource without a timer or wait handle holds nothing unmanaged, and leaving it
    // undisposed keeps Token (and Register on it) valid for work that finishes after Dispose.
    private readonly CancellationTokenSource _cts = new();
    private int _disposed;

    public RunnerLifetime() { Token = _cts.Token; }

    public CancellationToken Token { get; }

    public bool Disposed => Volatile.Read(ref _disposed) != 0;

    /// <returns>false, without calling <paramref name="post"/>, once disposed; false when <paramref name="post"/> throws ObjectDisposedException.</returns>
    public bool Post(Action<string> post, string json)
    {
        if (Disposed) return false;
        try { post(json); return true; }
        catch (ObjectDisposedException) { return false; }
    }

    public void Dispose()
    {
        if (Interlocked.Exchange(ref _disposed, 1) != 0) return;
        _cts.Cancel();
    }
}
