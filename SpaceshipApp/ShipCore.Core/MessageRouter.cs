using System.Text.Json;

namespace ShipCore.Core;

public sealed record Routed(string? Reply, string? Problem);

/// <summary>Sends one WebView message to the store or the action gate. Protocol checks every message first; a refused message gets no reply and no effect.</summary>
public sealed class MessageRouter
{
    private readonly ConfigSchema _schema;
    private readonly ConfigStore _store;
    private readonly ActionGate _gate;
    private readonly Func<string, Task<bool>> _confirm;

    /// <param name="confirm">Asks the person before a power action. Never reached from the page today: the schema lists no power actions.</param>
    public MessageRouter(ConfigSchema schema, ConfigStore store, ActionGate gate, Func<string, Task<bool>> confirm)
    {
        _schema = schema; _store = store; _gate = gate; _confirm = confirm;
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
                return Reply(new { type = "config", values = _store.Get(keys) });
            }
            case "config.set":
            {
                var r = _store.Set(m.GetProperty("key").GetString()!, m.GetProperty("value").GetString()!);
                return Reply(new { type = "config.result", id = m.GetProperty("id").GetInt64(), ok = r.Ok, error = r.Error });
            }
            case "action":
            {
                var id = m.GetProperty("id").GetString()!;
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
            default: return new(null, null); // setup.* and aboutme.* are accepted but not handled in the host yet
        }
    }

    private static Routed Reply(object reply) => new(JsonSerializer.Serialize(reply), null);
}
