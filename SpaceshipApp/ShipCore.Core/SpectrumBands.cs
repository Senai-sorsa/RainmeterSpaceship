using System.Numerics;

namespace ShipCore.Core;

/// <summary>Splits a block of audio samples into log-spaced bands, as music visualizers do: a Hann window against leakage,
/// the energy of each log-spaced band, and decibels mapped to 0..1 so quiet passages still move and loud ones do not
/// pin. Pure arithmetic: the WASAPI capture only supplies the samples.</summary>
public static class SpectrumBands
{
    /// <summary>The decibel window mapped to 0..1 (a full-scale sine is 0 dB).</summary>
    public const double FloorDb = -70, CeilingDb = -6;

    /// <returns>One level per band, 0 to 1, low frequencies first. Null when the block length is not a power of two of at least 2, or the band count is not positive.</returns>
    public static double[]? Compute(IReadOnlyList<float> samples, int sampleRate, int bands, double minHz = 40, double maxHz = 16000)
    {
        var n = samples.Count;
        if (n < 2 || (n & (n - 1)) != 0 || bands <= 0 || sampleRate <= 0) return null;
        var windowed = new float[n];
        for (var i = 0; i < n; i++) windowed[i] = (float)(samples[i] * (0.5 - 0.5 * Math.Cos(2 * Math.PI * i / (n - 1))));
        var bins = Fft(windowed, n);
        var result = new double[bands];
        var nyquist = Math.Min(maxHz, sampleRate / 2.0);
        for (var b = 0; b < bands; b++)
        {
            // log-spaced edges from minHz to nyquist; a band narrower than one bin uses the bin nearest its centre
            var lo = minHz * Math.Pow(nyquist / minHz, (double)b / bands);
            var hi = minHz * Math.Pow(nyquist / minHz, (double)(b + 1) / bands);
            var from = Math.Max(1, (int)Math.Ceiling(lo * n / sampleRate));
            var to = Math.Min(n / 2 - 1, (int)Math.Floor(hi * n / sampleRate));
            if (from > to) from = to = Math.Clamp((int)Math.Round(Math.Sqrt(lo * hi) * n / sampleRate), 1, n / 2 - 1);
            var power = 0.0;
            for (var k = from; k <= to; k++) power += bins[k].Magnitude * bins[k].Magnitude;
            // Parseval with the Hann window (sum of w^2 = 3n/8): a full-scale sine's energy over its bins reads amplitude 1
            var amp = Math.Sqrt(power * 32.0 / 3.0) / n;
            var db = amp > 0 ? 20 * Math.Log10(amp) : double.NegativeInfinity;
            result[b] = Math.Clamp((db - FloorDb) / (CeilingDb - FloorDb), 0, 1);
        }
        return result;
    }

    /// <summary>Iterative radix-2 FFT; the input is copied, not changed.</summary>
    private static Complex[] Fft(IReadOnlyList<float> input, int n)
    {
        var a = new Complex[n];
        var bits = Convert.ToInt32(Math.Log2(n));
        for (var i = 0; i < n; i++)
        {
            var j = 0;
            for (var k = 0; k < bits; k++) j |= ((i >> k) & 1) << (bits - 1 - k);
            a[j] = input[i];
        }
        for (var len = 2; len <= n; len <<= 1)
        {
            var angle = -2 * Math.PI / len;
            var wl = new Complex(Math.Cos(angle), Math.Sin(angle));
            for (var i = 0; i < n; i += len)
            {
                var w = Complex.One;
                for (var j = 0; j < len / 2; j++)
                {
                    var u = a[i + j];
                    var v = a[i + j + len / 2] * w;
                    a[i + j] = u + v;
                    a[i + j + len / 2] = u - v;
                    w *= wl;
                }
            }
        }
        return a;
    }
}
