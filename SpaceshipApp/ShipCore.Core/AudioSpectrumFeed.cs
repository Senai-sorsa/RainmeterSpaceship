using System.Globalization;
using System.Text;

namespace ShipCore.Core;

/// <summary>The audio.spectrum message: the newest bands for the HUD's audio ring, sent about 20 times a second while
/// sound is playing (system.metrics carries the spectrum only once a second, too slow for a visualizer). Pure: the host
/// supplies the bands and posts the JSON.</summary>
public sealed class AudioSpectrumFeed
{
    /// <summary>A band under this level counts as quiet.</summary>
    public const double Quiet = 0.02;
    private bool _sentQuiet = true;

    /// <summary>The JSON to post now, or null when there is nothing worth sending: no spectrum, or silence that the page
    /// already has (one all-quiet frame is sent so the ring settles, then nothing until sound returns).</summary>
    public string? Next(double[]? bands)
    {
        if (bands is null || bands.Length == 0 || bands.Length > 64) return null;
        var quiet = bands.All(v => v < Quiet);
        if (quiet && _sentQuiet) return null;
        _sentQuiet = quiet;
        return Json(bands);
    }

    /// <summary>{"type":"audio.spectrum","bands":[...]} with three decimals per band, each clamped to 0..1.</summary>
    public static string Json(IReadOnlyList<double> bands)
    {
        var sb = new StringBuilder("{\"type\":\"audio.spectrum\",\"bands\":[");
        for (var i = 0; i < bands.Count; i++)
        {
            if (i > 0) sb.Append(',');
            var v = double.IsFinite(bands[i]) ? Math.Clamp(bands[i], 0, 1) : 0;
            sb.Append(v.ToString("0.###", CultureInfo.InvariantCulture));
        }
        return sb.Append("]}").ToString();
    }
}
