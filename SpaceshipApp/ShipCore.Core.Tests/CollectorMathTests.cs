namespace ShipCore.Core.Tests;

public class CollectorMathTests
{
    [Fact]
    public void NetworkRateIsBytesPerSecondAndNullOnAResetOrNoTime()
    {
        var a = new NetCounters(1000, 500);
        var b = new NetCounters(3000, 1500);
        Assert.Equal((2000.0, 1000.0), NetworkRate.Rate(a, b, 1.0));
        Assert.Equal((1000.0, 500.0), NetworkRate.Rate(a, b, 2.0));
        Assert.Null(NetworkRate.Rate(b, a, 1.0));   // counter went backwards
        Assert.Null(NetworkRate.Rate(a, b, 0));     // nothing elapsed
    }

    [Fact]
    public void SpectrumFindsTheBandOfAToneAndSilenceIsZero()
    {
        const int rate = 48000, n = 1024;
        var tone = Enumerable.Range(0, n).Select(i => (float)Math.Sin(2 * Math.PI * 1000 * i / rate)).ToList();
        var bands = SpectrumBands.Compute(tone, rate, 8)!;
        Assert.Equal(8, bands.Length);
        var loudest = Array.IndexOf(bands, bands.Max());
        Assert.True(bands[loudest] > 0.5);
        Assert.True(bands.Where((_, i) => i != loudest).All(v => v < bands[loudest]));

        var silence = SpectrumBands.Compute(new float[n], rate, 8)!;
        Assert.All(silence, v => Assert.Equal(0, v));
    }

    [Theory]
    [InlineData(1000)]   // not a power of two
    [InlineData(1)]      // too short
    public void SpectrumRejectsBadBlockLengths(int n)
    {
        Assert.Null(SpectrumBands.Compute(new float[n], 48000, 8));
        Assert.Null(SpectrumBands.Compute(new float[1024], 48000, 0));
    }
}
