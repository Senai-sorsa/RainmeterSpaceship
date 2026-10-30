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
