namespace ShipCore.Core.Tests;

public class AudioSpectrumTests
{
    const int Rate = 48000, N = 1024;
    static List<float> Tone(double hz, double amp) => Enumerable.Range(0, N).Select(i => (float)(amp * Math.Sin(2 * Math.PI * hz * i / Rate))).ToList();

    [Fact]
    public void AQuieterToneReadsLowerOnTheDecibelScale()
    {
        // 0 dB fills the band, -40 dB sits mid-scale (dB mapped from -70..-6), so quiet music still moves the ring
        var loud = SpectrumBands.Compute(Tone(1000, 1.0), Rate, 24)!.Max();
        var quiet = SpectrumBands.Compute(Tone(1000, 0.01), Rate, 24)!.Max();
        Assert.Equal(1, loud, 3);
        Assert.InRange(quiet, 0.35, 0.6);
    }

    [Fact]
    public void TheHannWindowKeepsAToneOutOfFarBands()
    {
        var bands = SpectrumBands.Compute(Tone(1000, 0.5), Rate, 24)!;
        var top = Array.IndexOf(bands, bands.Max());
        Assert.All(bands.Where((_, i) => Math.Abs(i - top) > 2), v => Assert.True(v < 0.35, $"far band {v}"));
    }

    [Fact]
    public void EveryBandHasABinEvenBelowOneBinWidth()
    {
        // 24 bands from 40 Hz: the lowest are narrower than a 47 Hz bin; a bass tone must still light one of them
        var bands = SpectrumBands.Compute(Tone(60, 0.5), Rate, 24)!;
        Assert.True(bands.Take(4).Max() > 0.8);
    }

    [Fact]
    public void TheFeedSendsSoundThenOneQuietFrameThenNothing()
    {
        var feed = new AudioSpectrumFeed();
        Assert.Null(feed.Next(null));
        Assert.Null(feed.Next([0, 0, 0]));                 // silent from the start: nothing to settle
        Assert.NotNull(feed.Next([0.5, 0.2, 0]));          // sound
        Assert.NotNull(feed.Next([0.4, 0.1, 0]));
        Assert.Equal("{\"type\":\"audio.spectrum\",\"bands\":[0,0.01,0]}", feed.Next([0, 0.01, 0])); // one quiet frame
        Assert.Null(feed.Next([0, 0, 0]));                 // then nothing until sound returns
        Assert.Null(feed.Next(new double[65]));            // over the page's limit
    }

    [Fact]
    public void TheJsonClampsAndRoundsEachBand()
    {
        Assert.Equal("{\"type\":\"audio.spectrum\",\"bands\":[1,0,0.123,0]}", AudioSpectrumFeed.Json([1.7, -2, 0.12345, double.NaN]));
    }
}
