using System.Net.Security;
using System.Net.Sockets;
using System.Security.Authentication;
using System.Text;
using System.Text.RegularExpressions;
using ShipCore.Core;

// The upkeep block's Gmail unread count, as the skin's ShipCore MailLoop does it: the address and app password (DPAPI,
// %LOCALAPPDATA%\SpaceshipHUD\gmail.dat, saved by ShipCore setup-gmail) sign in over IMAP/TLS and read STATUS INBOX (UNSEEN).
// Every 2 min while the HUD is shown, into Data\mail.txt (JARVIS reads it too), and a status.update to the page.
// The login is a secret: it is never logged or sent to the page; the page gets the count or a short reason.
sealed class MailRunner(string data, Func<bool> shown, Action<string> post, Func<int>? factor = null) : IDisposable
{
    readonly System.Windows.Forms.Timer _tick = new() { Interval = 3000 }; // 120 s after the first check
    readonly string _file = Path.Combine(data, "mail.txt");
    bool _fetching;

    /// <summary>The last message, for a page that just loaded.</summary>
    public string? Last { get; private set; }

    public void Start()
    {
        _tick.Tick += (_, _) => Tick();
        _tick.Start();
    }

    async void Tick()
    {
        if (!shown() || _fetching) { if (_tick.Interval < 3000) _tick.Interval = 3000; return; } // after Soon(): don't spin while hidden or busy
        _tick.Interval = PowerPolicy.Scale(120000, factor?.Invoke() ?? 1);
        _fetching = true;
        try
        {
            var body = await Task.Run(Check);
            var text = $"T {DateTimeOffset.UtcNow.ToUnixTimeSeconds()}\n{body}\n";
            try
            {
                var tmp = _file + ".tmp" + Environment.ProcessId;
                File.WriteAllText(tmp, text, new UTF8Encoding(false));
                File.Move(tmp, _file, overwrite: true);
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException) { } // the page still gets the count
            Last = StatusScripts.Mail(text);
            post(Last);
        }
        finally { _fetching = false; }
    }

    static async Task<string> Check()
    {
        var cred = CalendarRunner.Unprotect(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SpaceshipHUD", "gmail.dat"));
        if (cred is null) return "OFF";
        var p = cred.Split('\n');
        if (p.Length < 2) return "ERR bad saved login";
        try { return "UNREAD " + await Unread(p[0].Trim(), p[1].Trim()); }
        catch (Exception e) when (e is IOException or SocketException or AuthenticationException or OperationCanceledException or InvalidDataException)
        {
            return "ERR " + (e is InvalidDataException ? e.Message : e is OperationCanceledException ? "no connection" : e.GetType().Name);
        }
    }

    static string Quote(string s) => "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";

    static async Task<int> Unread(string user, string pass)
    {
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        using var tcp = new TcpClient();
        await tcp.ConnectAsync("imap.gmail.com", 993, cts.Token);
        await using var ssl = new SslStream(tcp.GetStream(), false);
        await ssl.AuthenticateAsClientAsync(new SslClientAuthenticationOptions { TargetHost = "imap.gmail.com" }, cts.Token);
        using var rd = new StreamReader(ssl, Encoding.ASCII);
        await using var wr = new StreamWriter(ssl, Encoding.ASCII) { NewLine = "\r\n", AutoFlush = true };
        await rd.ReadLineAsync(cts.Token); // greeting
        async Task<string> Imap(string tag, string cmd)
        {
            await wr.WriteLineAsync(tag + " " + cmd);
            var sb = new StringBuilder();
            while (true)
            {
                var line = await rd.ReadLineAsync(cts.Token) ?? throw new IOException("connection closed");
                sb.Append(line).Append('\n');
                if (line.StartsWith(tag + " ", StringComparison.Ordinal)) return sb.ToString();
            }
        }
        if (!Regex.IsMatch(await Imap("a1", "LOGIN " + Quote(user) + " " + Quote(pass)), @"^a1 OK", RegexOptions.Multiline))
            throw new InvalidDataException("login refused - check the address and app password");
        var m = Regex.Match(await Imap("a2", "STATUS INBOX (UNSEEN)"), @"UNSEEN (\d+)");
        try { await Imap("a3", "LOGOUT"); } catch (IOException) { }
        return m.Success && int.TryParse(m.Groups[1].Value, out var n) ? n : throw new InvalidDataException("no unread count in reply");
    }

    /// <summary>status_block.lua right-click (Data\mail.refresh): check on the next tick instead of in up to 2 min.</summary>
    public void Soon() { _tick.Stop(); _tick.Interval = 1; _tick.Start(); }

    public void Dispose() { _tick.Stop(); _tick.Dispose(); }
}
