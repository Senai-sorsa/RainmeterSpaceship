namespace ShipCore.Core.Tests;

public class SpeedTestTests
{
    [Fact]
    public void ParsesOoklaJsonToMbps()
    {
        var r = SpeedTest.Parse("{\"type\":\"result\",\"ping\":{\"latency\":9.7},\"download\":{\"bandwidth\":22050000,\"bytes\":1},\"upload\":{\"bandwidth\":52925000}}");
        Assert.Equal((176.4, 423.4), r);
    }

    [Theory]
    [InlineData("")]
    [InlineData("not json")]
    [InlineData("{\"download\":{\"bandwidth\":1}}")]
    [InlineData("{\"download\":{\"bandwidth\":\"x\"},\"upload\":{\"bandwidth\":1}}")]
    [InlineData("[1]")]
    public void NoResultIsNull(string json) => Assert.Null(SpeedTest.Parse(json));

    [Fact]
    public void MessageIsAStatusUpdate() =>
        Assert.Equal("{\"type\":\"status.update\",\"kind\":\"speed\",\"state\":\"error\",\"why\":\"timed out\"}", SpeedTest.Message("error", "timed out"));
}
