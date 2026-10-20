namespace ShipCore.Core.Tests;

public class PipeGateTests
{
    private readonly FakeClock _clock = new();
    private PipeGate Gate() => new(_clock, "n0nce", "sess1", TimeSpan.FromSeconds(10));

    [Fact]
    public void FailedHellosAreCappedAndANullNonceIsRefused()
    {
        var g = Gate();
        Assert.False(g.Verify(new Hello(null!, 42, "sess1"), 42));
        Assert.False(g.Verify(new Hello("bad", 42, "sess1"), 42));
        Assert.False(g.Verify(new Hello("bad", 42, "sess1"), 42));
        Assert.False(g.Verify(new Hello("n0nce", 42, "sess1"), 42)); // fourth try, even a right hello, is too late
    }

    [Fact]
    public void NothingIsSentBeforeAValidHello()
    {
        var g = Gate();
        var sent = 0;
        Assert.False(g.TrySend(() => sent++));
        Assert.True(g.Verify(new Hello("n0nce", 42, "sess1"), 42));
        Assert.True(g.TrySend(() => sent++));
        Assert.Equal(1, sent);
    }

    [Theory]
    [InlineData("wrong", 42, "sess1", 42)]
    [InlineData("n0nce", 42, "other", 42)]
    [InlineData("n0nce", 41, "sess1", 42)]   // the message claims another pid than the one connected
    [InlineData("n0nce", 42, "sess1", 99)]
    [InlineData("", 42, "sess1", 42)]
    public void AnyMismatchStaysClosed(string nonce, int pid, string session, int peer)
    {
        var g = Gate();
        Assert.False(g.Verify(new Hello(nonce, pid, session), peer));
        Assert.False(g.TrySend(() => { }));
    }

    [Fact]
    public void AnExpiredNonceIsRefused()
    {
        var g = Gate();
        _clock.Now += TimeSpan.FromSeconds(11);
        Assert.False(g.Verify(new Hello("n0nce", 42, "sess1"), 42));
    }

    [Fact]
    public void AReplayedHelloIsRefusedAfterSuccess()
    {
        var g = Gate();
        Assert.True(g.Verify(new Hello("n0nce", 42, "sess1"), 42));
        Assert.False(g.Verify(new Hello("n0nce", 42, "sess1"), 42));
        Assert.True(g.Verified); // the first, valid hello still stands
    }
}
