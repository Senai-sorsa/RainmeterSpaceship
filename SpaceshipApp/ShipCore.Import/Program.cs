using ShipCore.Core;

// One-time copy of the skin's values into the host's settings.json. Dry run by default: it prints the plan and writes nothing.
// --write <settings.json> copies the plan into a file that does not exist yet. It never edits a file in place.
string? schemaPath = null, skin = null, target = null;
var write = false;
for (var i = 0; i < args.Length; i++)
{
    switch (args[i])
    {
        case "--schema" when i + 1 < args.Length: schemaPath = args[++i]; break;
        case "--skin" when i + 1 < args.Length: skin = args[++i]; break;
        case "--write" when i + 1 < args.Length: target = args[++i]; write = true; break;
        default: return Usage();
    }
}
if (schemaPath is null || skin is null || !File.Exists(schemaPath) || !Directory.Exists(skin)) return Usage();

var schema = ConfigSchema.Parse(File.ReadAllText(schemaPath));
var plan = SkinImport.Build(new ConfigStore(skin, schema), schema);
Console.WriteLine($"{plan.Values.Count} values to import, {plan.Skipped.Count} skipped:");
foreach (var (key, value) in plan.Values) Console.WriteLine($"  {key}={value}");
foreach (var reason in plan.Skipped) Console.WriteLine($"  skipped {reason}");

if (!write)
{
    Console.WriteLine("Dry run: nothing written. Add --write <new settings.json path> to copy.");
    return 0;
}
if (File.Exists(target!))
{
    Console.Error.WriteLine($"{target} already exists; choose a new path. Nothing written.");
    return 1;
}
var result = new SettingsStore(target!, schema).Import(plan.Values);
if (!result.Ok)
{
    Console.Error.WriteLine(result.Error);
    return 1;
}
Console.WriteLine($"Wrote {target}");
return 0;

static int Usage()
{
    Console.Error.WriteLine("usage: ShipCore.Import --schema <contract\\config-keys.json> --skin <Skins\\Spaceship\\@Resources> [--write <new settings.json>]");
    return 2;
}
