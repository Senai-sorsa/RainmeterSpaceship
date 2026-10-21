using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32;
using ShipCore.Core;

// Windows implementations of the Core interfaces. Core decides; these only read the OS or write the one Run value.

// IWindowSnapshotSource: what VisibilityPolicy needs, read fresh on every call.
sealed class Win32Snapshots(Func<Rectangle> monitor) : IWindowSnapshotSource
{
    public WindowSnapshot Take()
    {
        var fg = GetForegroundWindow();
        WindowInfo? info = null;
        if (fg != IntPtr.Zero)
        {
            var sb = new StringBuilder(256);
            GetClassName(fg, sb, sb.Capacity);
            GetWindowThreadProcessId(fg, out var pid);
            // The extended frame bounds, not GetWindowRect: the invisible resize border would otherwise hide a maximised-looking window.
            var r = DwmGetWindowAttribute(fg, 9, out var rect, Marshal.SizeOf<NativeRect>()) == 0 ? rect : default;
            info = new WindowInfo(sb.ToString(), ProcessName((int)pid), new ShipCore.Core.Rect(r.Left, r.Top, r.Right, r.Bottom), pid == Environment.ProcessId);
        }
        var m = monitor();
        var notice = SHQueryUserNotificationState(out var raw) == 0 && raw >= 1 && raw <= 7 ? (NotificationState)(raw - 1) : NotificationState.NotPresent;
        var running = Process.GetProcesses().Select(p => { using (p) return p.ProcessName; }).ToList();
        return new WindowSnapshot(info, new ShipCore.Core.Rect(m.Left, m.Top, m.Right, m.Bottom), notice, running);
    }

    static string ProcessName(int pid)
    {
        try { using var p = Process.GetProcessById(pid); return p.ProcessName; }
        catch (Exception e) when (e is ArgumentException or InvalidOperationException or System.ComponentModel.Win32Exception) { return ""; }
    }

    [StructLayout(LayoutKind.Sequential)] struct NativeRect { public int Left, Top, Right, Bottom; }

    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder name, int max);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr h, int attr, out NativeRect value, int size);
    [DllImport("shell32.dll")] static extern int SHQueryUserNotificationState(out int state);
}

// Power and shell actions are not wired. Throwing (not returning) keeps a call from looking like success; the router logs it.
// shortcut: no power or flow actions until P-F needs them, then implement behind confirmation and exit-code checks.
sealed class UnwiredHost : IPowerActions, IShell
{
    static Exception NotWired(string what) => new InvalidOperationException(what + " is not wired in the standalone host yet");
    public void Shutdown() => throw NotWired("shutdown");
    public void Restart() => throw NotWired("restart");
    public void Sleep() => throw NotWired("sleep");
    public void Lock() => throw NotWired("lock");
    public void OpenFlow(string flow) => throw NotWired("flow " + flow);
}

// IRunKey: the current user's Run key and nothing else. AutoStart validates the value it writes.
sealed class RunKeyStore : IRunKey
{
    const string Path = @"Software\Microsoft\Windows\CurrentVersion\Run";

    public string? Get(string name) => Registry.CurrentUser.OpenSubKey(Path, false)?.GetValue(name) as string;

    public void Set(string name, string value)
    {
        using var key = Registry.CurrentUser.CreateSubKey(Path, true);
        key.SetValue(name, value, RegistryValueKind.String);
    }

    public void Delete(string name)
    {
        using var key = Registry.CurrentUser.OpenSubKey(Path, true);
        key?.DeleteValue(name, false);
    }
}
