using System.Runtime.InteropServices;
using ShipCore.Core;

// audio.lua's readout click: the Win7Audio plugin's ToggleNext. The next active output device (after the default one, in
// Windows' own order) becomes the default for every role, as the plugin and the Sound panel's "Set Default" do.
// IPolicyConfig is undocumented but unchanged since Windows 7 (SoundSwitch, AudioDeviceCmdlets use the same vtable).
static class AudioOut
{
    const int eRender = 0, eConsole = 0, DEVICE_STATE_ACTIVE = 1;

    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceEnumerator
    {
        [PreserveSig] int EnumAudioEndpoints(int dataFlow, int stateMask, out IMMDeviceCollection devices);
        [PreserveSig] int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice device);
    }

    [ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceCollection
    {
        [PreserveSig] int GetCount(out uint count);
        [PreserveSig] int Item(uint index, out IMMDevice device);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDevice
    {
        void Activate(); // vtable slots only, never called
        void OpenPropertyStore();
        [PreserveSig] int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
    }

    [ComImport, Guid("F8679F50-850A-41CF-9C72-430F290290C8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IPolicyConfig
    {
        void GetMixFormat(); void GetDeviceFormat(); void ResetDeviceFormat(); void SetDeviceFormat(); void GetProcessingPeriod(); // slots only
        void SetProcessingPeriod(); void GetShareMode(); void SetShareMode(); void GetPropertyValue(); void SetPropertyValue();
        [PreserveSig] int SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string id, int role);
    }

    /// <summary>False when there is no other device or Windows refused; nothing changes then.</summary>
    public static bool Next()
    {
        try
        {
            var en = (IMMDeviceEnumerator)WindowsDial.NewEnumerator();
            if (en.EnumAudioEndpoints(eRender, DEVICE_STATE_ACTIVE, out var all) != 0 || all.GetCount(out var n) != 0) return false;
            var ids = new List<string>();
            for (uint i = 0; i < n; i++)
                if (all.Item(i, out var d) == 0 && d.GetId(out var id) == 0) ids.Add(id);
            string? cur = en.GetDefaultAudioEndpoint(eRender, eConsole, out var def) == 0 && def.GetId(out var cid) == 0 ? cid : null;
            var next = HostRules.NextDevice(ids, cur);
            if (next is null || next == cur) return false;
            var pc = (IPolicyConfig)Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("870AF99C-171D-4F9E-AF0D-E63DF40C2BC9"))!)!;
            var ok = true;
            for (var role = 0; role < 3; role++) ok &= pc.SetDefaultEndpoint(next, role) == 0; // console, multimedia, communications
            return ok;
        }
        catch (Exception e) when (e is COMException or InvalidCastException) { return false; }
    }
}
