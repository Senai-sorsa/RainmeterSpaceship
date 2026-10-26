using System.Net.NetworkInformation;
using System.Net.Sockets;
using ShipCore.Core;

// The network block's ping, LAN and WAN rows on the skin's schedule (ping 10 s, LAN 30 s, WAN 300 s) and the centre's S&P 500
// (5 min open, 1 h closed), only while the HUD is shown. Runs on the UI thread with async I/O; a message goes to the page when
// a value changes.
sealed class NetRunner(Func<string?> pingHost, Func<bool> shown, Action<string> post) : IDisposable
{
    static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(10), MaxResponseContentBufferSize = 65536 }; // the Yahoo chart reply is a few KB
    readonly System.Windows.Forms.Timer _tick = new() { Interval = 2000 };
    readonly Ping _pinger = new();
    DateTime _pingDue, _lanDue, _wanDue, _spxDue;
    bool _pinging, _asking, _spxAsking;
    long? _ping;
    string? _lan, _wan, _sent, _spxSent;

    public void Start()
    {
        _tick.Tick += (_, _) => Tick();
        _tick.Start();
    }

    /// <summary>The last messages, for a page that just loaded.</summary>
    public IEnumerable<string> Last => new[] { _sent, _spxSent }.OfType<string>();

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
        if (now >= _spxDue && !_spxAsking)
        {
            _spxDue = now.AddSeconds(Spx.NextSeconds(true)); _spxAsking = true; // a failed fetch retries in 5 min
            try
            {
                // Yahoo refuses requests without a browser user agent; the skin sends the same one.
                using var req = new HttpRequestMessage(HttpMethod.Get, Spx.Url);
                req.Headers.TryAddWithoutValidation("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36");
                using var res = await Http.SendAsync(req);
                if (res.IsSuccessStatusCode && Spx.Parse(await res.Content.ReadAsStringAsync(), DateTimeOffset.UtcNow.ToUnixTimeSeconds()) is { } r)
                {
                    _spxDue = now.AddSeconds(Spx.NextSeconds(r.Open));
                    if (r.Json != _spxSent) { _spxSent = r.Json; post(r.Json); }
                }
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException) { } // keep the last reading
            finally { _spxAsking = false; }
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
