using System.Text.Json;

namespace ShipCore.Core;

/// <summary>The skin's speed test (ShipCore.exe speedtest): Ookla's CLI with --format=json; the result is saved as LinkDownMbps / LinkUpMbps.</summary>
public static class SpeedTest
{
    /// <summary>Download and upload in Mbps from the CLI's JSON (bandwidth is bytes per second); null when either is missing.</summary>
    public static (double Down, double Up)? Parse(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            double Mbps(string k) => doc.RootElement.GetProperty(k).GetProperty("bandwidth").GetInt64() * 8 / 1e6;
            return (Mbps("download"), Mbps("upload"));
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException or FormatException) { return null; }
    }

    /// <summary>The page's status.update: state is testing, done or error; why is a short reason for an error.</summary>
    public static string Message(string state, string why = "") => JsonSerializer.Serialize(new { type = "status.update", kind = "speed", state, why });
}
