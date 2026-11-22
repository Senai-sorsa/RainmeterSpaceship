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

    /// <summary>The exact size match when there is one; otherwise the display whose shape is closest to the home panel's (aspects within 2 % count as equal),
    /// then the one nearest in pixel count. So after a resolution change the HUD stays on the same panel instead of jumping to the primary. -1 when no display has a usable size.</summary>
    public static int PickHomeDisplayNearest(IReadOnlyList<(int Width, int Height)> displays, (int Width, int Height) home)
    {
        var exact = PickHomeDisplay(displays, home);
        if (exact >= 0 || home.Width <= 0 || home.Height <= 0) return exact;
        int best = -1;
        double bestAspect = 0, bestSize = 0;
        for (int i = 0; i < displays.Count; i++)
        {
            var (w, h) = displays[i];
            if (w <= 0 || h <= 0) continue;
            var aspect = Math.Abs(Math.Log((double)w / h) - Math.Log((double)home.Width / home.Height));
            var size = Math.Abs(Math.Log((double)w * h / ((double)home.Width * home.Height)));
            if (best < 0 || aspect < bestAspect - 0.02 || (Math.Abs(aspect - bestAspect) <= 0.02 && size < bestSize))
                (best, bestAspect, bestSize) = (i, aspect, size);
        }
        return best;
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
