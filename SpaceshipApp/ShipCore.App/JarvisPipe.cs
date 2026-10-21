using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using ShipCore.Core;

// One JARVIS client at a time on a per-run pipe. The name, nonce and session go to a session file in the user's temp folder; JARVIS reads it and must present them back.
sealed class JarvisPipe : IDisposable
{
    readonly string _pipe;
    readonly string _nonce = Convert.ToHexString(RandomNumberGenerator.GetBytes(16)).ToLowerInvariant();
    readonly string _session = Guid.NewGuid().ToString("N");
    readonly string _sessionFile = Path.Combine(Path.GetTempPath(), "spaceship-app", "host-session.json");
    readonly IClock _clock;
    readonly CancellationTokenSource _stop = new();

    public JarvisPipe(IClock clock)
    {
        _clock = clock;
        var user = new string(Environment.UserName.Where(c => char.IsAsciiLetterOrDigit(c) || c is '.' or '_' or '-').Take(64).ToArray());
        _pipe = $"SpaceshipHost-{(user.Length == 0 ? "user" : user)}-{_session}";
    }

    public void Start()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_sessionFile)!);
        File.WriteAllText(_sessionFile, HostPipeWire.SessionJson(new SessionFile(_pipe, _nonce, _session, Environment.ProcessId)));
        _ = Task.Run(() => Serve(_stop.Token));
    }

    async Task Serve(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                using var pipe = new NamedPipeServerStream(_pipe, PipeDirection.InOut, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
                await pipe.WaitForConnectionAsync(ct);
                await Talk(pipe, ct);
            }
            catch (Exception e) when (e is IOException or OperationCanceledException or ObjectDisposedException)
            {
                if (ct.IsCancellationRequested) return;
                // a client that drops or stalls mid-hello is only that client's problem; the next one gets a fresh pipe
            }
        }
    }

    async Task Talk(NamedPipeServerStream pipe, CancellationToken ct)
    {
        // The hello must arrive within 10 s and fit in 1 KiB, so a stalled or noisy peer is cut off.
        using var helloDeadline = CancellationTokenSource.CreateLinkedTokenSource(ct);
        helloDeadline.CancelAfter(TimeSpan.FromSeconds(10));
        var line = new List<byte>();
        var one = new byte[1];
        while (line.Count < 1024 && await pipe.ReadAsync(one, helloDeadline.Token) == 1 && one[0] != '\n') line.Add(one[0]);

        var gate = new PipeGate(_clock, _nonce, _session, TimeSpan.FromSeconds(10));
        var hello = HostPipeWire.ParseHello(Encoding.UTF8.GetString(line.ToArray()));
        if (hello is null || !gate.Verify(hello, ClientPid(pipe))) return;

        await pipe.WriteAsync(Encoding.UTF8.GetBytes(HostPipeWire.Ready + "\n"), ct);
        await pipe.FlushAsync(ct);
        // The host sends nothing else yet, so hold the connection until JARVIS closes it.
        while (await pipe.ReadAsync(one, ct) > 0) { }
    }

    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetNamedPipeClientProcessId(IntPtr pipe, out uint pid);

    static int ClientPid(NamedPipeServerStream pipe) => GetNamedPipeClientProcessId(pipe.SafePipeHandle.DangerousGetHandle(), out var pid) ? (int)pid : -1;

    public void Dispose()
    {
        _stop.Cancel();
        try { File.Delete(_sessionFile); } catch (IOException) { }
    }
}
