using System.Text.Json;

namespace ShipCore.Core.Tests;

public class ProtocolTests
{
    [Fact]
    public void EveryFixtureGetsTheVerdictItDeclares()
    {
        var schema = Repo.Schema();
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(Repo.Root, "contract", "fixtures", "ui-to-host.json")));
        var wrong = new List<string>();
        foreach (var f in doc.RootElement.EnumerateArray())
        {
            var ok = Protocol.Problem(f.GetProperty("msg"), schema) is null;
            if (ok != f.GetProperty("valid").GetBoolean()) wrong.Add(f.GetProperty("name").GetString()!);
        }
        Assert.Empty(wrong);
        Assert.True(doc.RootElement.GetArrayLength() > 20);
    }

    [Theory]
    [InlineData("{")]
    [InlineData("")]
    [InlineData("nope")]
    public void BrokenJsonIsRefusedNotThrown(string json) => Assert.Equal("not json", Protocol.Problem(json, Repo.Schema()));

    [Fact]
    public void ActionsAreExactlyTheRegistrysAndNeverPowerOrShell()
    {
        var a = Repo.Schema().Actions;
        Assert.Contains("edit.toggle", a);
        Assert.DoesNotContain("shutdown", a);
        Assert.DoesNotContain("shell.open", a);
        Assert.DoesNotContain("sys.powerAction", a);
    }
}
