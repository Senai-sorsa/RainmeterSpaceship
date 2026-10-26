using System.Runtime.InteropServices;
using ShipCore.Core;

// IGpuCounters through PDH, the API Task Manager's GPU column reads. Read-only: it opens a query and nothing else.
sealed class WindowsGpuCounters : IGpuCounters, IDisposable
{
    const uint PDH_FMT_DOUBLE = 0x200;
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

    public WindowsGpuCounters()
    {
        if (PdhOpenQueryW(null, IntPtr.Zero, out _query) != 0) { _query = IntPtr.Zero; return; }
        if (PdhAddEnglishCounterW(_query, @"\GPU Engine(*)\Utilization Percentage", IntPtr.Zero, out _counter) != 0) Dispose();
    }

    /// <returns>Empty when the counter is missing, on the first read (a rate needs two samples) and on any PDH error.</returns>
    public IReadOnlyList<(string Instance, double Percent)> Read()
    {
        if (_query == IntPtr.Zero || PdhCollectQueryData(_query) != 0) return [];
        uint bytes = _bufBytes, count;
        var rc = PdhGetFormattedCounterArrayW(_counter, PDH_FMT_DOUBLE, ref bytes, out count, _buf);
        if (rc == PDH_MORE_DATA)
        {
            // the buffer is kept and only grows, so a steady instance count allocates nothing here
            if (_buf != IntPtr.Zero) Marshal.FreeHGlobal(_buf);
            _buf = Marshal.AllocHGlobal((int)bytes); _bufBytes = bytes;
            rc = PdhGetFormattedCounterArrayW(_counter, PDH_FMT_DOUBLE, ref bytes, out count, _buf);
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
