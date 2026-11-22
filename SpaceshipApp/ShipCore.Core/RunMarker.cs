namespace ShipCore.Core;

/// <summary>A file that exists while the app runs. Quit and the kill chord remove it. If it is still there at the next start, the last run ended without a clean exit (a crash, Task Manager, a power cut).</summary>
public sealed class RunMarker
{
    private readonly string _path;

    public RunMarker(string path) { _path = path; }

    public bool LastRunEndedUncleanly() => File.Exists(_path);

    /// <returns>false when the file could not be written; the app still runs, it just cannot warn next time.</returns>
    public bool MarkRunning(DateTimeOffset now)
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(_path)!);
            File.WriteAllText(_path, now.ToString("O") + " pid " + Environment.ProcessId);
            return true;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { return false; }
    }

    public void MarkCleanExit()
    {
        try { File.Delete(_path); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { /* next start may warn once; the run itself is fine */ }
    }
}
