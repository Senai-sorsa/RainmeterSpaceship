namespace ShipCore.Core.Tests;

public class NetInfoTests
{
    [Theory]
    [InlineData("203.0.113.7\n", "203.0.113.7")]
    [InlineData("999.1.1.1", null)]
    [InlineData("<html>", null)]
    [InlineData("::1", null)]
    [InlineData("1.2.3", null)]
    [InlineData(null, null)]
    public void WanReplyMustBeAnIpv4Address(string? reply, string? want) => Assert.Equal(want, NetInfo.Ipv4(reply));

    [Theory]
    [InlineData("8.8.8.8", "8.8.8.8")]
    [InlineData("router.local", "router.local")]
    [InlineData("a b", "1.1.1.1")]
    [InlineData(null, "1.1.1.1")]
    public void PingHostFallsBackToTheDefault(string? setting, string want) => Assert.Equal(want, NetInfo.PingHost(setting));

    [Fact]
    public void MessageKeepsUnknownApartFromNone() =>
        Assert.Equal("""{"type":"net.update","ping":0,"lan":"","wan":null}""", NetInfo.ToJson(0, "", null));
}
