namespace ShipCore.Core;

/// <summary>The live wallpaper behind the HUD: which file the page may play, and when playing it is wasted work (Lively's pause rules).</summary>
public static class Wallpaper
{
    // What the page's <video>/<img> can show. Anything else (an .mlw, an .exe, a folder) is refused.
    public static readonly HashSet<string> Videos = new(StringComparer.OrdinalIgnoreCase) { ".mp4", ".webm", ".m4v", ".mov" };
    public static readonly HashSet<string> Images = new(StringComparer.OrdinalIgnoreCase) { ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp" };

    /// <summary>The WallpaperFile setting as a full path the page may show, or null. Quotes from Explorer's "Copy as path" are dropped.</summary>
    public static string? FilePath(string? setting)
    {
        var p = (setting ?? "").Trim().Trim('"').Trim();
        if (p.Length == 0 || !Path.IsPathFullyQualified(p) || p.StartsWith(@"\\", StringComparison.Ordinal)) return null; // local files only, no network shares
        var ext = Path.GetExtension(p);
        return Videos.Contains(ext) || Images.Contains(ext) ? Path.GetFullPath(p) : null;
    }

    /// <summary>True when the foreground window hides the desktop: fullscreen, or maximised over the work area.</summary>
    public static bool Hidden(WindowSnapshot s, Rect workArea)
    {
        var f = s.Foreground;
        if (f is null || f.IsOurs || VisibilityPolicy.Shell.Contains(f.ClassName)) return false;
        return f.Bounds.Contains(workArea, 1);
    }
}
