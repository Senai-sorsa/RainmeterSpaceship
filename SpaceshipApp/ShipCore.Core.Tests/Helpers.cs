using ShipCore.Core;

namespace ShipCore.Core.Tests;

static class Repo
{
    public static string Root { get; } = Find();
    private static string Find()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !Directory.Exists(Path.Combine(d.FullName, "contract"))) d = d.Parent;
        return d?.FullName ?? throw new InvalidOperationException("repo root with contract/ not found");
    }
    public static ConfigSchema Schema() => ConfigSchema.Parse(File.ReadAllText(Path.Combine(Root, "contract", "config-keys.json")));
}

sealed class FakeClock : IClock { public DateTimeOffset Now { get; set; } = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero); }
sealed class FakePower : IPowerActions
{
    public List<string> Calls { get; } = new();
    public void Shutdown() => Calls.Add("shutdown");
    public void Restart() => Calls.Add("restart");
    public void Sleep() => Calls.Add("sleep");
    public void Lock() => Calls.Add("lock");
}
sealed class FakeShell : IShell { public List<string> Flows { get; } = new(); public void OpenFlow(string f) => Flows.Add(f); }
