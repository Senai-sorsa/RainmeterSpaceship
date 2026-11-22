namespace ShipCore.Core.Tests;

public sealed class RunnerLifetimeTests
{
    [Fact]
    public void PostCallsThroughBeforeDisposeAndNotAfter()
    {
        var sent = new List<string>();
        var life = new RunnerLifetime();
        Assert.True(life.Post(sent.Add, "a"));
        life.Dispose();
        Assert.False(life.Post(sent.Add, "b"));
        Assert.Equal(["a"], sent);
    }

    [Fact]
    public void DisposeTwiceDoesNotThrow()
    {
        var life = new RunnerLifetime();
        life.Dispose();
        life.Dispose();
        Assert.True(life.Disposed);
    }

    [Fact]
    public void DisposeCancelsTheToken()
    {
        var life = new RunnerLifetime();
        var token = life.Token;
        Assert.False(token.IsCancellationRequested);
        Assert.False(life.Disposed);
        life.Dispose();
        Assert.True(token.IsCancellationRequested);
        Assert.True(life.Token.IsCancellationRequested); // still readable after Dispose
    }

    [Fact]
    public void PostSwallowsAnObjectDisposedExceptionFromTheCallback()
    {
        var life = new RunnerLifetime();
        Assert.False(life.Post(_ => throw new ObjectDisposedException("webview"), "a"));
    }

    [Fact]
    public void PostLetsOtherExceptionsThrough()
    {
        var life = new RunnerLifetime();
        Assert.Throws<InvalidOperationException>(() => life.Post(_ => throw new InvalidOperationException(), "a"));
    }
}
