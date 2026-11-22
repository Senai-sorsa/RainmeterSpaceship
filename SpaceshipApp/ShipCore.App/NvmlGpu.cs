using System.Runtime.InteropServices;
using ShipCore.Core;

// NVIDIA's own driver library (nvml.dll, installed in System32 with the driver; the same source nvidia-smi uses). Read-only: init, ask the
// first card for load, temperature, graphics clock and power, nothing else. No NVIDIA card or driver: Read() stays null and nothing is logged.
sealed class NvmlGpu : IGpuTelemetry
{
    [StructLayout(LayoutKind.Sequential)] struct Utilization { public uint Gpu, Memory; }
    const string Lib = "nvml.dll";
    [DllImport(Lib, EntryPoint = "nvmlInit_v2"), DefaultDllImportSearchPaths(DllImportSearchPath.System32)] static extern int Init();
    [DllImport(Lib, EntryPoint = "nvmlDeviceGetHandleByIndex_v2"), DefaultDllImportSearchPaths(DllImportSearchPath.System32)] static extern int GetHandle(uint index, out IntPtr device);
    [DllImport(Lib, EntryPoint = "nvmlDeviceGetUtilizationRates"), DefaultDllImportSearchPaths(DllImportSearchPath.System32)] static extern int GetUtilization(IntPtr device, out Utilization u);
    [DllImport(Lib, EntryPoint = "nvmlDeviceGetTemperature"), DefaultDllImportSearchPaths(DllImportSearchPath.System32)] static extern int GetTemperature(IntPtr device, int sensor, out uint celsius);
    [DllImport(Lib, EntryPoint = "nvmlDeviceGetClockInfo"), DefaultDllImportSearchPaths(DllImportSearchPath.System32)] static extern int GetClock(IntPtr device, int clock, out uint mhz);
    [DllImport(Lib, EntryPoint = "nvmlDeviceGetPowerUsage"), DefaultDllImportSearchPaths(DllImportSearchPath.System32)] static extern int GetPower(IntPtr device, out uint milliwatts);

    bool _tried, _ok;
    IntPtr _device;

    public GpuReading? Read()
    {
        try
        {
            if (!_tried) { _tried = true; _ok = Init() == 0 && GetHandle(0, out _device) == 0; }
            if (!_ok) return null;
            double? load = GetUtilization(_device, out var u) == 0 ? u.Gpu : null;
            double? temp = GetTemperature(_device, 0, out var t) == 0 ? t : null;       // 0 = the GPU die
            double? clock = GetClock(_device, 0, out var c) == 0 ? c : null;            // 0 = graphics clock
            double? power = GetPower(_device, out var mw) == 0 ? mw / 1000.0 : null;
            return new GpuReading(load, temp, clock, power);
        }
        catch (Exception e) when (e is DllNotFoundException or EntryPointNotFoundException or BadImageFormatException or SEHException)
        {
            _ok = false;                                                                  // no driver library: never asked again
            return null;
        }
    }
}
