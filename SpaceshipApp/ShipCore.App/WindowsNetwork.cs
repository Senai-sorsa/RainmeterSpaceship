using System.Net.NetworkInformation;
using ShipCore.Core;

// Byte counters of the up network interfaces, summed. Read-only. Loopback and tunnel adapters are left out, so a VPN does not count twice.
sealed class WindowsNetwork : INetworkCounters
{
    public NetCounters Read()
    {
        ulong received = 0, sent = 0;
        foreach (var ni in NetworkInterface.GetAllNetworkInterfaces())
        {
            if (ni.OperationalStatus != OperationalStatus.Up || ni.NetworkInterfaceType is NetworkInterfaceType.Loopback or NetworkInterfaceType.Tunnel) continue;
            try
            {
                var s = ni.GetIPv4Statistics();
                received += (ulong)s.BytesReceived;
                sent += (ulong)s.BytesSent;
            }
            catch (NetworkInformationException) { } // an adapter with no IPv4 has no statistics; skip it
        }
        return new NetCounters(received, sent);
    }
}
