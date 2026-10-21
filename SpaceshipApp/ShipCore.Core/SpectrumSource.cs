namespace ShipCore.Core;

/// <summary>The newest audio spectrum (bands, 0 to 1), or null when there is none. The WASAPI capture implements it; tests use a fake.</summary>
public interface ISpectrumSource { double[]? Latest { get; } }

/// <summary>Whether a process with this executable name (no .exe) is running. The Windows host uses Process; tests use a fake.</summary>
public interface IProcessNames { bool IsRunning(string name); }
