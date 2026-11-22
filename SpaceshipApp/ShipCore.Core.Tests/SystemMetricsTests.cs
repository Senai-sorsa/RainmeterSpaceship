namespace ShipCore.Core.Tests;

public sealed class SystemMetricsTests
{
    [Fact]
    public void CpuPercentIsBusyTimeOverElapsedTime()
    {
        // kernel includes idle: over the interval, 200 total (100 kernel + 100 user), 50 idle, so 150 busy
        var prev = new CpuTimes(Idle: 100, Kernel: 200, User: 100);
        var cur = new CpuTimes(Idle: 150, Kernel: 300, User: 200);
        Assert.Equal(75.0, SystemMetrics.CpuPercent(prev, cur));
    }

    [Fact]
    public void CpuPercentIsNullWhenNothingElapsedOrACounterWentBack()
    {
        var t = new CpuTimes(10, 20, 30);
        Assert.Null(SystemMetrics.CpuPercent(t, t));
        Assert.Null(SystemMetrics.CpuPercent(t, new CpuTimes(9, 20, 30)));
    }

    [Theory]
    [InlineData(100UL, 25UL, 75.0)]
    [InlineData(100UL, 150UL, 0.0)]
    [InlineData(0UL, 0UL, 0.0)]
    public void MemoryPercentIsUsedShare(ulong total, ulong available, double expected)
    {
        Assert.Equal(expected, SystemMetrics.MemoryPercent(total, available));
    }

    [Fact]
    public void PowerReadsUnknownAsNull()
    {
        Assert.Equal(new PowerSummary(false, 50), SystemMetrics.Power(0, 50));
        Assert.Equal(new PowerSummary(true, null), SystemMetrics.Power(1, 255));
        Assert.Equal(new PowerSummary(null, null), SystemMetrics.Power(255, 255));
        Assert.Equal(new PowerSummary(true, 100), SystemMetrics.Power(1, 120));
    }
}
