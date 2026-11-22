using System.ComponentModel;

namespace ShipCore.Core;

/// <summary>The running-process name list for VisibilityPolicy. A process can exit or deny access between the snapshot
/// and the name read; that one entry is skipped instead of failing the whole list.</summary>
public static class ProcessNames
{
    public static List<string> Collect(IEnumerable<Func<string>> names)
    {
        var list = new List<string>();
        foreach (var name in names)
        {
            try { list.Add(name()); }
            catch (Exception e) when (e is InvalidOperationException or Win32Exception) { }
        }
        return list;
    }
}
