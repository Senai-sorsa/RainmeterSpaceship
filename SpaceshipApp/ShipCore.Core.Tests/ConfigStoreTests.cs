using System.Text;

namespace ShipCore.Core.Tests;

public sealed class ConfigStoreTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "shipcore-" + Guid.NewGuid().ToString("N"));
    private readonly ConfigStore _store;

    public ConfigStoreTests()
    {
        Directory.CreateDirectory(_dir);
        File.WriteAllText(Path.Combine(_dir, "Settings.inc"), "; keep me\r\n[Variables]\r\nScale=0.67\r\nColorAccent=0,210,255\r\n\r\n[Other]\r\nX=1\r\n");
        File.WriteAllText(Path.Combine(_dir, "State.inc"), "[Variables]\nOff_TopPower=0\n");
        _store = new ConfigStore(_dir, Repo.Schema());
    }
    public void Dispose() => Directory.Delete(_dir, true);
    private string Read(string f) => File.ReadAllText(Path.Combine(_dir, f));

    [Fact]
    public void SetReplacesOnlyThatLineAndKeepsLineEndingsAndComments()
    {
        Assert.True(_store.Set("Scale", "0.8").Ok);
        Assert.Equal("; keep me\r\n[Variables]\r\nScale=0.8\r\nColorAccent=0,210,255\r\n\r\n[Other]\r\nX=1\r\n", Read("Settings.inc"));
    }

    [Fact]
    public void AnIndentedOrDifferentlyCasedKeyIsReplacedNotDuplicated()
    {
        File.WriteAllText(Path.Combine(_dir, "Settings.inc"), "[Variables]\r\n   JarvisName=Old\r\nscale=1\n");
        Assert.True(_store.Set("JarvisName", "Friday").Ok);
        Assert.True(_store.Set("Scale", "0.8").Ok);
        Assert.Equal("[Variables]\r\n   JarvisName=Friday\r\nScale=0.8\n", Read("Settings.inc"));
        Assert.Equal("Friday", _store.Get(new[] { "JarvisName" })["JarvisName"]);
    }

    [Fact]
    public void MixedLineEndingsStayAsTheyWereAndNothingIsMerged()
    {
        File.WriteAllText(Path.Combine(_dir, "Settings.inc"), "[Variables]\r\nScale=1\nColorAccent=0,210,255\r\n");
        Assert.True(_store.Set("JarvisName", "Friday").Ok);
        Assert.Equal("[Variables]\r\nScale=1\nColorAccent=0,210,255\r\nJarvisName=Friday\r\n", Read("Settings.inc"));
    }

    [Fact]
    public void AnAbsentKeyIsAddedAtTheEndOfVariablesNotAfterOtherSections()
    {
        Assert.True(_store.Set("JarvisName", "Friday").Ok);
        Assert.Equal("; keep me\r\n[Variables]\r\nScale=0.67\r\nColorAccent=0,210,255\r\nJarvisName=Friday\r\n\r\n[Other]\r\nX=1\r\n", Read("Settings.inc"));
    }

    [Fact]
    public void RefusedWritesLeaveTheFileUntouched()
    {
        var before = Read("Settings.inc");
        foreach (var (k, v) in new[] { ("Scale", "9"), ("Scale", "1\nEvil=1"), ("NoSuchKey", "1"), ("Other", "1"), ("Scale=1\nX", "1") })
            Assert.False(_store.Set(k, v).Ok);
        Assert.Equal(before, Read("Settings.inc"));
        Assert.Empty(Directory.GetFiles(_dir, "*.tmp*"));
    }

    [Fact]
    public void KeysGoToTheFileTheSchemaNamesAndGetReadsThemBack()
    {
        Assert.True(_store.Set("Off_TopPower", "1").Ok);
        Assert.Equal("[Variables]\nOff_TopPower=1\n", Read("State.inc"));
        var got = _store.Get(new[] { "Off_TopPower", "Scale", "JarvisName", "bogus" });
        Assert.Equal(new Dictionary<string, string> { ["Off_TopPower"] = "1", ["Scale"] = "0.67" }, got);
    }

    [Fact]
    public void AByteOrderMarkSurvivesAWrite()
    {
        File.WriteAllBytes(Path.Combine(_dir, "State.inc"), new byte[] { 0xEF, 0xBB, 0xBF }.Concat(Encoding.UTF8.GetBytes("[Variables]\nOff_TopPower=0\n")).ToArray());
        Assert.True(_store.Set("Off_TopPower", "1").Ok);
        Assert.Equal(new byte[] { 0xEF, 0xBB, 0xBF }, File.ReadAllBytes(Path.Combine(_dir, "State.inc")).Take(3).ToArray());
        Assert.Equal("1", _store.Get(new[] { "Off_TopPower" })["Off_TopPower"]);
    }

    [Fact]
    public void AMissingFileIsCreatedWithTheKey()
    {
        Directory.CreateDirectory(_dir);
        Assert.True(_store.Set("TopPower_DX", "5").Ok);
        Assert.Equal("TopPower_DX=5", Read("Offsets.inc"));
    }

    [Fact]
    public void ConcurrentWritesToDifferentKeysAreAllKept()
    {
        Parallel.For(0, 20, i => Assert.True(_store.Set(i % 2 == 0 ? "Scale" : "GlowWidth", i % 2 == 0 ? "0.8" : "3.0").Ok));
        var t = Read("Settings.inc");
        Assert.Contains("Scale=0.8", t);
        Assert.Contains("GlowWidth=3.0", t);
        Assert.Equal(1, t.Split("GlowWidth=").Length - 1);
    }
}
