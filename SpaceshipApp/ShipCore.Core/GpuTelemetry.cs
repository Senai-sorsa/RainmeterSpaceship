namespace ShipCore.Core;

/// <summary>What a GPU vendor's own driver reports for the card: load, temperature, graphics clock, power draw. Null where the driver gives nothing.</summary>
public readonly record struct GpuReading(double? LoadPercent, double? TempC, double? ClockMHz, double? PowerW);

/// <summary>
/// A second opinion on the GPU that does not depend on Windows' per-engine counters (which show 3D, copy and video engines but can miss
/// compute work such as CUDA) or on HWiNFO. The Windows host implements it with NVML for NVIDIA; null when there is no such card or driver.
/// </summary>
public interface IGpuTelemetry { GpuReading? Read(); }
