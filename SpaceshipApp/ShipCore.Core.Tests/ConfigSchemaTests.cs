namespace ShipCore.Core.Tests;

public class ConfigSchemaTests
{
    private readonly ConfigSchema _s = Repo.Schema();

    [Theory]
    [InlineData("Scale", "0.67", true)]
    [InlineData("Scale", "0.671", false)]   // off the 0.01 grid? 0.671 is not a multiple of 0.01
    [InlineData("Scale", "9", false)]       // above max
    [InlineData("Scale", "abc", false)]
    [InlineData("Scale", "1e3", false)]
    [InlineData("ColorAccent", "0,210,255", true)]
    [InlineData("ColorAccent", "0,210,256", false)]
    [InlineData("ColorAccent", "0,210", false)]
    [InlineData("ColorAccent", "", false)]          // the theme colour itself must not be emptied
    [InlineData("JarvisColorIdle", "", true)]       // empty = follow the theme
    [InlineData("JarvisName", "Friday", true)]
    [InlineData("JarvisName", "Fri day", false)]
    [InlineData("JarvisName", "Fri\nday", false)]
    [InlineData("frameStyle", "none", false)]  // virtual: not a real key
    [InlineData("NoSuchKey", "1", false)]
    [InlineData("UseShipImage", "1", true)]
    [InlineData("UseShipImage", "2", false)]
    public void ValueRules(string key, string value, bool ok) => Assert.Equal(ok, _s.Problem(key, value) is null);

    [Fact]
    public void NoTextRuleAcceptsALineBreakOrAnIniMetaCharacter()
    {
        foreach (var k in _s.Keys.Values.Where(k => k.Kind == "text"))
            foreach (var bad in new[] { "a\nb", "a\rb", "a\0b" })
                Assert.NotNull(_s.Problem(k.Key, bad));
    }

    [Fact]
    public void EveryDefaultIsValidForItsOwnKey()
    {
        var bad = _s.Keys.Values.Where(k => _s.Problem(k.Key, k.Default) is not null).Select(k => k.Key + "=" + k.Default).ToList();
        Assert.Empty(bad);
    }

    [Fact]
    public void FileNamesAreOnlyTheThreeIncFiles() =>
        Assert.Subset(new HashSet<string> { "Settings.inc", "State.inc", "Offsets.inc" }, _s.Keys.Values.Select(k => k.File).ToHashSet());
}
