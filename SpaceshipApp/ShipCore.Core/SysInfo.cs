using System.Text.Json;

namespace ShipCore.Core;

/// <summary>The names the bottom panels show (panels.lua: mUser, mHost, Hardware.inc's OsName, CpuName, DGpuName, the screen size and refresh). Sent once per page.</summary>
public static class SysInfo
{
    /// <param name="hardwareInc">The text of @Resources\Hardware.inc, or empty when it is missing.</param>
    /// <param name="display">The primary screen as "WIDTHxHEIGHT @HZ", or null.</param>
    public static string ToJson(string user, string host, string hardwareInc, string? display, string? version = null)
    {
        var hw = ConfigStore.Parse(hardwareInc);
        string? Get(string k) => hw.TryGetValue(k, out var v) && v.Trim() is { Length: > 0 and <= 80 } t ? t : null;
        return JsonSerializer.Serialize(new { type = "sys.info", user, host, os = Get("OsName"), cpu = Get("CpuName"), gpu = Get("DGpuName"), display, version });
    }
}
