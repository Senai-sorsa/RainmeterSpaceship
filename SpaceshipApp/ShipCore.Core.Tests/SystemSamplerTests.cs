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

    private sealed class LabelledRegistry(Dictionary<int, string> values, Dictionary<int, string> labels) : IHwinfoRegistry
    {
        public int LabelReads { get; private set; }
        public string? ReadValueRaw(int index) => values.GetValueOrDefault(index);
        public IReadOnlyDictionary<int, string> ReadLabels() { LabelReads++; return labels; }
    }

    [Fact]
    public void LabelsFillUnmappedSensorsAndASetIndexWins()
    {
        var m = new FakeMetrics();
        for (var i = 0; i < 61; i++) m.Cpu.Enqueue(new CpuTimes(0, 0, 0));
        var reg = new LabelledRegistry(new() { [1] = "40", [2] = "55", [3] = "60" }, new() { [1] = "Tctl", [2] = "GPU Temperature" });
        var s = new SystemSampler(m, reg);
        var f = s.Sample(new Dictionary<string, string> { ["HW_CpuTemp"] = "3", ["HW_GpuTemp"] = "-1" }, 1);
        Assert.Equal(60.0, f.Hw["HW_CpuTemp"]);
        Assert.Equal(55.0, f.Hw["HW_GpuTemp"]);
        for (var i = 2; i <= 60; i++) s.Sample(new Dictionary<string, string>(), i);
        Assert.Equal(1, reg.LabelReads);
        s.Sample(new Dictionary<string, string>(), 61);
        Assert.Equal(2, reg.LabelReads);
    }

    private sealed class FakeNetwork : INetworkCounters
    {
        public Queue<NetCounters> Counters { get; } = new();
        public NetCounters Read() => Counters.Dequeue();
    }

    [Fact]
    public void NetworkRatesNeedTwoSamplesAndUseTheElapsedTime()
    {
        var m = new FakeMetrics();
        m.Cpu.Enqueue(new CpuTimes(0, 0, 0)); m.Cpu.Enqueue(new CpuTimes(0, 0, 0));
        var net = new FakeNetwork();
        net.Counters.Enqueue(new NetCounters(1000, 100)); net.Counters.Enqueue(new NetCounters(3000, 600));
        var s = new SystemSampler(m, new FakeRegistry(new()), net);
        Assert.Null(s.Sample(new Dictionary<string, string>(), 1).Net);
        Assert.Equal((1000.0, 250.0), s.Sample(new Dictionary<string, string>(), 2, 2.0).Net);
    }

    private sealed class FakeProcesses(params string[] running) : IProcessNames
    {
        public bool IsRunning(string name) => running.Contains(name, StringComparer.OrdinalIgnoreCase);
    }

    private sealed class FakeSpectrum(double[]? bands) : ISpectrumSource
    {
        public double[]? Latest => bands;
    }

    [Fact]
    public void WatchedProcessesAreTrimmedCheckedAndBadNamesDropped()
    {
        var m = new FakeMetrics();
        m.Cpu.Enqueue(new CpuTimes(0, 0, 0));
        var s = new SystemSampler(m, new FakeRegistry(new()), null, new FakeSpectrum([0.5, 0.25]), new FakeProcesses("Spotify"));
        var f = s.Sample(new Dictionary<string, string> { ["WatchProcesses"] = " Spotify.exe , bad name!, obs64 " }, 1);
        Assert.Equal(2, f.Processes!.Count);
        Assert.True(f.Processes["Spotify"]);
        Assert.False(f.Processes["obs64"]);
        Assert.Equal(new[] { 0.5, 0.25 }, f.Spectrum);
    }

    [Fact]
    public void WithoutSourcesTheFrameHasNoSpectrumAndNoProcesses()
    {
        var m = new FakeMetrics();
        m.Cpu.Enqueue(new CpuTimes(0, 0, 0));
        var f = new SystemSampler(m, new FakeRegistry(new())).Sample(new Dictionary<string, string> { ["WatchProcesses"] = "Spotify" }, 1);
        Assert.Null(f.Spectrum);
        Assert.Null(f.Processes);
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

    private sealed class FakeGpu : IGpuCounters
    {
        public int Reads { get; private set; }
        public IReadOnlyList<(string Instance, double Percent)> Read() { Reads++; return [("pid_4_luid_0x1_engtype_3D", 30), ("pid_9_luid_0x1_engtype_3D", 25), ("pid_9_luid_0x1_engtype_Copy", 70)]; }
    }

    [Fact]
    public void GpuIsTheBusiestEngineReadEveryTwoSamples()
    {
        var m = new FakeMetrics();
        for (var i = 0; i < 3; i++) m.Cpu.Enqueue(new CpuTimes(0, 0, 0));
        var gpu = new FakeGpu();
        var s = new SystemSampler(m, new FakeRegistry(new()), gpu: gpu);
        Assert.Equal(70.0, s.Sample(new Dictionary<string, string>(), 1).GpuPercent);
        Assert.Equal(70.0, s.Sample(new Dictionary<string, string>(), 2).GpuPercent);
        s.Sample(new Dictionary<string, string>(), 3);
        Assert.Equal(2, gpu.Reads);
    }

    private sealed class SlowMetrics : ISystemMetrics
    {
        public int AudioReads, DriveReads;
        public CpuTimes ReadCpuTimes() => new(0, 0, 0);
        public (ulong Total, ulong Available) ReadMemory() => (100, 40);
        public (byte AcLine, byte BatteryPercent) ReadPower() => (0, 80);
        public ulong UptimeMs() => 5000;
        public (ulong Total, ulong Free)? ReadDrive() { DriveReads++; return (1000, 250); }
        public AudioLevel? ReadAudio(bool capture) { AudioReads++; return capture ? null : new AudioLevel(35, false, "Speakers"); }
        public uint? BatteryLifeSec() => 3480;
    }

    private sealed class AcMetrics : ISystemMetrics
    {
        public CpuTimes ReadCpuTimes() => new(0, 0, 0);
        public (ulong Total, ulong Available) ReadMemory() => (100, 40);
        public (byte AcLine, byte BatteryPercent) ReadPower() => (1, 80);
        public ulong UptimeMs() => 5000;
        public uint? BatteryLifeSec() => 3480;
    }

    [Fact]
    public void BatteryTimeLeftIsSentOnBatteryOnly()
    {
        var onBatt = new SystemSampler(new SlowMetrics(), new FakeRegistry(new())).Sample(new Dictionary<string, string>(), 1);
        Assert.Equal(3480u, onBatt.BatteryLifeSec);
        using var doc = JsonDocument.Parse(SystemSampler.ToJson(onBatt));
        Assert.Equal(3480, doc.RootElement.GetProperty("batteryLife").GetInt32());
        Assert.Null(new SystemSampler(new AcMetrics(), new FakeRegistry(new())).Sample(new Dictionary<string, string>(), 1).BatteryLifeSec);
    }

    [Fact]
    public void AudioIsReadEveryTwoSamplesAndTheDriveEveryThirtyAndHeldBetween()
    {
        var m = new SlowMetrics();
        var s = new SystemSampler(m, new FakeRegistry(new()));
        SystemFrame f = null!;
        for (var seq = 1; seq <= 31; seq++) f = s.Sample(new Dictionary<string, string>(), seq);
        Assert.Equal(16 * 2, m.AudioReads); // seq 1, 3, ... 31, speaker and mic each time
        Assert.Equal(2, m.DriveReads); // seq 1 and 31
        Assert.Equal((1000UL, 250UL), f.Drive);
        Assert.Equal(new AudioLevel(35, false, "Speakers"), f.Speaker);
        Assert.Null(f.Mic);
        using var doc = JsonDocument.Parse(SystemSampler.ToJson(f));
        Assert.Equal(35, doc.RootElement.GetProperty("volume").GetInt32());
        Assert.Equal("Speakers", doc.RootElement.GetProperty("audioDevice").GetString());
        Assert.Equal(JsonValueKind.Null, doc.RootElement.GetProperty("mic").ValueKind);
    }

    [Fact]
    public void BusiestSumsProcessesPerEngineAndClamps()
    {
        Assert.Null(GpuLoad.Busiest([]));
        Assert.Equal(55.0, GpuLoad.Busiest([("pid_4_luid_0x1_engtype_3D", 30), ("pid_9_luid_0x1_engtype_3D", 25), ("pid_9_luid_0x1_engtype_Copy", 10)]));
        Assert.Equal(100.0, GpuLoad.Busiest([("pid_1_luid_0x1_engtype_3D", 80), ("pid_2_luid_0x1_engtype_3D", 60)]));
        Assert.Null(GpuLoad.Busiest([("pid_1_luid_0x1_engtype_3D", double.NaN)]));
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
        Assert.Equal(100, root.GetProperty("memoryTotal").GetInt64());
        Assert.Equal(60, root.GetProperty("memoryUsed").GetInt64());
        Assert.Equal(JsonValueKind.Null, root.GetProperty("idleMs").ValueKind); // the fake keeps the interface default

        var fixture = JsonDocument.Parse(File.ReadAllText(Path.Combine(Repo.Root, "contract", "fixtures", "host-to-ui.json")));
        var declared = fixture.RootElement.EnumerateArray().First(e => e.GetProperty("name").GetString() == "full frame").GetProperty("msg");
        Assert.Equal(declared.EnumerateObject().Select(p => p.Name).OrderBy(n => n), root.EnumerateObject().Select(p => p.Name).OrderBy(n => n));
    }

    [Fact]
    public void SysInfoTakesTheNamesFromHardwareIncAndLeavesOutBlankOnes()
    {
        var json = SysInfo.ToJson("senai", "SHIP", "[Variables]\r\nCpuName=RYZEN AI 9 465\r\n;OsName=X\r\nDGpuName=  \r\n", "2560x1600 @240");
        using var doc = JsonDocument.Parse(json);
        var r = doc.RootElement;
        Assert.Equal("sys.info", r.GetProperty("type").GetString());
        Assert.Equal("RYZEN AI 9 465", r.GetProperty("cpu").GetString());
        Assert.Equal(JsonValueKind.Null, r.GetProperty("os").ValueKind);
        Assert.Equal(JsonValueKind.Null, r.GetProperty("gpu").ValueKind);
        Assert.Equal("2560x1600 @240", r.GetProperty("display").GetString());
    }
}
