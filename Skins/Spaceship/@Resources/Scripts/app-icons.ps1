# Extracts each app's real icon for the HUD and prepares it for the neon look.
# Input : ..\Data\IconQueue.txt   one "id|path" per line (written by the Controller after a Start menu scan);
#         path is a file (exe / lnk) or shell:AppsFolder\<AppID> for Start menu and Store apps.
# Output: ..\Icons\<id>.png       128 x 128, greyscale with alpha (Rainmeter recolours it theme-colour -> white)
#         ..\Icons\<id>_glow.png  the icon's silhouette, blurred (tinted with the theme colour as a glow)
#         ..\Icons\_index.txt     the ids that have icons
$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path $PSScriptRoot -Parent
$queue = Join-Path $root 'Data\IconQueue.txt'
$dir = Join-Path $root 'Icons'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
if (-not (Test-Path $queue)) { Write-Output 'icons=0'; exit }

Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class HudIcons {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct SHFILEINFO {
        public IntPtr hIcon; public int iIcon; public uint dwAttributes;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szDisplayName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 80)] public string szTypeName;
    }
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    static extern int SHParseDisplayName(string name, IntPtr bindCtx, out IntPtr pidl, uint sfgaoIn, out uint sfgaoOut);
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    static extern IntPtr SHGetFileInfo(IntPtr pidl, uint attr, ref SHFILEINFO info, uint size, uint flags);
    [DllImport("shell32.dll", EntryPoint = "#727")]
    static extern int SHGetImageList(int list, ref Guid iid, out IImageList ppv);
    [DllImport("user32.dll")] static extern bool DestroyIcon(IntPtr h);
    [DllImport("ole32.dll")] static extern void CoTaskMemFree(IntPtr p);

    [ComImport, Guid("46EB5926-582E-4017-9FDF-E8998DAA0950"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IImageList {
        [PreserveSig] int Add(IntPtr bmp, IntPtr mask, ref int i);
        [PreserveSig] int ReplaceIcon(int i, IntPtr icon, ref int pi);
        [PreserveSig] int SetOverlayImage(int image, int overlay);
        [PreserveSig] int Replace(int i, IntPtr bmp, IntPtr mask);
        [PreserveSig] int AddMasked(IntPtr bmp, int mask, ref int i);
        [PreserveSig] int Draw(IntPtr p);
        [PreserveSig] int Remove(int i);
        [PreserveSig] int GetIcon(int i, int flags, ref IntPtr icon);
    }

    // the shell's 256 px icon (SHIL_JUMBO) for a path or shell:AppsFolder\AppID, with alpha
    static Bitmap Jumbo(string path) {
        IntPtr pidl; uint outAttr;
        if (SHParseDisplayName(path, IntPtr.Zero, out pidl, 0, out outAttr) != 0) return null;
        SHFILEINFO info = new SHFILEINFO();
        SHGetFileInfo(pidl, 0, ref info, (uint)Marshal.SizeOf(info), 0x4000 | 0x8);  // SYSICONINDEX | PIDL
        CoTaskMemFree(pidl);
        Guid iid = new Guid("46EB5926-582E-4017-9FDF-E8998DAA0950");
        IImageList list;
        if (SHGetImageList(4, ref iid, out list) != 0) return null;
        IntPtr h = IntPtr.Zero;
        list.GetIcon(info.iIcon, 1, ref h);   // ILD_TRANSPARENT
        if (h == IntPtr.Zero) return null;
        Bitmap bmp;
        using (Icon ic = Icon.FromHandle(h)) { bmp = ic.ToBitmap(); }
        DestroyIcon(h);
        return bmp;
    }

    static Rectangle AlphaBounds(Bitmap b) {
        int x0 = b.Width, y0 = b.Height, x1 = -1, y1 = -1;
        for (int y = 0; y < b.Height; y++)
            for (int x = 0; x < b.Width; x++)
                if (b.GetPixel(x, y).A > 24) { if (x < x0) x0 = x; if (y < y0) y0 = y; if (x > x1) x1 = x; if (y > y1) y1 = y; }
        if (x1 < 0) return Rectangle.Empty;
        return new Rectangle(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
    }

    static float[] BoxBlur(float[] a, int w, int h, int r) {
        float[] tmp = new float[a.Length], o = new float[a.Length];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                float s = 0; int n = 0;
                for (int k = -r; k <= r; k++) { int xx = x + k; if (xx >= 0 && xx < w) { s += a[y * w + xx]; n++; } }
                tmp[y * w + x] = s / n;
            }
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                float s = 0; int n = 0;
                for (int k = -r; k <= r; k++) { int yy = y + k; if (yy >= 0 && yy < h) { s += tmp[yy * w + x]; n++; } }
                o[y * w + x] = s / n;
            }
        return o;
    }

    // writes <out>.png (greyscale + alpha, contrast lifted) and <out>_glow.png (blurred silhouette)
    public static bool Make(string path, string outBase) {
        Bitmap src = Jumbo(path);
        if (src == null) return false;
        Rectangle r = AlphaBounds(src);
        if (r.IsEmpty) return false;
        const int S = 128, PAD = 14;
        int inner = S - 2 * PAD;
        float k = Math.Min((float)inner / r.Width, (float)inner / r.Height);
        int w = Math.Max(1, (int)(r.Width * k)), h = Math.Max(1, (int)(r.Height * k));
        Bitmap fit = new Bitmap(S, S, PixelFormat.Format32bppArgb);
        using (Graphics g = Graphics.FromImage(fit)) {
            g.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;
            g.DrawImage(src, new Rectangle((S - w) / 2, (S - h) / 2, w, h), r, GraphicsUnit.Pixel);
        }
        float[] alpha = new float[S * S];
        Bitmap grey = new Bitmap(S, S, PixelFormat.Format32bppArgb);
        for (int y = 0; y < S; y++)
            for (int x = 0; x < S; x++) {
                Color c = fit.GetPixel(x, y);
                float l = (0.30f * c.R + 0.59f * c.G + 0.11f * c.B) / 255f;
                l = Math.Max(0f, Math.Min(1f, (l - 0.12f) / 0.76f));      // lift contrast so logos read
                int v = (int)(l * 255);
                grey.SetPixel(x, y, Color.FromArgb(c.A, v, v, v));
                alpha[y * S + x] = c.A / 255f;
            }
        float[] blur = BoxBlur(BoxBlur(BoxBlur(alpha, S, S, 5), S, S, 5), S, S, 5);
        Bitmap glow = new Bitmap(S, S, PixelFormat.Format32bppArgb);
        for (int i = 0; i < S * S; i++)
            glow.SetPixel(i % S, i / S, Color.FromArgb((int)Math.Min(255f, blur[i] * 340f), 255, 255, 255));
        grey.Save(outBase + ".png", ImageFormat.Png);
        glow.Save(outBase + "_glow.png", ImageFormat.Png);
        src.Dispose(); fit.Dispose(); grey.Dispose(); glow.Dispose();
        return true;
    }
}
'@

$done = @()
foreach ($line in [IO.File]::ReadAllLines($queue)) {
    $parts = $line.Split('|', 2)
    if ($parts.Count -lt 2) { continue }
    $id = $parts[0].Trim(); $path = $parts[1].Trim()
    if ($id -eq '' -or $path -eq '') { continue }
    try { if ([HudIcons]::Make($path, (Join-Path $dir $id))) { $done += $id } } catch { }
}
[IO.File]::WriteAllLines((Join-Path $dir '_index.txt'), [string[]]$done)
Write-Output "icons=$($done.Count)"
