namespace ShipCore.Core.Tests;

public class WallpaperTests
{
    private static readonly Rect Screen = new(0, 0, 2560, 1600), Work = new(0, 0, 2560, 1552);
    private static WindowSnapshot Snap(string cls, Rect b, bool ours = false) => new(new WindowInfo(cls, "app", b, ours), Screen, NotificationState.AcceptsNotifications, []);

    [Theory]
    [InlineData(@"C:\Walls\hole.mp4", @"C:\Walls\hole.mp4")]
    [InlineData(@"""C:\Walls\hole.webm""", @"C:\Walls\hole.webm")]
    [InlineData(@"  C:\Walls\pic.JPG ", @"C:\Walls\pic.JPG")]
    public void AcceptsLocalVideosAndPictures(string setting, string want) => Assert.Equal(want, Wallpaper.FilePath(setting));

    [Theory]
    [InlineData(null)] [InlineData("")] [InlineData("hole.mp4")] [InlineData(@"\\server\share\hole.mp4")]
    [InlineData(@"C:\Walls\hole.mlw")] [InlineData(@"C:\Walls\run.exe")] [InlineData(@"C:\Walls")]
    public void RefusesEverythingElse(string? setting) => Assert.Null(Wallpaper.FilePath(setting));

    [Theory]
    [InlineData(3840, 2160, "screen", 2844, 1600)] // a 16:9 4K video still covers the 16:10 screen
    [InlineData(3840, 2160, "1080", 1920, 1080)]
    [InlineData(2160, 3840, "720", 720, 1280)]     // portrait: the short side
    public void ShrinksToTheLevel(int w, int h, string q, int ww, int wh) => Assert.Equal((ww, wh), Wallpaper.Scaled(w, h, q, 2560, 1600));

    [Theory]
    [InlineData(3840, 2160, "max")] [InlineData(3840, 2160, null)] [InlineData(3840, 2160, "9999")]
    [InlineData(1920, 1080, "1440")] [InlineData(2560, 1600, "screen")] [InlineData(0, 0, "720")]
    public void KeepsTheOriginal(int w, int h, string? q) => Assert.Null(Wallpaper.Scaled(w, h, q, 2560, 1600));

    [Fact]
    public void ACacheNameChangesWithTheSourceAndSize()
    {
        var t = new DateTime(2026, 10, 30);
        var a = Wallpaper.CacheName(@"C:\W\hole.mp4", 100, t, (2560, 1440));
        Assert.Equal(a, Wallpaper.CacheName(@"c:\w\HOLE.mp4", 100, t, (2560, 1440)));
        Assert.NotEqual(a, Wallpaper.CacheName(@"C:\W\hole.mp4", 101, t, (2560, 1440)));
        Assert.NotEqual(a, Wallpaper.CacheName(@"C:\W\hole.mp4", 100, t, (1920, 1080)));
        Assert.Matches("^wall-[0-9A-F]{16}-2560x1440\\.mp4$", a);
        Assert.Matches("^wall-[0-9A-F]{16}\\.webm$", Wallpaper.CacheName(@"C:\W\hole.WEBM", 100, t, null));
    }

    [Fact] public void AMaximisedWindowHidesIt() => Assert.True(Wallpaper.Hidden(Snap("Chrome_WidgetWin_1", Work), Work));
    [Fact] public void AFullscreenGameHidesIt() => Assert.True(Wallpaper.Hidden(Snap("UnrealWindow", Screen), Work));
    [Fact] public void ASmallWindowDoesNot() => Assert.False(Wallpaper.Hidden(Snap("Notepad", new Rect(100, 100, 900, 700)), Work));
    [Fact] public void TheDesktopAndOurWindowDoNot()
    {
        Assert.False(Wallpaper.Hidden(Snap("Progman", Screen), Work));
        Assert.False(Wallpaper.Hidden(Snap("CSpace", Screen, ours: true), Work));
        Assert.False(Wallpaper.Hidden(new WindowSnapshot(null, Screen, NotificationState.AcceptsNotifications, []), Work));
    }
}
