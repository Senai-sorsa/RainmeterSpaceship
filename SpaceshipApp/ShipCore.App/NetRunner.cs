using System.Net.NetworkInformation;
using System.Net.Sockets;
using ShipCore.Core;

// The network block's ping, LAN and WAN rows on the skin's schedule (ping 10 s, LAN 30 s, WAN 300 s), only while the HUD
// is shown. Runs on the UI thread with async I/O; a net.update goes to the page when a value changes.
sealed class NetRunner(Func<string?> pingHost, Func<bool> shown, Action<string> post) : IDisposable
{
    static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(10), MaxResponseContentBufferSize = 1024 };
    readonly System.Windows.Forms.Timer _tick = new() { Interval = 2000 };
    readonly Ping _pinger = new();
    DateTime _pingDue, _lanDue, _wanDue;
    bool _pinging, _asking;
    long? _ping;
    string? _lan, _wan, _sent;

    public void Start()
    {
        _tick.Tick += (_, _) => Tick();
        _tick.Start();
    }

    /// <summary>The last message, for a page that just loaded.</summary>
    public string? Last => _sent;

    async void Tick()
    {
        if (!shown()) return;
        var now = DateTime.UtcNow;
        if (now >= _lanDue) { _lanDue = now.AddSeconds(30); _lan = Lan(); Send(); }
        if (now >= _pingDue && !_pinging)
        {
            _pingDue = now.AddSeconds(10); _pinging = true;
            try
            {
                var r = await _pinger.SendPingAsync(NetInfo.PingHost(pingHost()), 3000);
                _ping = r.Status == IPStatus.Success ? Math.Max(1, r.RoundtripTime) : 0;
            }
            catch (Exception e) when (e is PingException or InvalidOperationException) { _ping = 0; }
            finally { _pinging = false; }
            Send();
        }
        if (now >= _wanDue && !_asking)
        {
            _wanDue = now.AddSeconds(300); _asking = true;
            try { _wan = NetInfo.Ipv4(await Http.GetStringAsync(NetInfo.WanUrl)) ?? ""; }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException) { _wan = ""; }
            finally { _asking = false; }
            Send();
        }
    }

    void Send()
    {
        var json = NetInfo.ToJson(_ping, _lan, _wan);
        if (json == _sent) return;
        _sent = json;
        post(json);
    }

    // The address of the first connected adapter with an IPv4 gateway (Rainmeter SysInfo IP_ADDRESS Best), or "".
    static string Lan()
    {
        try
        {
            foreach (var n in NetworkInterface.GetAllNetworkInterfaces())
            {
                if (n.OperationalStatus != OperationalStatus.Up || n.NetworkInterfaceType is NetworkInterfaceType.Loopback or NetworkInterfaceType.Tunnel) continue;
                var ip = n.GetIPProperties();
                if (!ip.GatewayAddresses.Any(g => g.Address.AddressFamily == AddressFamily.InterNetwork && !g.Address.Equals(System.Net.IPAddress.Any))) continue;
                var a = ip.UnicastAddresses.FirstOrDefault(u => u.Address.AddressFamily == AddressFamily.InterNetwork);
                if (a is not null) return a.Address.ToString();
            }
        }
        catch (NetworkInformationException) { }
        return "";
    }

    public void Dispose() { _tick.Stop(); _tick.Dispose(); _pinger.Dispose(); }
}
