namespace ShipCore.Core;

/// <summary>Total bytes received and sent by the up network interfaces, as the OS counts them.</summary>
public readonly record struct NetCounters(ulong Received, ulong Sent);

/// <summary>Reads the interface counters. The Windows host implements it with NetworkInterface; tests use a fake.</summary>
public interface INetworkCounters { NetCounters Read(); }

public static class NetworkRate
{
    /// <returns>Bytes per second down and up between two samples. Null when no time passed or a counter went backwards (an interface went away or the counter reset).</returns>
    public static (double Down, double Up)? Rate(NetCounters prev, NetCounters cur, double seconds)
    {
        if (seconds <= 0 || cur.Received < prev.Received || cur.Sent < prev.Sent) return null;
        return ((cur.Received - prev.Received) / seconds, (cur.Sent - prev.Sent) / seconds);
    }
}
