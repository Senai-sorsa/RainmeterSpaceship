using System.Net;
using System.Net.Sockets;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>The network block's ping, LAN and WAN rows (Right\SysInfo.ini: PingPlugin every 10 s, SysInfo IP every 30 s, api.ipify.org every 300 s).</summary>
public static class NetInfo
{
    public const string WanUrl = "https://api.ipify.org";
    static readonly Regex Host = new(@"^[A-Za-z0-9.:-]{1,64}$");

    /// <summary>The PingHost setting if it has the schema's shape, else the skin's default.</summary>
    public static string PingHost(string? setting) => setting is not null && Host.IsMatch(setting) ? setting : "1.1.1.1";

    /// <summary>A dotted IPv4 address from untrusted text (the WAN reply), or null.</summary>
    public static string? Ipv4(string? text)
    {
        var t = text?.Trim() ?? "";
        return Regex.IsMatch(t, @"^\d{1,3}(\.\d{1,3}){3}$") && IPAddress.TryParse(t, out var a) && a.AddressFamily == AddressFamily.InterNetwork ? a.ToString() : null;
    }

    /// <param name="pingMs">Round trip, 0 when lost, null before the first ping.</param>
    /// <param name="lan">This PC's address, "" when it has none, null before the first read.</param>
    /// <param name="wan">The public address, "" when the lookup failed, null before the first one.</param>
    public static string ToJson(long? pingMs, string? lan, string? wan) =>
        JsonSerializer.Serialize(new { type = "net.update", ping = pingMs, lan, wan });
}
