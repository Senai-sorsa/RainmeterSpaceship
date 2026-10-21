namespace ShipCore.Core;

/// <summary>Where the UI's settings are read and written. The router depends on this only.</summary>
public interface IConfigStore
{
    Dictionary<string, string> Get(IEnumerable<string> keys);
    SetResult Set(string key, string value);
}
