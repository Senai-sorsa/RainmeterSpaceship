using System.Text.Json;

namespace ShipCore.Core;

public sealed record Routed(string? Reply, string? Problem);

/// <summary>Sends one WebView message to the store or the action gate. Protocol checks every message first; a refused message gets no reply and no effect.</summary>
public sealed class MessageRouter
{
    private readonly ConfigSchema _schema;
    private readonly IConfigStore _store;
    private readonly ActionGate _gate;
    private readonly Func<string, Task<bool>> _confirm;
    private readonly HostState _state;
    private readonly DialGate? _dial;
    private readonly HitRegions? _hits;
    private readonly Action<string>? _launch, _open;
    private readonly LltGate? _llt;
    private readonly Action<string>? _refresh;
    private readonly Action? _speed;
    private readonly Action<string, string?>? _jarvis;

    /// <param name="confirm">Asks the person before a power action. Never reached from the page today: the schema lists no power actions.</param>
    /// <param name="state">Setup flag and About-me text. Without it they live in memory for this run only.</param>
    /// <param name="launch">Runs an Apps.ini app by id (AppLaunch). Null means app.launch is accepted and ignored.</param>
    /// <param name="open">target.open: Task Manager, the to-do note, a settings page or a media key, from a fixed list (checked by Protocol). Null means it is ignored.</param>
    /// <param name="dial">The systems dial's writes. Null means the dial is not wired and every dial.set is refused.</param>
    /// <param name="llt">The console's Legion Toolkit buttons. Null means every llt.set is refused.</param>
    /// <param name="refresh">status.refresh: reads that block (llt when no kind is given) again now; "apps" for the apps.scan action. Null means it is ignored.</param>
    /// <param name="speed">speed.run: starts the speed test (it reports with status.update). Null means it is ignored.</param>
    /// <param name="jarvis">jarvis.cmd and the jarvis.* actions: a verb from JarvisStatus.Verbs and the asked text. Null means they are ignored.</param>
    /// <param name="hits">Where the page takes the mouse. Null means hit.regions is accepted and ignored.</param>
    public MessageRouter(ConfigSchema schema, IConfigStore store, ActionGate gate, Func<string, Task<bool>> confirm, HostState? state = null, DialGate? dial = null, HitRegions? hits = null, Action<string>? launch = null, Action<string>? open = null, LltGate? llt = null, Action<string>? refresh = null, Action? speed = null, Action<string, string?>? jarvis = null)
    {
        _llt = llt; _refresh = refresh; _speed = speed; _jarvis = jarvis;
        _schema = schema; _store = store; _gate = gate; _confirm = confirm; _state = state ?? new HostState(null); _dial = dial; _hits = hits; _launch = launch; _open = open;
    }

    public async Task<Routed> HandleAsync(string json)
    {
        var problem = Protocol.Problem(json, _schema);
        if (problem is not null) return new(null, problem);
        using var doc = JsonDocument.Parse(json);
        var m = doc.RootElement;
        switch (m.GetProperty("type").GetString())
        {
            case "config.get":
            {
                var keys = m.GetProperty("keys").EnumerateArray().Select(k => k.GetString()!).ToList();
                return Reply(new { type = "config.values", values = _store.Get(keys) });
            }
            case "config.set":
            {
                var key = m.GetProperty("key").GetString()!;
                var r = _store.Set(key, m.GetProperty("value").GetString()!);
                return Reply(new { type = "config.ack", id = m.GetProperty("id").GetInt64(), key, ok = r.Ok, error = r.Error });
            }
            case "setup.get": return Reply(new { type = "setup.state", done = _state.SetupDone });
            case "setup.finish":
                _state.SetSetupDone(true);
                return Reply(new { type = "setup.state", done = true });
            case "aboutme.get": return Reply(new { type = "aboutme.value", text = _state.AboutMe });
            case "aboutme.set":
                _state.SetAboutMe(m.GetProperty("text").GetString()!);
                return Reply(new { type = "aboutme.value", text = _state.AboutMe });
            case "action":
            {
                var id = m.GetProperty("id").GetString()!;
                // Setup actions mirror the mock host: reset clears the flag for the next start, rerun reopens the wizard now.
                if (id == "setup.reset") { _state.SetSetupDone(false); return new(null, null); }
                if (id == "setup.rerun") return Reply(new { type = "setup.state", done = false });
                // the Control Center's assistant buttons (control.lua STOP / FORGET / REINDEX / TRAIN)
                if (id.StartsWith("jarvis.", StringComparison.Ordinal) && JarvisStatus.Verbs.Contains(id[7..])) { _jarvis?.Invoke(id[7..], null); return new(null, null); }
                // the Control Center's Scan apps (controller.lua Rescan): the host reruns the Start-menu scan
                if (id == "apps.scan") { _refresh?.Invoke("apps"); return new(null, null); }
                // Only power ids reach the gate; the other schema actions are not implemented in the host yet.
                if (id is not ("shutdown" or "restart" or "sleep" or "lock")) return new(null, null);
                var g = await _gate.PowerAsync(id, _confirm);
                return Reply(new { type = "action.result", id, ran = g.Ran, reason = g.Reason });
            }
            case "flow.open":
            {
                var flow = m.GetProperty("flow").GetString()!;
                var g = _gate.Flow(flow);
                return Reply(new { type = "flow.result", flow, ran = g.Ran, reason = g.Reason });
            }
            case "dial.set":
            {
                var control = m.GetProperty("control").GetString()!;
                var id = m.GetProperty("id").GetInt64();
                if (_dial is null) return Reply(new { type = "dial.result", id, ran = false, reason = "not wired" });
                var g = await _dial.SetAsync(control, m.GetProperty("value"));
                return Reply(new { type = "dial.result", id, control, ran = g.Ran, reason = g.Reason });
            }
            case "hit.regions":
                _hits?.Set(m);
                return new(null, null);
            case "app.launch":
                _launch?.Invoke(m.GetProperty("id").GetString()!);
                return new(null, null);
            case "target.open":
                _open?.Invoke(m.GetProperty("what").GetString()!);
                return new(null, null);
            case "llt.set":
            {
                var id = m.GetProperty("id").GetInt64();
                var feature = m.GetProperty("feature").GetString()!;
                if (_llt is null) return Reply(new { type = "llt.result", id, feature, ran = false, reason = "not wired" });
                var g = await _llt.SetAsync(feature, m.GetProperty("value").GetString()!, _store.Get(LltGate.Keys));
                if (g.Ran) _refresh?.Invoke("llt");
                return Reply(new { type = "llt.result", id, feature, ran = g.Ran, reason = g.Reason });
            }
            case "status.refresh":
                _refresh?.Invoke(m.TryGetProperty("kind", out var rk) ? rk.GetString()! : "llt");
                return new(null, null);
            case "speed.run":
                _speed?.Invoke();
                return new(null, null);
            case "jarvis.cmd":
                _jarvis?.Invoke(m.GetProperty("cmd").GetString()!, m.TryGetProperty("text", out var jt) && jt.ValueKind == JsonValueKind.String ? jt.GetString() : null);
                return new(null, null);
            default: return new(null, null);
        }
    }

    private static Routed Reply(object reply) => new(JsonSerializer.Serialize(reply), null);
}
