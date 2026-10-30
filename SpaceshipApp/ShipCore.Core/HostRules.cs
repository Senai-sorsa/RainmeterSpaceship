namespace ShipCore.Core;

/// <summary>Plain host decisions with no Windows types, so they can be tested without a desktop.</summary>
public static class HostRules
{
    /// <returns>index of the first display whose size matches the home size, or -1 when none does.</returns>
    /// <summary>ToggleNext: the device after <paramref name="current"/>, wrapping; the first when current is not listed; null for none.</summary>
    public static string? NextDevice(IReadOnlyList<string> ids, string? current) =>
        ids.Count == 0 ? null : ids[(ids.ToList().IndexOf(current ?? "") + 1) % ids.Count];

    public static int PickHomeDisplay(IReadOnlyList<(int Width, int Height)> displays, (int Width, int Height) home)
    {
        for (int i = 0; i < displays.Count; i++)
            if (displays[i] == home) return i;
        return -1;
    }

    /// <returns>the size in "WxH" form, or the fallback when the text is not one.</returns>
    public static (int Width, int Height) ParseSize(string text, (int Width, int Height) fallback)
    {
        var parts = text.Split('x');
        return parts.Length == 2 && int.TryParse(parts[0], out var w) && int.TryParse(parts[1], out var h) && w > 0 && h > 0
            ? (w, h) : fallback;
    }

    /// <returns>paths of log files older than <paramref name="keep"/>, so the host can delete them.</returns>
    public static IReadOnlyList<string> ExpiredLogs(IEnumerable<(string Path, DateTime Written)> files, DateTime now, TimeSpan keep) =>
        files.Where(f => now - f.Written > keep).Select(f => f.Path).ToList();
}
