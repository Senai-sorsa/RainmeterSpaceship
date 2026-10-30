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

    /// <summary>
    /// The size to re-encode a w×h video to for WallpaperQuality ("screen" = still covers this screen, "1440"/"1080"/"720" = short side),
    /// or null to play the original (Original, an unknown level, or a video already that small).
    /// </summary>
    public static (int W, int H)? Scaled(int w, int h, string? quality, int screenW, int screenH)
    {
        if (w <= 0 || h <= 0) return null;
        double s = quality switch
        {
            "screen" => Math.Max((double)screenW / w, (double)screenH / h),
            "1440" or "1080" or "720" => int.Parse(quality) / (double)Math.Min(w, h),
            _ => 1,
        };
        if (s >= 0.95) return null; // a 5 % shrink isn't worth an encode
        return ((int)Math.Round(w * s / 2) * 2, (int)Math.Round(h * s / 2) * 2); // encoders want even sizes
    }

    /// <summary>
    /// A file's name in CSpace's wallpaper folder: the original as is (size null) or re-encoded to size. A new source file, edit
    /// or size gets a new name, so a stale copy is never played.
    /// </summary>
    public static string CacheName(string path, long length, DateTime written, (int W, int H)? size)
    {
        var id = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.UTF8.GetBytes($"{path.ToUpperInvariant()}|{length}|{written.Ticks}")))[..16];
        return size is { } s ? $"wall-{id}-{s.W}x{s.H}.mp4" : $"wall-{id}{Path.GetExtension(path).ToLowerInvariant()}";
    }

    /// <summary>True when the foreground window hides the desktop: fullscreen, or maximised over the work area.</summary>
    public static bool Hidden(WindowSnapshot s, Rect workArea)
    {
        var f = s.Foreground;
        if (f is null || f.IsOurs || VisibilityPolicy.Shell.Contains(f.ClassName)) return false;
        return f.Bounds.Contains(workArea, 1);
    }
}
