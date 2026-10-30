namespace ShipCore.Core;

/// <summary>P6-2: decides when the host restarts a JARVIS that died. Pure logic: the caller starts the process.
/// Only a JARVIS that was seen online and then went offline is restarted (never a first start, never after the Control Center's quit).
/// Waits 2, 5, then 15 s between tries; gives up after 5 tries inside 10 minutes.</summary>
public sealed class JarvisSupervisor
{
    static readonly int[] Backoff = [2, 5, 15];
    const int MaxTries = 5;
    const long WindowS = 600;
    readonly Queue<long> _tries = new();
    bool _seenOnline, _quit;
    long _due;

    public bool GaveUp { get; private set; }

    /// <summary>The user asked JARVIS to stop: stay down until <see cref="Started"/>.</summary>
    public void Quit() => _quit = true;

    /// <summary>The user started JARVIS again: supervision and the try count begin afresh.</summary>
    public void Started() { _quit = false; GaveUp = false; _tries.Clear(); _due = 0; }

    /// <param name="enabled">Asked only when a restart is due (JarvisAutoStart and JarvisEnabled).</param>
    /// <returns>True when the caller should start JARVIS now.</returns>
    public bool Tick(bool offline, long nowS, Func<bool> enabled)
    {
        if (!offline) { _seenOnline = true; _due = 0; GaveUp = false; return false; }
        if (!_seenOnline || _quit) return false;
        while (_tries.Count > 0 && nowS - _tries.Peek() > WindowS) _tries.Dequeue();
        if (_tries.Count >= MaxTries) { GaveUp = true; return false; }
        if (_due == 0) { _due = nowS + Backoff[Math.Min(_tries.Count, Backoff.Length - 1)]; return false; }
        if (nowS < _due) return false;
        _due = 0;
        if (!enabled()) return false;
        _tries.Enqueue(nowS);
        return true;
    }
}
