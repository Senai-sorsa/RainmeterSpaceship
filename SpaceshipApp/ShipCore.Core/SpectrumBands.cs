using System.Numerics;

namespace ShipCore.Core;

/// <summary>Splits a block of audio samples into log-spaced bands of magnitude. Pure arithmetic: the WASAPI capture only supplies the samples.</summary>
public static class SpectrumBands
{
    /// <returns>One magnitude per band, 0 to 1, low frequencies first. Null when the block length is not a power of two of at least 2, or the band count is not positive.</returns>
    public static double[]? Compute(IReadOnlyList<float> samples, int sampleRate, int bands, double minHz = 40, double maxHz = 16000)
    {
        var n = samples.Count;
        if (n < 2 || (n & (n - 1)) != 0 || bands <= 0 || sampleRate <= 0) return null;
        var bins = Fft(samples, n);
        var result = new double[bands];
        var nyquist = Math.Min(maxHz, sampleRate / 2.0);
        for (var b = 0; b < bands; b++)
        {
            // Log-spaced edges from minHz to nyquist; each band takes the largest FFT bin inside it.
            var lo = minHz * Math.Pow(nyquist / minHz, (double)b / bands);
            var hi = minHz * Math.Pow(nyquist / minHz, (double)(b + 1) / bands);
            var from = Math.Max(1, (int)Math.Ceiling(lo * n / sampleRate));
            var to = Math.Min(n / 2 - 1, (int)Math.Floor(hi * n / sampleRate));
            var peak = 0.0;
            for (var k = from; k <= to; k++) peak = Math.Max(peak, bins[k].Magnitude);
            // Scale so a full-scale sine reads about 1.
            result[b] = Math.Clamp(peak * 2.0 / n, 0, 1);
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
