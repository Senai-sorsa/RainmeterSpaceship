using System.Text.Json;

namespace ShipCore.Core.Tests;

public sealed class SystemSamplerTests
{
    private sealed class FakeMetrics : ISystemMetrics
    {
        public Queue<CpuTimes> Cpu { get; } = new();
        public CpuTimes ReadCpuTimes() => Cpu.Dequeue();
        public (ulong Total, ulong Available) ReadMemory() => (100, 40);
        public (byte AcLine, byte BatteryPercent) ReadPower() => (0, 80);
        public ulong UptimeMs() => 5000;
    }

    private sealed class FakeRegistry(Dictionary<int, string> values) : IHwinfoRegistry
    {
        public string? ReadValueRaw(int index) => values.GetValueOrDefault(index);
    }

    [Fact]
    public void TheFirstFrameHasNoCpuFigureAndTheSecondDoes()
    {
        var m = new FakeMetrics();
        m.Cpu.Enqueue(new CpuTimes(100, 200, 100));
        m.Cpu.Enqueue(new CpuTimes(150, 300, 200));
        var s = new SystemSampler(m, new FakeRegistry(new()));
        Assert.Null(s.Sample(new Dictionary<string, string>(), 1).CpuPercent);
        Assert.Equal(75.0, s.Sample(new Dictionary<string, string>(), 2).CpuPercent);
    }

    [Fact]
    public void HwinfoValuesComeFromTheMappedIndexesAndNullWhenNotReported()
    {
        var m = new FakeMetrics();
        m.Cpu.Enqueue(new CpuTimes(0, 0, 0));
        var registry = new FakeRegistry(new() { [7] = "48.5 C" });
        var settings = new Dictionary<string, string> { ["HW_CpuTemp"] = "7", ["HW_GpuTemp"] = "9", ["HW_Fan1"] = "-1" };
        var f = new SystemSampler(m, registry).Sample(settings, 1);
        Assert.Equal(48.5, f.Hw["HW_CpuTemp"]);
        Assert.Null(f.Hw["HW_GpuTemp"]);
        Assert.Null(f.Hw["HW_Fan1"]);
    }

    [Fact]
    public void TheJsonHasTheFieldsTheFixtureDeclares()
    {
        var m = new FakeMetrics();
        m.Cpu.Enqueue(new CpuTimes(0, 0, 0));
        var json = SystemSampler.ToJson(new SystemSampler(m, new FakeRegistry(new())).Sample(new Dictionary<string, string>(), 3));
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;
        Assert.Equal("system.metrics", root.GetProperty("type").GetString());
        Assert.Equal(3, root.GetProperty("seq").GetInt64());
        Assert.Equal(60, root.GetProperty("memoryPercent").GetDouble());
        Assert.Equal(JsonValueKind.Null, root.GetProperty("cpuPercent").ValueKind);
        Assert.False(root.GetProperty("onAc").GetBoolean());
        Assert.Equal(80, root.GetProperty("batteryPercent").GetInt32());

        var fixture = JsonDocument.Parse(File.ReadAllText(Path.Combine(Repo.Root, "contract", "fixtures", "host-to-ui.json")));
        var declared = fixture.RootElement.EnumerateArray().First(e => e.GetProperty("name").GetString() == "full frame").GetProperty("msg");
        Assert.Equal(declared.EnumerateObject().Select(p => p.Name).OrderBy(n => n), root.EnumerateObject().Select(p => p.Name).OrderBy(n => n));
    }
}
