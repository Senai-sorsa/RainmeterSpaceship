using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
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

// Port of the skin helper's windows.txt (Scripts\ShipCore.cs WindowExes / ProcessExes): which exes have an app
// window, as the taskbar would show it, and which run at all (read-only); Focus raises one when an app slot is clicked.
// Names are lower-cased file names with .exe.
static class AppWindows
{
    public static HashSet<string> WithWindow()
    {
        var set = new HashSet<string>();
        var cache = new Dictionary<uint, string>();
        EnumWindows((h, _) => { if (AppWindowExe(h, cache) is { } exe) set.Add(exe); return true; }, IntPtr.Zero);
        return set;
    }

    public static HashSet<string> Running()
    {
        var set = new HashSet<string>();
        foreach (var p in Process.GetProcesses())
            using (p) try { set.Add(p.ProcessName.ToLowerInvariant() + ".exe"); } catch (InvalidOperationException) { /* exited */ }
        return set;
    }

    /// <summary>Brings the first app window of exe to the front, restoring it if minimised (the skin helper's focus). False if it has none.</summary>
    public static bool Focus(string exe)
    {
        var found = IntPtr.Zero;
        var cache = new Dictionary<uint, string>();
        EnumWindows((h, _) => { if (AppWindowExe(h, cache) == exe) { found = h; return false; } return true; }, IntPtr.Zero);
        if (found == IntPtr.Zero) return false;
        if (IsIconic(found)) ShowWindow(found, 9); // SW_RESTORE
        SetForegroundWindow(found);
        return true;
    }

    static string ExeOf(uint pid, Dictionary<uint, string> cache)
    {
        if (cache.TryGetValue(pid, out var p)) return p;
        p = "";
        var h = OpenProcess(0x1000, false, pid); // PROCESS_QUERY_LIMITED_INFORMATION
        if (h != IntPtr.Zero)
        {
            var sb = new StringBuilder(1024); var size = 1024;
            if (QueryFullProcessImageName(h, 0, sb, ref size)) p = Path.GetFileName(sb.ToString()).ToLowerInvariant();
            CloseHandle(h);
        }
        return cache[pid] = p;
    }

    static string? AppWindowExe(IntPtr h, Dictionary<uint, string> cache)
    {
        if (!IsWindowVisible(h) || GetWindow(h, 4) != IntPtr.Zero) return null; // GW_OWNER: owned popups are not app windows
        var ex = GetWindowLong(h, -20);
        var appWin = (ex & 0x00040000) != 0;
        if (((ex & 0x00000080) != 0 || (ex & 0x08000000) != 0) && !appWin) return null; // tool / no-activate windows
        if (DwmGetWindowAttribute(h, 14, out var cloaked, 4) == 0 && cloaked != 0) return null;
        if (GetWindowTextLength(h) == 0) return null;
        var cb = new StringBuilder(256); GetClassName(h, cb, 256);
        var cls = cb.ToString();
        if (cls is "Progman" or "WorkerW" or "Shell_TrayWnd" or "Shell_SecondaryTrayWnd" or "Windows.UI.Core.CoreWindow" || cls.StartsWith("RainmeterMeterWindow", StringComparison.Ordinal)) return null;
        GetWindowThreadProcessId(h, out var pid);
        var exe = ExeOf(pid, cache);
        return exe is "" or "rainmeter.exe" or "cspace.exe" or "applicationframehost.exe" ? null : exe;
    }

    delegate bool EnumProc(IntPtr h, IntPtr l);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr GetWindow(IntPtr h, uint cmd);
    [DllImport("user32.dll")] static extern int GetWindowLong(IntPtr h, int index);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowTextLength(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder name, int max);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr h, int attr, out int value, int size);
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern bool QueryFullProcessImageName(IntPtr h, int flags, StringBuilder name, ref int size);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
}
