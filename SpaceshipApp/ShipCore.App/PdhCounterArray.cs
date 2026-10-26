using System.Runtime.InteropServices;
using ShipCore.Core;

// One wildcard PDH counter read as an instance list: the GPU engines (IGpuCounters, Task Manager's GPU column) and the
// per-process CPU and memory for the targeter. Read-only: it opens a query and nothing else.
sealed class PdhCounterArray : IGpuCounters, IDisposable
{
    public const string Gpu = @"\GPU Engine(*)\Utilization Percentage";
    const uint PDH_FMT_DOUBLE = 0x200, PDH_FMT_NOCAP100 = 0x8000;
    const int PDH_MORE_DATA = unchecked((int)0x800007D2);
    // PDH_FMT_COUNTERVALUE_ITEM_W: a name pointer, then { CStatus, pad, double }; 8-byte aligned on x86 and x64
    const int ItemSize = 24, StatusOffset = 8, ValueOffset = 16;

    [DllImport("pdh.dll", CharSet = CharSet.Unicode)] static extern int PdhOpenQueryW(string? source, IntPtr user, out IntPtr query);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode)] static extern int PdhAddEnglishCounterW(IntPtr query, string path, IntPtr user, out IntPtr counter);
    [DllImport("pdh.dll")] static extern int PdhCollectQueryData(IntPtr query);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode)] static extern int PdhGetFormattedCounterArrayW(IntPtr counter, uint format, ref uint bytes, out uint count, IntPtr buffer);
    [DllImport("pdh.dll")] static extern int PdhCloseQuery(IntPtr query);

    IntPtr _query, _counter, _buf;
    uint _bufBytes;
    readonly uint _format;

    /// <param name="noCap">a process's % Processor Time counts every core, so it must not be capped at 100</param>
    public PdhCounterArray(string path, bool noCap = false)
    {
        _format = PDH_FMT_DOUBLE | (noCap ? PDH_FMT_NOCAP100 : 0);
        if (PdhOpenQueryW(null, IntPtr.Zero, out _query) != 0) { _query = IntPtr.Zero; return; }
        if (PdhAddEnglishCounterW(_query, path, IntPtr.Zero, out _counter) != 0) Dispose();
    }

    /// <returns>Empty when the counter is missing, on the first read (a rate needs two samples) and on any PDH error.</returns>
    public IReadOnlyList<(string Instance, double Percent)> Read()
    {
        if (_query == IntPtr.Zero || PdhCollectQueryData(_query) != 0) return [];
        uint bytes = _bufBytes, count;
        var rc = PdhGetFormattedCounterArrayW(_counter, _format, ref bytes, out count, _buf);
        if (rc == PDH_MORE_DATA)
        {
            // the buffer is kept and only grows, so a steady instance count allocates nothing here
            if (_buf != IntPtr.Zero) Marshal.FreeHGlobal(_buf);
            _buf = Marshal.AllocHGlobal((int)bytes); _bufBytes = bytes;
            rc = PdhGetFormattedCounterArrayW(_counter, _format, ref bytes, out count, _buf);
        }
        if (rc != 0) return [];
        var list = new List<(string, double)>((int)count);
        for (var i = 0; i < count; i++)
        {
            var item = _buf + i * ItemSize;
            var status = (uint)Marshal.ReadInt32(item, StatusOffset);
            if (status > 1) continue; // PDH_CSTATUS_VALID_DATA 0 or NEW_DATA 1; the rest is the "sample is not valid" case
            var name = Marshal.PtrToStringUni(Marshal.ReadIntPtr(item));
            if (name is not null) list.Add((name, BitConverter.Int64BitsToDouble(Marshal.ReadInt64(item, ValueOffset))));
        }
        return list;
    }

    public void Dispose()
    {
        if (_query != IntPtr.Zero) { PdhCloseQuery(_query); _query = IntPtr.Zero; }
        if (_buf != IntPtr.Zero) { Marshal.FreeHGlobal(_buf); _buf = IntPtr.Zero; _bufBytes = 0; }
    }
}
