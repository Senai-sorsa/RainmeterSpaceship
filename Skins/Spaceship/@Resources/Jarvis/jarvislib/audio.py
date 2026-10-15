"""audio: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import ctypes


def _com(obj, slot, *args):
    """Call method number `slot` of a COM object; a failed HRESULT raises OSError."""
    fn = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, *(type(a) for a in args))
    return fn(ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0][slot])(obj, *args)


def speakers(mute=None, volume=None):
    """The default speakers (Core Audio, IAudioEndpointVolume): set mute (True / False) and / or volume (0.0-1.0) when
    given, then return (muted, percent) as Windows reports them. A value Windows did not take raises OSError."""
    ole, P = ctypes.oledll.ole32, ctypes.c_void_p

    def guid(text):
        g = ctypes.create_string_buffer(16)
        ole.CLSIDFromString(ctypes.c_wchar_p(text), g)
        return ctypes.cast(g, P)
    ctypes.windll.ole32.CoInitialize(None)                    # once per thread; a repeat is harmless
    devices, device, vol, state, level = P(), P(), P(), ctypes.c_int(), ctypes.c_float(1)
    ole.CoCreateInstance(guid("{BCDE0395-E52F-467C-8E3D-C4579291692E}"), None, 23,
                         guid("{A95664D2-9614-4F35-A746-DE8DB63617E6}"), ctypes.byref(devices))
    try:
        _com(devices, 4, ctypes.c_int(0), ctypes.c_int(1), ctypes.pointer(device))       # GetDefaultAudioEndpoint
        _com(device, 3, guid("{5CDF2C82-841E-4546-9722-0CF74078229A}"), ctypes.c_uint(23), P(None), ctypes.pointer(vol))
        if volume is not None:
            _com(vol, 7, ctypes.c_float(volume), P(None))                                # SetMasterVolumeLevelScalar
        if mute is not None:
            _com(vol, 14, ctypes.c_int(bool(mute)), P(None))                             # SetMute
        _com(vol, 15, ctypes.pointer(state))                                             # GetMute
        _com(vol, 9, ctypes.pointer(level))                                              # GetMasterVolumeLevelScalar
    finally:
        for obj in (vol, device, devices):
            if obj:
                _com(obj, 2)                                                             # Release
    if mute is not None and bool(state.value) != bool(mute):
        raise OSError("Windows did not change the mute state")
    if volume is not None and abs(level.value - volume) > 0.01:
        raise OSError("Windows did not change the volume")
    return bool(state.value), round(level.value * 100)


def speakers_mute(on=None):
    """Set the mute state and return it. on=None only reads it, and counts a volume of 0 % as muted (nothing would
    be heard either way)."""
    is_muted, percent = speakers(mute=on)
    return is_muted or (on is None and percent <= 0)
