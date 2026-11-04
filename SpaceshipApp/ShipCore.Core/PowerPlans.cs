namespace ShipCore.Core;

/// <summary>The built-in Windows power plans the dial may switch to, by mode name. Fixed GUIDs, so a mode name never reaches the command line.</summary>
public static class PowerPlans
{
    public static readonly IReadOnlyDictionary<string, string> Guids = new Dictionary<string, string>
    {
        ["quiet"] = "a1841308-3541-4fab-bc81-f71556f20b4a",
        ["balance"] = "381b4222-f694-41f0-9685-ff5bb260df2e",
        ["performance"] = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
    };
}
