using System.Text.Json;

namespace ShipCore.Core;

/// <summary>The centre HUD's S&amp;P 500 tape (Center\HUD.ini mSPX + hud.lua OnSPX): Yahoo's chart JSON for ^GSPC.</summary>
public static class Spx
{
    public const string Url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=1d&interval=15m";

    /// <summary>The skin's schedule: every 5 minutes while the market is open, hourly while it is closed.</summary>
    public static int NextSeconds(bool open) => open ? 300 : 3600;

    /// <summary>spx.update from the untrusted reply, or null when it has no usable price and previous close.</summary>
    public static (string Json, bool Open)? Parse(string? body, long nowS)
    {
        if (string.IsNullOrEmpty(body)) return null;
        try
        {
            using var d = JsonDocument.Parse(body);
            var meta = d.RootElement.GetProperty("chart").GetProperty("result")[0].GetProperty("meta");
            var price = Num(meta, "regularMarketPrice");
            var prev = Num(meta, "chartPreviousClose") ?? Num(meta, "previousClose");
            if (price is not > 0 || prev is not > 0) return null;
            var open = false;
            if (meta.TryGetProperty("currentTradingPeriod", out var tp) && tp.ValueKind == JsonValueKind.Object
                && tp.TryGetProperty("regular", out var reg) && reg.ValueKind == JsonValueKind.Object
                && Num(reg, "start") is { } s && Num(reg, "end") is { } e)
                open = nowS >= s && nowS <= e;
            return (JsonSerializer.Serialize(new { type = "spx.update", price, prev, open }), open);
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException or IndexOutOfRangeException) { return null; }
    }

    static double? Num(JsonElement o, string name) =>
        o.TryGetProperty(name, out var v) && v.ValueKind == JsonValueKind.Number && v.TryGetDouble(out var n) && double.IsFinite(n) && n < 1e9 ? n : null;
}
