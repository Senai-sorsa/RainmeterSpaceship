using System.Text.Json;

namespace ShipCore.Core;

/// <summary>Where the page takes the mouse, in window pixels, from its last hit.regions message. Outside these the window lets clicks through.
/// Keyboard is true while the page shows something that types (the wizard, the Control Center). Written on the UI thread only.</summary>
public sealed class HitRegions
{
    public const int MaxRects = 64, MaxCoord = 16384;
    private (int X, int Y, int W, int H)[] _rects = Array.Empty<(int, int, int, int)>();

    public bool Keyboard { get; private set; }

    public void Set(IEnumerable<(int X, int Y, int W, int H)> rects, bool keyboard) { _rects = rects.ToArray(); Keyboard = keyboard; }

    /// <summary>Reads a message Protocol already accepted.</summary>
    public void Set(JsonElement m) => Set(
        m.GetProperty("rects").EnumerateArray().Select(r => (r[0].GetInt32(), r[1].GetInt32(), r[2].GetInt32(), r[3].GetInt32())),
        m.GetProperty("keyboard").GetBoolean());

    public bool Contains(int x, int y) => _rects.Any(r => x >= r.X && y >= r.Y && x < r.X + r.W && y < r.Y + r.H);
}
