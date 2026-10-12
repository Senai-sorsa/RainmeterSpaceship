// ShipCore - background helper for the Spaceship HUD.
// Built on your PC by Scripts\core.ps1 with the C# compiler that ships with Windows (.NET Framework 4, C# 5),
// started hidden by the Controller, and it stops by itself when Rainmeter closes.
//
//   ShipCore.exe watch           "<@Resources>"   background services (below)
//   ShipCore.exe setup-gmail     "<@Resources>"   small window: Gmail address + app password (stored encrypted)
//   ShipCore.exe setup-calendars "<@Resources>"   small window: calendar feed links, labels, on/off (encrypted)
//   ShipCore.exe pick-todo       "<@Resources>"   file picker for the Obsidian to-do note -> Settings.inc
//   ShipCore.exe speedtest       "<@Resources>"   runs Ookla speedtest, saves LinkDownMbps / LinkUpMbps
//   ShipCore.exe brightness <0-100>   ShipCore.exe mic <0-100>
//   ShipCore.exe focus <exe> "<target>"   bring a running app's window to the front (restoring it if
//                                         minimised); if it has no window, launch <target> instead
//
// Files written to @Resources\Data\ (the HUD's Lua scripts read them):
//   windows.txt   T <unix> | W <exe> (has an app window) | P <exe> (running)              every ~1.5 s
//   mail.txt      T <unix> | UNREAD <n> | ERR <reason> | OFF                                every 2 min
//   calendar.txt  T <unix> | C <calendars> <errors> | E <start>|<end>|<allday>|<label>|<title>   every 10 min
//   sys.txt       T <unix> | BRIGHT <0-100|-1> | MIC <0-100|-1> | MICMUTE <0|1>               every 3 s
//   speed.txt     T <unix> | STATE testing|done|error | DOWN <Mbps> | UP <Mbps> | PING <ms>
//   net.txt       T <unix> | DOWN <bytes/s> | UP <bytes/s> | IF <adapter>                   every 1 s
//                 + an automatic speed test every AutoSpeedTestHours (default 6) when the network is quiet
//                 (the adapter Windows actually routes internet traffic through - not virtual / idle ones)
// Secrets (Gmail app password, calendar links) live in %LOCALAPPDATA%\SpaceshipHUD\, encrypted for your
// Windows account (DPAPI) - not in the skin folder, presets or anything you'd share.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Management;
using System.Net;
using System.Net.Security;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

public static class ShipCore
{
    static string Res = "", Data = "", Store = "";

    // ------------------------------------------------------------------ Win32
    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr GetWindow(IntPtr h, uint cmd);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongW")] static extern int GetWindowLong(IntPtr h, int index);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowTextLength(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder sb, int max);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr FindWindow(string cls, string title);
    [DllImport("user32.dll")] static extern IntPtr SendMessageTimeout(IntPtr h, uint msg, IntPtr w, ref COPYDATASTRUCT l, uint flags, uint timeout, out IntPtr result);
    [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr h, int attr, out int value, int size);
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern bool QueryFullProcessImageName(IntPtr hProc, uint flags, StringBuilder sb, ref uint size);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern bool AttachThreadInput(uint a, uint b, bool attach);
    [DllImport("user32.dll")] static extern bool AllowSetForegroundWindow(int pid);
    [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("iphlpapi.dll")] static extern int GetBestInterface(uint destAddr, out uint index);
    [StructLayout(LayoutKind.Sequential)] struct COPYDATASTRUCT { public IntPtr dwData; public int cbData; public IntPtr lpData; }

    [STAThread]
    public static int Main(string[] args)
    {
        if (args.Length < 1) return 1;
        string cmd = args[0].ToLowerInvariant();
        try
        {
            if (cmd == "brightness" && args.Length > 1) { SetBrightness(int.Parse(args[1])); return 0; }
            if (cmd == "mic" && args.Length > 1) { MicVolume.Set(int.Parse(args[1]) / 100f); return 0; }
            if (cmd == "focus" && args.Length > 2)
            {
                Init(Path.GetDirectoryName(Path.GetDirectoryName(Application.ExecutablePath)));   // @Resources\Bin\.. (for the log)
                FocusOrLaunch(args[1], args[2]); return 0;
            }
            if (args.Length < 2) return 1;
            Init(args[1]);
            if (cmd == "watch") return Watch();
            if (cmd == "setup-gmail") { Application.EnableVisualStyles(); Application.Run(new GmailForm()); return 0; }
            if (cmd == "setup-calendars") { Application.EnableVisualStyles(); Application.Run(new CalendarForm()); return 0; }
            if (cmd == "pick-todo") { PickTodo(); return 0; }
            if (cmd == "speedtest") { SpeedTest(); return 0; }
        }
        catch (Exception e) { Log(cmd + ": " + e); }
        return 1;
    }

    public static void Init(string res)
    {
        Res = res.Trim().TrimEnd('"').TrimEnd('\\') + "\\";
        Data = Res + "Data\\";
        Store = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SpaceshipHUD") + "\\";
        try { Directory.CreateDirectory(Data); Directory.CreateDirectory(Store); } catch { }
        try { ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072; } catch { }   // TLS 1.2
    }

    public static void Log(string msg)
    {
        try { File.AppendAllText(Data + "shipcore.log", DateTime.Now.ToString("s") + "  " + msg + Environment.NewLine); }
        catch { }
    }

    static void WriteAtomic(string path, string text)
    {
        string tmp = path + ".tmp";
        File.WriteAllText(tmp, text, new UTF8Encoding(false));
        try { if (File.Exists(path)) File.Replace(tmp, path, null); else File.Move(tmp, path); }
        catch { File.Copy(tmp, path, true); File.Delete(tmp); }
    }

    public static long Unix(DateTime utc) { return (long)(utc - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalSeconds; }
    static long UnixNow() { return Unix(DateTime.UtcNow); }

    // Rainmeter bang through WM_COPYDATA (same channel Rainmeter.exe uses on the command line)
    public static bool Bang(string bang)
    {
        IntPtr rm = FindWindow("DummyRainWClass", null);
        if (rm == IntPtr.Zero) return false;
        byte[] data = Encoding.Unicode.GetBytes(bang + "\0");
        var cds = new COPYDATASTRUCT();
        cds.dwData = (IntPtr)1; cds.cbData = data.Length; cds.lpData = Marshal.AllocHGlobal(data.Length);
        try { Marshal.Copy(data, 0, cds.lpData, data.Length); IntPtr r; SendMessageTimeout(rm, 0x004A, IntPtr.Zero, ref cds, 2, 3000, out r); }
        finally { Marshal.FreeHGlobal(cds.lpData); }
        return true;
    }

    static void SaveSetting(string key, string value)
    {
        string v = value.Replace("\"", "");
        Bang("[!WriteKeyValue Variables " + key + " \"" + v + "\" \"" + Res + "Settings.inc\"][!SetVariableGroup " + key + " \"" + v + "\" Spaceship]");
    }

    // ------------------------------------------------------------------ encrypted store (DPAPI, current user)
    public static void Protect(string name, string text)
    {
        byte[] enc = ProtectedData.Protect(Encoding.UTF8.GetBytes(text), Encoding.UTF8.GetBytes("SpaceshipHUD"), DataProtectionScope.CurrentUser);
        File.WriteAllBytes(Store + name, enc);
    }

    public static string Unprotect(string name)
    {
        try
        {
            if (!File.Exists(Store + name)) return null;
            byte[] dec = ProtectedData.Unprotect(File.ReadAllBytes(Store + name), Encoding.UTF8.GetBytes("SpaceshipHUD"), DataProtectionScope.CurrentUser);
            return Encoding.UTF8.GetString(dec);
        }
        catch (Exception e) { Log("store " + name + ": " + e.Message); return null; }
    }

    // ------------------------------------------------------------------ watch loop
    static int Watch()
    {
        bool created;
        using (var mutex = new Mutex(true, "SpaceshipShipCore", out created))
        {
            if (!created) return 0;
            var mailT = new Thread(MailLoop); mailT.IsBackground = true; mailT.Start();
            var calT = new Thread(CalendarLoop); calT.IsBackground = true; calT.Start();
            var sysT = new Thread(SysLoop); sysT.IsBackground = true; sysT.Start();
            var netT = new Thread(NetLoop); netT.IsBackground = true; netT.Start();
            string last = null; long lastBeat = 0; int missing = 0;
            while (true)
            {
                if (FindWindow("DummyRainWClass", null) == IntPtr.Zero) { if (++missing > 20) break; } else missing = 0;
                try
                {
                    var sb = new StringBuilder();
                    foreach (string e in WindowExes()) sb.Append("W ").Append(e).Append('\n');
                    foreach (string e in ProcessExes()) sb.Append("P ").Append(e).Append('\n');
                    string body = sb.ToString();
                    long now = UnixNow();
                    if (body != last || now - lastBeat >= 5) { WriteAtomic(Data + "windows.txt", "T " + now + "\n" + body); last = body; lastBeat = now; }
                }
                catch (Exception e) { Log("windows: " + e.Message); }
                Thread.Sleep(1500);
            }
        }
        return 0;
    }

    static string ExeOf(uint pid, Dictionary<uint, string> cache)
    {
        string p;
        if (cache.TryGetValue(pid, out p)) return p;
        p = "";
        IntPtr h = OpenProcess(0x1000, false, pid);
        if (h != IntPtr.Zero)
        {
            var sb = new StringBuilder(1024); uint size = 1024;
            if (QueryFullProcessImageName(h, 0, sb, ref size)) p = Path.GetFileName(sb.ToString()).ToLowerInvariant();
            CloseHandle(h);
        }
        cache[pid] = p;
        return p;
    }

    // a real app window (what the taskbar would show): its exe name, or null
    static string AppWindowExe(IntPtr h, Dictionary<uint, string> cache)
    {
        if (!IsWindowVisible(h) || GetWindow(h, 4) != IntPtr.Zero) return null;
        int ex = GetWindowLong(h, -20);
        bool appWin = (ex & 0x00040000) != 0;
        if (((ex & 0x00000080) != 0 || (ex & 0x08000000) != 0) && !appWin) return null;
        int cloaked;
        if (DwmGetWindowAttribute(h, 14, out cloaked, 4) == 0 && cloaked != 0) return null;
        if (GetWindowTextLength(h) == 0) return null;
        var cb = new StringBuilder(256); GetClassName(h, cb, 256);
        string cls = cb.ToString();
        if (cls == "Progman" || cls == "WorkerW" || cls == "Shell_TrayWnd" || cls == "Shell_SecondaryTrayWnd" ||
            cls.StartsWith("RainmeterMeterWindow") || cls == "Windows.UI.Core.CoreWindow") return null;
        uint pid; GetWindowThreadProcessId(h, out pid);
        string exe = ExeOf(pid, cache);
        if (exe.Length == 0 || exe == "rainmeter.exe" || exe == "shipcore.exe" || exe == "applicationframehost.exe") return null;
        return exe;
    }

    static SortedSet<string> WindowExes()
    {
        var set = new SortedSet<string>();
        var cache = new Dictionary<uint, string>();
        EnumWindows(delegate(IntPtr h, IntPtr l)
        {
            string exe = AppWindowExe(h, cache);
            if (exe != null) set.Add(exe);
            return true;
        }, IntPtr.Zero);
        return set;
    }

    // ------------------------------------------------------------------ app launcher: focus if running
    // Clicking an app that is already open brings its window forward (most programs ignore a second launch).
    // Windows (top of the z-order first) - the most recently used window of that program wins.
    static void FocusOrLaunch(string exe, string target)
    {
        exe = exe.Trim().ToLowerInvariant();
        if (!exe.EndsWith(".exe")) exe += ".exe";
        IntPtr found = IntPtr.Zero;
        var cache = new Dictionary<uint, string>();
        EnumWindows(delegate(IntPtr h, IntPtr l)
        {
            if (AppWindowExe(h, cache) == exe) { found = h; return false; }
            return true;
        }, IntPtr.Zero);
        if (found != IntPtr.Zero && Activate(found)) return;
        if (found != IntPtr.Zero) return;               // window exists but Windows refused focus: don't open a duplicate
        Launch(target);
    }

    static bool Activate(IntPtr h)
    {
        ShowWindow(h, IsIconic(h) ? 9 : 5);             // SW_RESTORE : SW_SHOW
        // Windows only lets the foreground process hand over focus; a tap of Alt plus attaching to the current
        // foreground thread lifts that lock for this one call
        keybd_event(0x12, 0, 0, UIntPtr.Zero); keybd_event(0x12, 0, 2, UIntPtr.Zero);
        IntPtr fg = GetForegroundWindow();
        uint dummy;
        uint fgThread = fg == IntPtr.Zero ? 0 : GetWindowThreadProcessId(fg, out dummy);
        uint me = GetCurrentThreadId();
        bool attached = fgThread != 0 && fgThread != me && AttachThreadInput(me, fgThread, true);
        BringWindowToTop(h);
        bool ok = SetForegroundWindow(h);
        if (attached) AttachThreadInput(me, fgThread, false);
        return ok || GetForegroundWindow() == h;
    }

    static void Launch(string target)
    {
        target = target.Trim();
        if (target.Length == 0) return;
        if (target.StartsWith("shell:", StringComparison.OrdinalIgnoreCase)) Process.Start("explorer.exe", "\"" + target + "\"");
        else Process.Start(new ProcessStartInfo(target) { UseShellExecute = true });
    }

    // ------------------------------------------------------------------ network speed (net.txt)
    // Rainmeter's NetIn/NetOut "Best" interface can land on a virtual adapter (WSL / Hyper-V / VirtualBox) that
    // carries nothing; here we ask Windows which adapter routes to the internet and read that one's counters.
    static void NetLoop()
    {
        long lastIn = -1, lastOut = -1; string lastId = null;
        var sw = Stopwatch.StartNew(); double lastT = 0;
        int n = 0; System.Net.NetworkInformation.NetworkInterface nic = null;
        int idle = 0; long rate = 0;
        while (true)
        {
            try
            {
                // automatic speed test every AutoSpeedTestHours (Settings.inc, 0 = off), only after the network has
                // been quiet for a minute so it never competes with what you're doing
                idle = rate < 150000 ? idle + 1 : 0;
                if (n >= 300 && n % 60 == 0 && idle >= 60) MaybeAutoSpeedTest();
                if (nic == null || n % 10 == 0) nic = InternetAdapter();
                n++;
                if (nic != null)
                {
                    var st = nic.GetIPv4Statistics();
                    long bin = st.BytesReceived, bout = st.BytesSent;
                    double t = sw.Elapsed.TotalSeconds;
                    if (lastId == nic.Id && lastIn >= 0 && t > lastT && bin >= lastIn && bout >= lastOut)
                    {
                        double dt = t - lastT;
                        rate = (long)((bin - lastIn + bout - lastOut) / dt);
                        WriteAtomic(Data + "net.txt", "T " + UnixNow() + "\nDOWN " + ((long)((bin - lastIn) / dt)).ToString(CultureInfo.InvariantCulture) +
                            "\nUP " + ((long)((bout - lastOut) / dt)).ToString(CultureInfo.InvariantCulture) + "\nIF " + nic.Name + "\n");
                    }
                    lastIn = bin; lastOut = bout; lastT = t; lastId = nic.Id;
                }
            }
            catch (Exception e) { Log("net: " + e.Message); nic = null; }
            Thread.Sleep(1000);
        }
    }

    static void MaybeAutoSpeedTest()
    {
        double hours = 6;
        try
        {
            var m = Regex.Match(File.ReadAllText(Res + "Settings.inc"), @"(?m)^\s*AutoSpeedTestHours\s*=\s*([\d.]+)");
            if (m.Success) hours = double.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
        }
        catch { }
        if (hours <= 0) return;
        long last = 0;
        try
        {
            var m = Regex.Match(File.ReadAllText(Data + "speed.txt"), @"(?m)^T (\d+)");
            if (m.Success) last = long.Parse(m.Groups[1].Value);
        }
        catch { }
        if (UnixNow() - last < hours * 3600) return;
        var th = new Thread(delegate() { try { SpeedTest(); } catch (Exception e) { Log("auto speedtest: " + e.Message); } });
        th.IsBackground = true; th.Start();
    }

    static System.Net.NetworkInformation.NetworkInterface InternetAdapter()
    {
        uint idx;
        // 8.8.8.8 in network byte order; only used to ask the routing table, nothing is sent
        bool routed = GetBestInterface(BitConverter.ToUInt32(new byte[] { 8, 8, 8, 8 }, 0), out idx) == 0;
        System.Net.NetworkInformation.NetworkInterface fallback = null;
        foreach (var ni in System.Net.NetworkInformation.NetworkInterface.GetAllNetworkInterfaces())
        {
            if (ni.OperationalStatus != System.Net.NetworkInformation.OperationalStatus.Up) continue;
            if (ni.NetworkInterfaceType == System.Net.NetworkInformation.NetworkInterfaceType.Loopback) continue;
            try
            {
                var p4 = ni.GetIPProperties().GetIPv4Properties();
                if (routed && p4 != null && p4.Index == idx) return ni;
            }
            catch { }
            if (fallback == null)
                foreach (var g in ni.GetIPProperties().GatewayAddresses)
                    if (g.Address.AddressFamily == AddressFamily.InterNetwork && !g.Address.Equals(IPAddress.Any)) { fallback = ni; break; }
        }
        return fallback;
    }

    static SortedSet<string> ProcessExes()
    {
        var set = new SortedSet<string>();
        foreach (var p in Process.GetProcesses())
        {
            try { set.Add(p.ProcessName.ToLowerInvariant() + ".exe"); } catch { }
            p.Dispose();
        }
        return set;
    }

    // ------------------------------------------------------------------ Gmail unread (IMAP over TLS)
    static void MailLoop()
    {
        while (true)
        {
            string body;
            string cred = Unprotect("gmail.dat");
            if (cred == null) body = "OFF\n";
            else
            {
                string[] p = cred.Split('\n');
                string err = "bad saved login";
                int n = p.Length >= 2 ? GmailUnread(p[0].Trim(), p[1].Trim(), out err) : -1;
                body = n >= 0 ? ("UNREAD " + n + "\n") : ("ERR " + Clean(err ?? "unknown") + "\n");
            }
            try { WriteAtomic(Data + "mail.txt", "T " + UnixNow() + "\n" + body); } catch { }
            for (int i = 0; i < 120 && !File.Exists(Data + "mail.refresh"); i++) Thread.Sleep(1000);
            try { File.Delete(Data + "mail.refresh"); } catch { }
        }
    }

    public static string GmailLastError = "";

    static string Quote(string s) { return "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\""; }

    public static int GmailUnread(string user, string pass, out string error)
    {
        error = null; GmailLastError = "";
        try
        {
            using (var tcp = new TcpClient())
            {
                var ar = tcp.BeginConnect("imap.gmail.com", 993, null, null);
                if (!ar.AsyncWaitHandle.WaitOne(15000)) throw new Exception("no connection");
                tcp.EndConnect(ar);
                tcp.ReceiveTimeout = 15000; tcp.SendTimeout = 15000;
                using (var ssl = new SslStream(tcp.GetStream(), false))
                {
                    ssl.AuthenticateAsClient("imap.gmail.com", null, SslProtocols.Tls12, true);
                    var rd = new StreamReader(ssl, Encoding.ASCII);
                    var wr = new StreamWriter(ssl, Encoding.ASCII); wr.NewLine = "\r\n"; wr.AutoFlush = true;
                    rd.ReadLine();                                                     // greeting
                    string resp = Imap(rd, wr, "a1", "LOGIN " + Quote(user) + " " + Quote(pass));
                    if (!Regex.IsMatch(resp, @"^a1 OK", RegexOptions.Multiline)) throw new Exception("login refused - check the address and app password");
                    resp = Imap(rd, wr, "a2", "STATUS INBOX (UNSEEN)");
                    var m = Regex.Match(resp, @"UNSEEN (\d+)");
                    try { Imap(rd, wr, "a3", "LOGOUT"); } catch { }
                    if (!m.Success) throw new Exception("no unread count in reply");
                    return int.Parse(m.Groups[1].Value);
                }
            }
        }
        catch (Exception e) { error = e.Message; GmailLastError = e.Message; return -1; }
    }

    static string Imap(StreamReader rd, StreamWriter wr, string tag, string cmd)
    {
        wr.WriteLine(tag + " " + cmd);
        var sb = new StringBuilder();
        while (true)
        {
            string line = rd.ReadLine();
            if (line == null) throw new Exception("connection closed");
            sb.Append(line).Append('\n');
            if (line.StartsWith(tag + " ")) break;
        }
        return sb.ToString();
    }

    // ------------------------------------------------------------------ calendars (iCalendar feeds)
    public class CalSource { public bool On = true; public string Label = ""; public string Url = ""; }
    public class CalEvent { public DateTime StartUtc, EndUtc; public bool AllDay; public string Label = "", Title = ""; }

    public static List<CalSource> LoadCalendars()
    {
        var list = new List<CalSource>();
        string s = Unprotect("calendars.dat");
        if (s == null) return list;
        foreach (string line in s.Split('\n'))
        {
            string[] p = line.Split(new[] { '\t' }, 3);
            if (p.Length < 3 || p[2].Trim() == "") continue;
            var c = new CalSource(); c.On = p[0] == "1"; c.Label = p[1]; c.Url = p[2].Trim();
            list.Add(c);
        }
        return list;
    }

    public static void SaveCalendars(List<CalSource> list)
    {
        var sb = new StringBuilder();
        foreach (var c in list) sb.Append(c.On ? "1" : "0").Append('\t').Append(c.Label.Replace("\t", " ")).Append('\t').Append(c.Url.Trim()).Append('\n');
        Protect("calendars.dat", sb.ToString());
    }

    static void CalendarLoop()
    {
        while (true)
        {
            try { SyncCalendars(); } catch (Exception e) { Log("calendar: " + e.Message); }
            for (int i = 0; i < 600 && !File.Exists(Data + "calendar.refresh"); i++) Thread.Sleep(1000);
            try { File.Delete(Data + "calendar.refresh"); } catch { }
        }
    }

    public static string Fetch(string url)
    {
        if (url.StartsWith("webcal://", StringComparison.OrdinalIgnoreCase)) url = "https://" + url.Substring(9);
        var req = (HttpWebRequest)WebRequest.Create(url);
        req.UserAgent = "SpaceshipHUD/1.0";
        req.Timeout = 30000; req.ReadWriteTimeout = 30000;
        req.AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate;
        using (var resp = (HttpWebResponse)req.GetResponse())
        using (var sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8))
            return sr.ReadToEnd();
    }

    static void SyncCalendars()
    {
        var sources = LoadCalendars();
        var events = new List<CalEvent>();
        int on = 0, errors = 0;
        DateTime from = DateTime.UtcNow.AddHours(-6), to = DateTime.UtcNow.AddDays(21);
        foreach (var src in sources)
        {
            if (!src.On) continue;
            on++;
            try { events.AddRange(ParseIcs(Fetch(src.Url), src.Label, from, to)); }
            catch (Exception e) { errors++; Log("calendar '" + src.Label + "': " + e.Message); }
        }
        events.Sort(delegate(CalEvent a, CalEvent b) { return a.StartUtc.CompareTo(b.StartUtc); });
        var sb = new StringBuilder();
        sb.Append("T ").Append(UnixNow()).Append('\n').Append("C ").Append(on).Append(' ').Append(errors).Append('\n');
        int n = 0;
        foreach (var e in events)
        {
            if (e.EndUtc < DateTime.UtcNow) continue;
            sb.Append("E ").Append(Unix(e.StartUtc)).Append('|').Append(Unix(e.EndUtc)).Append('|').Append(e.AllDay ? 1 : 0).Append('|')
              .Append(Clean(e.Label)).Append('|').Append(Clean(e.Title)).Append('\n');
            if (++n >= 40) break;
        }
        WriteAtomic(Data + "calendar.txt", sb.ToString());
    }

    static string Clean(string s) { return Regex.Replace(s ?? "", @"[|\r\n\t]", " ").Trim(); }

    // IANA zone names (what Google uses) -> Windows zone ids
    static readonly Dictionary<string, string> Zones = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
        { "America/Chicago", "Central Standard Time" }, { "America/New_York", "Eastern Standard Time" },
        { "America/Denver", "Mountain Standard Time" }, { "America/Phoenix", "US Mountain Standard Time" },
        { "America/Los_Angeles", "Pacific Standard Time" }, { "America/Anchorage", "Alaskan Standard Time" },
        { "Pacific/Honolulu", "Hawaiian Standard Time" }, { "America/Detroit", "Eastern Standard Time" },
        { "America/Indiana/Indianapolis", "US Eastern Standard Time" }, { "America/Toronto", "Eastern Standard Time" },
        { "America/Mexico_City", "Central Standard Time (Mexico)" }, { "Europe/London", "GMT Standard Time" },
        { "Europe/Berlin", "W. Europe Standard Time" }, { "Europe/Paris", "Romance Standard Time" },
        { "Asia/Tokyo", "Tokyo Standard Time" }, { "Asia/Kolkata", "India Standard Time" }, { "Africa/Addis_Ababa", "E. Africa Standard Time" },
        { "UTC", "UTC" }, { "Etc/UTC", "UTC" }, { "GMT", "UTC" } };

    static TimeZoneInfo Zone(string tzid)
    {
        if (string.IsNullOrEmpty(tzid)) return null;
        tzid = tzid.Trim('"');
        string win;
        foreach (string id in new[] { Zones.TryGetValue(tzid, out win) ? win : null, tzid })
        {
            if (id == null) continue;
            try { return TimeZoneInfo.FindSystemTimeZoneById(id); } catch { }
        }
        return null;                                                                   // unknown: treat as local time
    }

    class Prop { public string Name = "", Value = ""; public Dictionary<string, string> P = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase); }

    static Prop ParseLine(string line)
    {
        var pr = new Prop();
        int colon = -1; bool q = false;
        for (int i = 0; i < line.Length; i++) { if (line[i] == '"') q = !q; else if (line[i] == ':' && !q) { colon = i; break; } }
        if (colon < 0) return null;
        string head = line.Substring(0, colon);
        pr.Value = line.Substring(colon + 1);
        string[] parts = head.Split(';');
        pr.Name = parts[0].ToUpperInvariant();
        for (int i = 1; i < parts.Length; i++) { int eq = parts[i].IndexOf('='); if (eq > 0) pr.P[parts[i].Substring(0, eq)] = parts[i].Substring(eq + 1); }
        return pr;
    }

    // returns the wall-clock time and its zone (null zone + Utc kind for Z times, null zone + Local for floating)
    static DateTime ParseIcsTime(Prop pr, out bool allDay, out TimeZoneInfo tz)
    {
        allDay = false; tz = null;
        string v = pr.Value.Trim();
        string val; pr.P.TryGetValue("VALUE", out val);
        if (v.Length == 8 || (val != null && val.ToUpperInvariant() == "DATE"))
        {
            allDay = true;
            return DateTime.ParseExact(v.Substring(0, 8), "yyyyMMdd", CultureInfo.InvariantCulture);
        }
        bool utc = v.EndsWith("Z");
        var dt = DateTime.ParseExact(v.TrimEnd('Z').Substring(0, 15), "yyyyMMdd'T'HHmmss", CultureInfo.InvariantCulture);
        if (utc) return DateTime.SpecifyKind(dt, DateTimeKind.Utc);
        string tzid; pr.P.TryGetValue("TZID", out tzid);
        tz = Zone(tzid);
        return dt;
    }

    static DateTime ToUtc(DateTime wall, TimeZoneInfo tz, bool allDay)
    {
        if (wall.Kind == DateTimeKind.Utc) return wall;
        if (allDay || tz == null) return TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(wall, DateTimeKind.Unspecified), TimeZoneInfo.Local);
        try { return TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(wall, DateTimeKind.Unspecified), tz); }
        catch { return TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(wall.AddHours(1), DateTimeKind.Unspecified), tz); }  // skipped DST hour
    }

    static string Unescape(string s)
    {
        return s.Replace("\\n", " ").Replace("\\N", " ").Replace("\\,", ",").Replace("\\;", ";").Replace("\\\\", "\\").Trim();
    }

    class Vevent
    {
        public string Uid = "", Summary = "", RRule = null, Status = "";
        public DateTime Start, End; public bool AllDay, HasEnd; public TimeZoneInfo Tz; public TimeSpan? Duration;
        public List<DateTime> ExUtc = new List<DateTime>();
        public DateTime? RecurrenceIdUtc;
    }

    public static List<CalEvent> ParseIcs(string ics, string label, DateTime fromUtc, DateTime toUtc)
    {
        // unfold continuation lines
        var lines = new List<string>();
        foreach (string raw in ics.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n'))
        {
            if ((raw.StartsWith(" ") || raw.StartsWith("\t")) && lines.Count > 0) lines[lines.Count - 1] += raw.Substring(1);
            else lines.Add(raw);
        }
        var evs = new List<Vevent>();
        Vevent cur = null; int depth = 0;
        foreach (string line in lines)
        {
            if (line == "BEGIN:VEVENT") { cur = new Vevent(); depth = 0; continue; }
            if (cur == null) continue;
            if (line.StartsWith("BEGIN:")) { depth++; continue; }                     // VALARM etc.
            if (line.StartsWith("END:") && depth > 0) { depth--; continue; }
            if (line == "END:VEVENT") { evs.Add(cur); cur = null; continue; }
            if (depth > 0) continue;
            var pr = ParseLine(line);
            if (pr == null) continue;
            bool ad; TimeZoneInfo tz;
            try
            {
                switch (pr.Name)
                {
                    case "UID": cur.Uid = pr.Value.Trim(); break;
                    case "SUMMARY": cur.Summary = Unescape(pr.Value); break;
                    case "STATUS": cur.Status = pr.Value.Trim().ToUpperInvariant(); break;
                    case "RRULE": cur.RRule = pr.Value.Trim(); break;
                    case "DTSTART": cur.Start = ParseIcsTime(pr, out ad, out tz); cur.AllDay = ad; cur.Tz = tz; break;
                    case "DTEND": cur.End = ParseIcsTime(pr, out ad, out tz); cur.HasEnd = true; break;
                    case "DURATION": cur.Duration = ParseDuration(pr.Value.Trim()); break;
                    case "EXDATE":
                        foreach (string v in pr.Value.Split(','))
                        {
                            var p2 = new Prop(); p2.Value = v; p2.P = pr.P;
                            DateTime w = ParseIcsTime(p2, out ad, out tz);
                            cur.ExUtc.Add(ToUtc(w, tz, ad));
                        }
                        break;
                    case "RECURRENCE-ID": { DateTime w = ParseIcsTime(pr, out ad, out tz); cur.RecurrenceIdUtc = ToUtc(w, tz, ad); } break;
                }
            }
            catch { }
        }
        // overrides: (UID, original start) -> replaced
        var overridden = new HashSet<string>();
        foreach (var e in evs) if (e.RecurrenceIdUtc.HasValue) overridden.Add(e.Uid + "|" + Unix(e.RecurrenceIdUtc.Value));
        var outp = new List<CalEvent>();
        foreach (var e in evs)
        {
            if (e.Start == DateTime.MinValue || e.Status == "CANCELLED") continue;
            TimeSpan len = e.HasEnd ? (e.End - e.Start) : (e.Duration ?? (e.AllDay ? TimeSpan.FromDays(1) : TimeSpan.Zero));
            if (e.HasEnd && e.End.Kind != e.Start.Kind) len = ToUtc(e.End, e.Tz, e.AllDay) - ToUtc(e.Start, e.Tz, e.AllDay);
            if (len < TimeSpan.Zero) len = TimeSpan.Zero;
            var starts = (e.RRule != null && !e.RecurrenceIdUtc.HasValue) ? Expand(e, fromUtc - len, toUtc) : new List<DateTime> { e.Start };
            foreach (DateTime wall in starts)
            {
                DateTime su = ToUtc(wall, e.Tz, e.AllDay);
                if (e.RRule != null && !e.RecurrenceIdUtc.HasValue)
                {
                    if (overridden.Contains(e.Uid + "|" + Unix(su))) continue;
                    bool ex = false;
                    foreach (var x in e.ExUtc) if (Math.Abs((x - su).TotalMinutes) < 1) { ex = true; break; }
                    if (ex) continue;
                }
                DateTime eu = e.AllDay ? ToUtc(wall + len, e.Tz, true) : su + len;
                if (eu < fromUtc || su > toUtc) continue;
                var ce = new CalEvent(); ce.StartUtc = su; ce.EndUtc = eu > su ? eu : su.AddMinutes(1); ce.AllDay = e.AllDay;
                ce.Label = label; ce.Title = e.Summary == "" ? "(no title)" : e.Summary;
                outp.Add(ce);
            }
        }
        return outp;
    }

    static TimeSpan ParseDuration(string s)
    {
        var m = Regex.Match(s, @"^([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$");
        if (!m.Success) return TimeSpan.Zero;
        Func<int, int> g = delegate(int i) { return m.Groups[i].Success ? int.Parse(m.Groups[i].Value) : 0; };
        var t = new TimeSpan(g(2) * 7 + g(3), g(4), g(5), g(6));
        return m.Groups[1].Value == "-" ? -t : t;
    }

    static readonly string[] DayCodes = { "SU", "MO", "TU", "WE", "TH", "FR", "SA" };

    // RRULE expansion in the event's own wall-clock time (so a 9:00 class stays 9:00 across DST)
    static List<DateTime> Expand(Vevent e, DateTime fromUtc, DateTime toUtc)
    {
        var res = new List<DateTime>();
        var rule = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (string part in e.RRule.Split(';')) { int eq = part.IndexOf('='); if (eq > 0) rule[part.Substring(0, eq)] = part.Substring(eq + 1); }
        string freq; if (!rule.TryGetValue("FREQ", out freq)) return res;
        freq = freq.ToUpperInvariant();
        int interval = 1; string sv;
        if (rule.TryGetValue("INTERVAL", out sv)) int.TryParse(sv, out interval);
        if (interval < 1) interval = 1;
        int count = -1; if (rule.TryGetValue("COUNT", out sv)) int.TryParse(sv, out count);
        DateTime? untilUtc = null;
        if (rule.TryGetValue("UNTIL", out sv))
        {
            var p = new Prop(); p.Value = sv; bool ad; TimeZoneInfo tz;
            try { DateTime w = ParseIcsTime(p, out ad, out tz); untilUtc = w.Kind == DateTimeKind.Utc ? w : ToUtc(ad ? w.AddDays(1).AddSeconds(-1) : w, e.Tz, false); } catch { }
        }
        var byDay = new List<DayOfWeek>(); var byDayNth = new List<KeyValuePair<int, DayOfWeek>>();
        if (rule.TryGetValue("BYDAY", out sv))
            foreach (string d in sv.Split(','))
            {
                var m = Regex.Match(d.Trim().ToUpperInvariant(), @"^([+-]?\d+)?(SU|MO|TU|WE|TH|FR|SA)$");
                if (!m.Success) continue;
                var dow = (DayOfWeek)Array.IndexOf(DayCodes, m.Groups[2].Value);
                if (m.Groups[1].Success) byDayNth.Add(new KeyValuePair<int, DayOfWeek>(int.Parse(m.Groups[1].Value), dow)); else byDay.Add(dow);
            }
        var byMonthDay = new List<int>();
        if (rule.TryGetValue("BYMONTHDAY", out sv)) foreach (string d in sv.Split(',')) { int x; if (int.TryParse(d, out x)) byMonthDay.Add(x); }

        DateTime start = e.Start;
        int produced = 0, guard = 0;
        Func<DateTime, bool> emit = delegate(DateTime w)
        {
            if (w < start) return true;
            DateTime u = ToUtc(w, e.Tz, e.AllDay);
            if (untilUtc.HasValue && u > untilUtc.Value) return false;
            produced++;
            if (count > 0 && produced > count) return false;
            if (u >= fromUtc && u <= toUtc) res.Add(w);
            return u <= toUtc;                                                         // past the window: stop
        };
        if (freq == "DAILY")
        {
            for (DateTime d = start; guard++ < 5000; d = d.AddDays(interval))
            {
                if (byDay.Count > 0 && !byDay.Contains(d.DayOfWeek)) continue;
                if (!emit(d)) break;
            }
        }
        else if (freq == "WEEKLY")
        {
            var days = byDay.Count > 0 ? byDay : new List<DayOfWeek> { start.DayOfWeek };
            DateTime weekStart = start.Date.AddDays(-(int)start.DayOfWeek);           // Sunday-based weeks
            bool go = true;
            for (int w = 0; go && guard++ < 3000; w += interval)
            {
                for (int di = 0; di < 7 && go; di++)
                {
                    DateTime d = weekStart.AddDays(w * 7 + di);
                    if (!days.Contains(d.DayOfWeek)) continue;
                    go = emit(d + start.TimeOfDay);
                }
            }
        }
        else if (freq == "MONTHLY")
        {
            bool go = true;
            for (int mo = 0; go && guard++ < 600; mo += interval)
            {
                DateTime m0 = new DateTime(start.Year, start.Month, 1).AddMonths(mo);
                var cands = new List<DateTime>();
                int dim = DateTime.DaysInMonth(m0.Year, m0.Month);
                if (byDayNth.Count > 0)
                {
                    foreach (var kv in byDayNth)
                    {
                        var hits = new List<DateTime>();
                        for (int d = 1; d <= dim; d++) { var dd = new DateTime(m0.Year, m0.Month, d); if (dd.DayOfWeek == kv.Value) hits.Add(dd); }
                        int idx = kv.Key > 0 ? kv.Key - 1 : hits.Count + kv.Key;
                        if (idx >= 0 && idx < hits.Count) cands.Add(hits[idx]);
                    }
                }
                else
                {
                    var mds = byMonthDay.Count > 0 ? byMonthDay : new List<int> { start.Day };
                    foreach (int md in mds) { int d = md > 0 ? md : dim + md + 1; if (d >= 1 && d <= dim) cands.Add(new DateTime(m0.Year, m0.Month, d)); }
                }
                cands.Sort();
                foreach (var d in cands) { if (!go) break; go = emit(d + start.TimeOfDay); }
            }
        }
        else if (freq == "YEARLY")
        {
            for (int y = 0; guard++ < 200; y += interval)
            {
                int yr = start.Year + y;
                if (start.Month == 2 && start.Day == 29 && !DateTime.IsLeapYear(yr)) continue;
                if (!emit(new DateTime(yr, start.Month, start.Day) + start.TimeOfDay)) break;
            }
        }
        return res;
    }

    // ------------------------------------------------------------------ brightness + microphone (sys.txt)
    static void SysLoop()
    {
        while (true)
        {
            int b = GetBrightness();
            float mic = -1; bool mute = false;
            try { mic = MicVolume.Get(out mute); } catch { }
            try
            {
                WriteAtomic(Data + "sys.txt", "T " + UnixNow() + "\nBRIGHT " + b + "\nMIC " + (mic < 0 ? -1 : (int)Math.Round(mic * 100)) + "\nMICMUTE " + (mute ? 1 : 0) + "\n");
            }
            catch { }
            Thread.Sleep(3000);
        }
    }

    public static int GetBrightness()
    {
        try
        {
            using (var s = new ManagementObjectSearcher("root\\WMI", "SELECT CurrentBrightness FROM WmiMonitorBrightness"))
                foreach (ManagementObject o in s.Get()) return Convert.ToInt32(o["CurrentBrightness"]);
        }
        catch { }
        return -1;
    }

    public static void SetBrightness(int v)
    {
        v = Math.Max(0, Math.Min(100, v));
        using (var s = new ManagementObjectSearcher("root\\WMI", "SELECT * FROM WmiMonitorBrightnessMethods"))
            foreach (ManagementObject o in s.Get()) o.InvokeMethod("WmiSetBrightness", new object[] { (uint)1, (byte)v });
    }

    // ------------------------------------------------------------------ to-do note picker
    static void PickTodo()
    {
        using (var d = new OpenFileDialog())
        {
            d.Title = "Spaceship HUD - choose your Obsidian to-do note";
            d.Filter = "Markdown notes (*.md)|*.md|All files (*.*)|*.*";
            if (d.ShowDialog() == DialogResult.OK)
            {
                SaveSetting("ObsidianTodo", d.FileName);
                Bang("[!RefreshGroup Spaceship]");
            }
        }
    }

    // ------------------------------------------------------------------ speed test (Ookla CLI)
    static string FindSpeedtest()
    {
        var cands = new List<string>();
        string la = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        cands.Add(Path.Combine(la, "Microsoft\\WinGet\\Links\\speedtest.exe"));
        foreach (string dir in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(';'))
            if (dir.Trim() != "") cands.Add(Path.Combine(dir.Trim(), "speedtest.exe"));
        try
        {
            string pk = Path.Combine(la, "Microsoft\\WinGet\\Packages");
            if (Directory.Exists(pk))
                foreach (string d in Directory.GetDirectories(pk, "Ookla.Speedtest*")) cands.Add(Path.Combine(d, "speedtest.exe"));
        }
        catch { }
        foreach (string c in cands) { try { if (File.Exists(c)) return c; } catch { } }
        return null;
    }

    static void SpeedTest()
    {
        bool created;
        using (var mutex = new Mutex(true, "SpaceshipSpeedtest", out created))
        {
            if (!created) return;
            WriteAtomic(Data + "speed.txt", "T " + UnixNow() + "\nSTATE testing\n");
            Bang("[!UpdateGroup Spaceship]");
            string exe = FindSpeedtest();
            if (exe == null) { WriteAtomic(Data + "speed.txt", "T " + UnixNow() + "\nSTATE error\nERR speedtest not installed - winget install Ookla.Speedtest.CLI\n"); return; }
            var psi = new ProcessStartInfo(exe, "--format=json --accept-license --accept-gdpr");
            psi.UseShellExecute = false; psi.RedirectStandardOutput = true; psi.RedirectStandardError = true; psi.CreateNoWindow = true;
            string json;
            using (var p = Process.Start(psi)) { json = p.StandardOutput.ReadToEnd(); p.WaitForExit(120000); }
            var dl = Regex.Match(json, "\"download\"\\s*:\\s*\\{[^}]*?\"bandwidth\"\\s*:\\s*(\\d+)");
            var ul = Regex.Match(json, "\"upload\"\\s*:\\s*\\{[^}]*?\"bandwidth\"\\s*:\\s*(\\d+)");
            var pg = Regex.Match(json, "\"ping\"\\s*:\\s*\\{[^}]*?\"latency\"\\s*:\\s*([\\d.]+)");
            if (!dl.Success || !ul.Success) { WriteAtomic(Data + "speed.txt", "T " + UnixNow() + "\nSTATE error\nERR no result\n"); Log("speedtest: " + json); return; }
            double down = long.Parse(dl.Groups[1].Value) * 8 / 1e6, up = long.Parse(ul.Groups[1].Value) * 8 / 1e6;
            string ping = pg.Success ? pg.Groups[1].Value : "0";
            WriteAtomic(Data + "speed.txt", string.Format(CultureInfo.InvariantCulture, "T {0}\nSTATE done\nDOWN {1:0.0}\nUP {2:0.0}\nPING {3}\n", UnixNow(), down, up, ping));
            SaveSetting("LinkDownMbps", Math.Round(down).ToString(CultureInfo.InvariantCulture));
            SaveSetting("LinkUpMbps", Math.Round(up).ToString(CultureInfo.InvariantCulture));
            SaveSetting("LastSpeedTest", DateTime.Now.ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture));
            Bang("[!UpdateGroup Spaceship]");
        }
    }

    // ------------------------------------------------------------------ setup windows (HUD-coloured WinForms)
    static readonly Color Bg = Color.FromArgb(4, 12, 20), Panel = Color.FromArgb(8, 26, 38), Acc = Color.FromArgb(0, 210, 255), Txt = Color.FromArgb(200, 240, 255);

    static void Style(Control c)
    {
        c.BackColor = c is TextBox || c is DataGridView ? Panel : Bg;
        c.ForeColor = Txt;
        c.Font = new Font("Segoe UI", 10f);
        var b = c as Button;
        if (b != null) { b.FlatStyle = FlatStyle.Flat; b.FlatAppearance.BorderColor = Acc; b.BackColor = Panel; b.ForeColor = Acc; b.Height = 32; }
        foreach (Control k in c.Controls) Style(k);
    }

    class GmailForm : Form
    {
        TextBox user = new TextBox(), pass = new TextBox();
        Label status = new Label();
        public GmailForm()
        {
            Text = "Spaceship HUD - Gmail unread count"; Width = 520; Height = 330; FormBorderStyle = FormBorderStyle.FixedDialog; MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            var intro = new Label { Text = "The HUD shows your Gmail unread count. It signs in with an app password (Google Account > Security > 2-Step Verification > App passwords), not your normal password. Both are stored encrypted for your Windows account only.", Left = 16, Top = 12, Width = 470, Height = 64 };
            var l1 = new Label { Text = "Gmail address", Left = 16, Top = 86, Width = 140 };
            user.SetBounds(160, 82, 330, 28);
            var l2 = new Label { Text = "App password", Left = 16, Top = 126, Width = 140 };
            pass.SetBounds(160, 122, 330, 28); pass.UseSystemPasswordChar = true;
            status.SetBounds(16, 166, 474, 40);
            var test = new Button { Text = "TEST", Left = 160, Top = 216, Width = 100 };
            var save = new Button { Text = "SAVE", Left = 270, Top = 216, Width = 100 };
            var clear = new Button { Text = "REMOVE", Left = 380, Top = 216, Width = 110 };
            Controls.AddRange(new Control[] { intro, l1, user, l2, pass, status, test, save, clear });
            Style(this); status.ForeColor = Acc;
            string cur = Unprotect("gmail.dat");
            if (cur != null) { string[] p = cur.Split('\n'); user.Text = p[0]; status.Text = "Saved login found. Enter a new app password to replace it."; }
            test.Click += delegate { string err; int n = GmailUnread(user.Text.Trim(), pass.Text.Replace(" ", "").Trim(), out err); status.Text = n >= 0 ? ("Works - " + n + " unread.") : ("Failed: " + err); };
            save.Click += delegate
            {
                if (user.Text.Trim() == "" || pass.Text.Trim() == "") { status.Text = "Enter both the address and the app password."; return; }
                Protect("gmail.dat", user.Text.Trim() + "\n" + pass.Text.Replace(" ", "").Trim());
                try { File.WriteAllText(Data + "mail.refresh", "1"); } catch { }
                status.Text = "Saved. The count appears within a few seconds."; Bang("[!UpdateGroup Spaceship]");
            };
            clear.Click += delegate { try { File.Delete(Store + "gmail.dat"); File.WriteAllText(Data + "mail.refresh", "1"); } catch { } status.Text = "Removed."; };
        }
    }

    class CalendarForm : Form
    {
        DataGridView grid = new DataGridView();
        Label status = new Label();
        public CalendarForm()
        {
            Text = "Spaceship HUD - calendars"; Width = 860; Height = 460; StartPosition = FormStartPosition.CenterScreen; MinimizeBox = false;
            var intro = new Label { Text = "Calendar feed links (.ics). Google Calendar: Settings > your calendar > Integrate calendar > \"Secret address in iCal format\". Subscribed (from URL) calendars: paste the feed URL you subscribed with. Untick a row to hide it. Stored encrypted for your Windows account.", Left = 12, Top = 10, Width = 820, Height = 46 };
            grid.SetBounds(12, 60, 820, 290);
            grid.AllowUserToAddRows = true; grid.RowHeadersVisible = false; grid.BorderStyle = BorderStyle.None;
            grid.EnableHeadersVisualStyles = false;
            grid.ColumnHeadersDefaultCellStyle.BackColor = Bg; grid.ColumnHeadersDefaultCellStyle.ForeColor = Acc;
            grid.DefaultCellStyle.BackColor = Panel; grid.DefaultCellStyle.ForeColor = Txt; grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(0, 80, 110);
            grid.GridColor = Color.FromArgb(0, 70, 95); grid.BackgroundColor = Panel;
            grid.Columns.Add(new DataGridViewCheckBoxColumn { HeaderText = "SHOW", Width = 60 });
            grid.Columns.Add(new DataGridViewTextBoxColumn { HeaderText = "LABEL", Width = 140 });
            grid.Columns.Add(new DataGridViewTextBoxColumn { HeaderText = "FEED LINK", AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill });
            foreach (var c in LoadCalendars()) grid.Rows.Add(c.On, c.Label, c.Url);
            status.SetBounds(12, 358, 500, 40);
            var test = new Button { Text = "TEST", Left = 520, Top = 362, Width = 100 };
            var save = new Button { Text = "SAVE", Left = 630, Top = 362, Width = 100 };
            var close = new Button { Text = "CLOSE", Left = 740, Top = 362, Width = 92 };
            Controls.AddRange(new Control[] { intro, grid, status, test, save, close });
            Style(this); status.ForeColor = Acc;
            test.Click += delegate
            {
                var list = Rows(); int ok = 0, ev = 0; string bad = "";
                foreach (var c in list) { if (!c.On) continue; try { ev += ParseIcs(Fetch(c.Url), c.Label, DateTime.UtcNow, DateTime.UtcNow.AddDays(14)).Count; ok++; } catch (Exception e) { bad = c.Label + ": " + e.Message; } }
                status.Text = bad == "" ? (ok + " feed(s) OK - " + ev + " events in the next 2 weeks.") : ("Problem - " + bad);
            };
            save.Click += delegate
            {
                SaveCalendars(Rows());
                try { File.WriteAllText(Data + "calendar.refresh", "1"); } catch { }
                status.Text = "Saved. The mission clock updates within a few seconds."; Bang("[!UpdateGroup Spaceship]");
            };
            close.Click += delegate { Close(); };
        }
        List<CalSource> Rows()
        {
            var list = new List<CalSource>();
            foreach (DataGridViewRow r in grid.Rows)
            {
                if (r.IsNewRow) continue;
                string url = Convert.ToString(r.Cells[2].Value ?? "").Trim();
                if (url == "") continue;
                var c = new CalSource(); c.On = r.Cells[0].Value is bool ? (bool)r.Cells[0].Value : true;
                c.Label = Convert.ToString(r.Cells[1].Value ?? "").Trim(); if (c.Label == "") c.Label = "CAL";
                c.Url = url; list.Add(c);
            }
            return list;
        }
    }
}

// ------------------------------------------------------------------ default microphone level (Core Audio)
public static class MicVolume
{
    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorCom { }

    [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceEnumerator
    {
        int EnumAudioEndpoints(int dataFlow, int stateMask, out IntPtr devices);
        int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice device);
    }

    [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDevice
    {
        int Activate(ref Guid iid, int clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object iface);
    }

    [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioEndpointVolume
    {
        int RegisterControlChangeNotify(IntPtr notify);
        int UnregisterControlChangeNotify(IntPtr notify);
        int GetChannelCount(out uint count);
        int SetMasterVolumeLevel(float levelDB, ref Guid ctx);
        int SetMasterVolumeLevelScalar(float level, ref Guid ctx);
        int GetMasterVolumeLevel(out float levelDB);
        int GetMasterVolumeLevelScalar(out float level);
        int SetChannelVolumeLevel(uint channel, float levelDB, ref Guid ctx);
        int SetChannelVolumeLevelScalar(uint channel, float level, ref Guid ctx);
        int GetChannelVolumeLevel(uint channel, out float levelDB);
        int GetChannelVolumeLevelScalar(uint channel, out float level);
        int SetMute([MarshalAs(UnmanagedType.Bool)] bool mute, ref Guid ctx);
        int GetMute([MarshalAs(UnmanagedType.Bool)] out bool mute);
    }

    static IAudioEndpointVolume Endpoint()
    {
        var en = (IMMDeviceEnumerator)new MMDeviceEnumeratorCom();
        IMMDevice dev;
        if (en.GetDefaultAudioEndpoint(1, 0, out dev) != 0 || dev == null) return null;   // eCapture, eConsole
        var iid = typeof(IAudioEndpointVolume).GUID;
        object o;
        if (dev.Activate(ref iid, 23, IntPtr.Zero, out o) != 0) return null;              // CLSCTX_ALL
        return o as IAudioEndpointVolume;
    }

    public static float Get(out bool mute)
    {
        mute = false;
        var ep = Endpoint();
        if (ep == null) return -1;
        float v; ep.GetMasterVolumeLevelScalar(out v); ep.GetMute(out mute);
        return v;
    }

    public static void Set(float v)
    {
        var ep = Endpoint();
        if (ep == null) return;
        var g = Guid.Empty;
        ep.SetMasterVolumeLevelScalar(Math.Max(0f, Math.Min(1f, v)), ref g);
        if (v > 0) ep.SetMute(false, ref g);
    }
}
