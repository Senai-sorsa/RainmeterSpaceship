namespace ShipCore.Core.Tests;

public class SpxTests
{
    const string Reply = """{"chart":{"result":[{"meta":{"regularMarketPrice":5800.5,"chartPreviousClose":5750,"currentTradingPeriod":{"regular":{"start":1000,"end":2000}}}}]}}""";

    [Fact]
    public void ReadsPriceAndSession()
    {
        var r = Spx.Parse(Reply, 1500)!.Value;
        Assert.Equal("""{"type":"spx.update","price":5800.5,"prev":5750,"open":true}""", r.Json);
        Assert.False(Spx.Parse(Reply, 2500)!.Value.Open);
    }

    [Fact]
    public void FallsBackToPreviousClose() =>
        Assert.NotNull(Spx.Parse("""{"chart":{"result":[{"meta":{"regularMarketPrice":1,"previousClose":2}}]}}""", 0));

    [Theory]
    [InlineData(null)]
    [InlineData("<html>")]
    [InlineData("""{"chart":{"result":[]}}""")]
    [InlineData("""{"chart":{"result":null}}""")]
    [InlineData("""{"chart":{"result":[{"meta":{"regularMarketPrice":"1","chartPreviousClose":2}}]}}""")]
    [InlineData("""{"chart":{"result":[{"meta":{"regularMarketPrice":1,"chartPreviousClose":0}}]}}""")]
    [InlineData("[1]")]
    public void RefusesAnythingElse(string? body) => Assert.Null(Spx.Parse(body, 0));

    [Fact]
    public void ScheduleFollowsTheMarket()
    {
        Assert.Equal(300, Spx.NextSeconds(true));
        Assert.Equal(3600, Spx.NextSeconds(false));
    }
}
