using System.Text.Json;

namespace ShipCore.Core.Tests;

public class TopProcsTests
{
    [Fact]
    public void RollsUpByNameDropsTheBlacklistAndDividesByThreads()
    {
        var top = TopProcs.Top(
            [("chrome", 40), ("chrome#1", 40), ("_Total", 800), ("Idle", 700), ("code", 60), ("x", double.NaN)],
            [("chrome", 100), ("chrome#1", 50), ("code", 7)], threads: 8, n: 2);
        Assert.Equal([("chrome", 10.0, 150.0), ("code", 7.5, 7.0)], top);
        var j = JsonDocument.Parse(TopProcs.ToJson(top)).RootElement;
        Assert.Equal("procs.top", j.GetProperty("type").GetString());
        Assert.Equal("chrome", j.GetProperty("top")[0].GetProperty("name").GetString());
    }
}
