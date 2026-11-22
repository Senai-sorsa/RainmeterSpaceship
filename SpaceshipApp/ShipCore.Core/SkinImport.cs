namespace ShipCore.Core;

/// <summary>Plans the one-time copy of the skin's values into the host's settings. It reads and checks; it writes nothing, so a dry run is just this call.</summary>
public static class SkinImport
{
    public sealed record Plan(IReadOnlyDictionary<string, string> Values, IReadOnlyList<string> Skipped);

    public static Plan Build(IConfigStore skin, ConfigSchema schema)
    {
        var values = new Dictionary<string, string>(StringComparer.Ordinal);
        var skipped = new List<string>();
        foreach (var (key, value) in skin.Get(schema.Keys.Keys).OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            var bad = schema.Problem(key, value);
            if (bad is null) values[key] = value;
            else skipped.Add($"{key}: {bad}");
        }
        return new(values, skipped);
    }
}
