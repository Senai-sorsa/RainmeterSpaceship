using System.ComponentModel;

namespace ShipCore.Core.Tests;

public class ProcessNamesTests
{
    [Fact]
    public void SkipsAnEntryThatThrowsBecauseTheProcessExitedOrIsDenied()
    {
        var names = ProcessNames.Collect([
            () => "a",
            () => throw new InvalidOperationException("exited"),
            () => "b",
            () => throw new Win32Exception(5),
            () => "c"]);
        Assert.Equal(["a", "b", "c"], names);
    }

    [Fact]
    public void OtherExceptionsStillPropagate() =>
        Assert.Throws<ArgumentException>(() => ProcessNames.Collect([() => throw new ArgumentException("bug")]));
}
