namespace ShipCore.Core;

/// <summary>Plain host decisions with no Windows types, so they can be tested without a desktop.</summary>
public static class HostRules
{
    /// <returns>index of the first display whose size matches the home size, or -1 when none does.</returns>
    public static int PickHomeDisplay(IReadOnlyList<(int Width, int Height)> displays, (int Width, int Height) home)
    {
        for (int i = 0; i < displays.Count; i++)
            if (displays[i] == home) return i;
        return -1;
    }

    /// <returns>paths of log files older than <paramref name="keep"/>, so the host can delete them.</returns>
    public static IReadOnlyList<string> ExpiredLogs(IEnumerable<(string Path, DateTime Written)> files, DateTime now, TimeSpan keep) =>
        files.Where(f => now - f.Written > keep).Select(f => f.Path).ToList();
}
