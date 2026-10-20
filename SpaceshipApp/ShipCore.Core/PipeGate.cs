namespace ShipCore.Core;

public sealed record Hello(string Nonce, int Pid, string Session);

/// <summary>Handshake state for the host <-> JARVIS pipes: nothing is sent to a peer until its hello matches the nonce and session we issued and the pid is the one the OS says is connected.</summary>
public sealed class PipeGate
{
    private readonly IClock _clock;
    private readonly string _nonce, _session;
    private readonly DateTimeOffset _issued;
    private readonly TimeSpan _ttl;
    public bool Verified { get; private set; }

    public PipeGate(IClock clock, string nonce, string session, TimeSpan ttl) { _clock = clock; _nonce = nonce; _session = session; _ttl = ttl; _issued = clock.Now; }

    /// <param name="peerPid">The connected client's process id as reported by the OS, not by the message.</param>
    public bool Verify(Hello h, int peerPid)
    {
        if (Verified) return false; // one hello per gate; a replay is refused
        var ok = _clock.Now - _issued <= _ttl && h.Pid == peerPid &&
                 System.Security.Cryptography.CryptographicOperations.FixedTimeEquals(System.Text.Encoding.UTF8.GetBytes(h.Nonce), System.Text.Encoding.UTF8.GetBytes(_nonce)) &&
                 h.Session == _session;
        Verified = ok;
        return ok;
    }

    /// <summary>The only way outbound data gets through: false until verified.</summary>
    public bool TrySend(Action send) { if (!Verified) return false; send(); return true; }
}
