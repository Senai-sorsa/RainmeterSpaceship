using System.Text;

namespace ShipCore.Core.Tests;

public sealed class SettingsStoreTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "shipcore-" + Guid.NewGuid().ToString("N"));
    private readonly ConfigSchema _schema = Repo.Schema();
    private string Path_ => Path.Combine(_dir, "settings.json");

    public SettingsStoreTests() => Directory.CreateDirectory(_dir);
    public void Dispose() => Directory.Delete(_dir, true);

    [Fact]
    public void SetThenGetRoundTripsAndWritesVersionOne()
    {
        var s = new SettingsStore(Path_, _schema);
        Assert.True(s.Set("AutoFit", "1").Ok);
        Assert.Equal("1", s.Get(new[] { "AutoFit" })["AutoFit"]);
        Assert.Contains("\"version\": 1", File.ReadAllText(Path_));
    }

    [Fact]
    public void InvalidValueAndUnknownKeyWriteNothing()
    {
        var s = new SettingsStore(Path_, _schema);
        Assert.False(s.Set("AutoFit", "7").Ok);
        Assert.False(s.Set("NotAKey", "1").Ok);
        Assert.False(File.Exists(Path_));
    }

    [Fact]
    public void UnknownKeysInTheFileSurviveAWrite()
    {
        File.WriteAllText(Path_, "{\"version\":1,\"values\":{\"FromNewerBuild\":\"x\"}}");
        var s = new SettingsStore(Path_, _schema);
        Assert.True(s.Set("AutoFit", "1").Ok);
        Assert.Contains("FromNewerBuild", File.ReadAllText(Path_));
    }

    [Fact]
    public void AnUnreadableFileIsNeverOverwritten()
    {
        File.WriteAllText(Path_, "{ not json");
        var s = new SettingsStore(Path_, _schema);
        Assert.Empty(s.Get(new[] { "AutoFit" }));
        Assert.False(s.Set("AutoFit", "1").Ok);
        Assert.Equal("{ not json", File.ReadAllText(Path_));
    }

    [Fact]
    public void ImportAddsOnlyMissingValuesAndExistingOnesWin()
    {
        var s = new SettingsStore(Path_, _schema);
        Assert.True(s.Set("AutoFit", "0").Ok);
        Assert.True(s.Import(new Dictionary<string, string> { ["AutoFit"] = "1", ["BootAnim"] = "0", ["BootSound"] = "9" }).Ok);
        var got = s.Get(new[] { "AutoFit", "BootAnim", "BootSound" });
        Assert.Equal("0", got["AutoFit"]);
        Assert.Equal("0", got["BootAnim"]);
        Assert.False(got.ContainsKey("BootSound"));
    }

    [Fact]
    public void SkinImportPlansValidValuesAndReportsTheRest()
    {
        var skin = Path.Combine(_dir, "skin");
        Directory.CreateDirectory(skin);
        File.WriteAllText(Path.Combine(skin, "Settings.inc"), "[Variables]\nAutoFit=1\nBootAnim=7\n");
        var plan = SkinImport.Build(new ConfigStore(skin, _schema), _schema);
        Assert.Equal("1", plan.Values["AutoFit"]);
        Assert.False(plan.Values.ContainsKey("BootAnim"));
        Assert.Single(plan.Skipped);
        Assert.StartsWith("BootAnim:", plan.Skipped[0]);
        Assert.False(File.Exists(Path_)); // the dry run writes nothing
    }
}
