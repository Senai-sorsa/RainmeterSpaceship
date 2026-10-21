using System.Diagnostics;
using ShipCore.Core;

// Read-only: lists whether a named process exists. Never kills or changes anything.
sealed class WindowsProcessNames : IProcessNames
{
    public bool IsRunning(string name)
    {
        var found = Process.GetProcessesByName(name);
        try { return found.Length > 0; }
        finally { foreach (var p in found) p.Dispose(); }
    }
}
