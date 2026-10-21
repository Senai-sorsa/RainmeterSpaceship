namespace ShipCore.Core.Tests;

public sealed class HwinfoSensorsTests
{
    private sealed class FakeRegistry(Dictionary<int, string> values) : IHwinfoRegistry
    {
        public List<int> Asked { get; } = new();
        public string? ReadValueRaw(int index) { Asked.Add(index); return values.GetValueOrDefault(index); }
    }

    [Fact]
    public void AnUnmappedSensorIsNotReadAtAll()
    {
        var reg = new FakeRegistry(new() { [5] = "47" });
        var s = new HwinfoSensors(reg, new Dictionary<string, int> { ["HW_CpuTemp"] = -1 });
        Assert.Null(s.Read("HW_CpuTemp"));
        Assert.Empty(reg.Asked);
    }

    [Fact]
    public void AMappedSensorReadsItsIndex()
    {
        var s = new HwinfoSensors(new FakeRegistry(new() { [5] = "47.5 C" }), new Dictionary<string, int> { ["HW_CpuTemp"] = 5 });
        Assert.Equal(47.5, s.Read("HW_CpuTemp"));
    }

    [Fact]
    public void HwinfoNotRunningGivesNoValue()
    {
        var s = new HwinfoSensors(new FakeRegistry(new()), new Dictionary<string, int> { ["HW_CpuTemp"] = 5 });
        Assert.Null(s.Read("HW_CpuTemp"));
    }

    [Theory]
    [InlineData("-3 W", -3.0)]
    [InlineData("0.25", 0.25)]
    [InlineData("n/a", null)]
    [InlineData("", null)]
    [InlineData(null, null)]
    public void ParseNumberTakesTheFirstNumber(string? raw, double? expected)
    {
        Assert.Equal(expected, HwinfoSensors.ParseNumber(raw));
    }

    [Fact]
    public void MapFromKeepsOnlyWholeIndexesOfHwKeys()
    {
        var map = HwinfoSensors.MapFrom(new Dictionary<string, string>
        {
            ["HW_CpuTemp"] = "5", ["HW_GpuTemp"] = "-1", ["HW_Fan1"] = "x", ["LinkDownMbps"] = "176",
        });
        Assert.Equal(new Dictionary<string, int> { ["HW_CpuTemp"] = 5, ["HW_GpuTemp"] = -1 }, map);
    }
}
