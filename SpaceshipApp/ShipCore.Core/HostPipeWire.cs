using System.Text.Json;
using System.Text.RegularExpressions;

namespace ShipCore.Core;

/// <summary>What the host writes to the session file so JARVIS can find its pipe. Read by jarvislib/host_pipe.py.</summary>
public sealed record SessionFile(string Pipe, string Nonce, string Session, int Pid);

/// <summary>Wire format of the host <-> JARVIS pipe: newline-delimited JSON. The same verdicts are tested from Python against contract/fixtures/host-pipe.json.</summary>
public static class HostPipeWire
{
    private static readonly Regex Name = new(@"^SpaceshipHost-[A-Za-z0-9._-]{1,64}-[0-9a-f]{32}\z", RegexOptions.CultureInvariant); // \z: a trailing newline must not pass, as in Python's fullmatch

    public const string Ready = "{\"type\":\"ready\"}";

    /// <summary>JARVIS only connects to a name of this shape, so a bad session file cannot point it at another pipe.</summary>
    public static bool PipeNameOk(string name) => Name.IsMatch(name);

    // camelCase keys, as jarvislib/host_pipe.py reads them ("pipe", "nonce", "session", "pid")
    static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };

    public static string SessionJson(SessionFile s) => JsonSerializer.Serialize(s, Json);

    public static SessionFile? ParseSession(string json)
    {
        try { return JsonSerializer.Deserialize<SessionFile>(json, Json) is { Pipe: not null } s && PipeNameOk(s.Pipe) ? s : null; }
        catch (JsonException) { return null; }
    }

    /// <returns>The hello, or null when the line is not a well-formed one.</returns>
    public static Hello? ParseHello(string line)
    {
        try
        {
            using var doc = JsonDocument.Parse(line);
            var r = doc.RootElement;
            if (r.GetProperty("type").GetString() != "hello") return null;
            return new Hello(r.GetProperty("nonce").GetString()!, r.GetProperty("pid").GetInt32(), r.GetProperty("session").GetString()!);
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException or FormatException) { return null; }
    }
}
