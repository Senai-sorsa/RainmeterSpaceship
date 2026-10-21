import { describe, expect, it } from 'vitest';
import { WebView2Host, type WebViewApi } from '../src/host/HostBridge';

/** Fake window.chrome.webview: records what the page posts and lets the test push host replies. */
function fakeWebView() {
  const posted: string[] = [];
  const listeners = new Set<(e: { data: unknown }) => void>();
  const api: WebViewApi = {
    postMessage: (t) => posted.push(t),
    addEventListener: (_, cb) => listeners.add(cb),
    removeEventListener: (_, cb) => listeners.delete(cb),
  };
  const fromHost = (data: unknown) => { for (const cb of [...listeners]) cb({ data }); };
  return { api, posted, fromHost, count: () => listeners.size };
}

describe('WebView2Host', () => {
  it('posts each message as one JSON string, the form the host reads', () => {
    const wv = fakeWebView();
    new WebView2Host(wv.api).send({ type: 'config.set', key: 'Scale', value: '0.8', id: 1 });
    expect(wv.posted).toEqual(['{"type":"config.set","key":"Scale","value":"0.8","id":1}']);
  });

  it('delivers host replies as messages, whether sent as text or as objects', () => {
    const wv = fakeWebView();
    const got: string[] = [];
    new WebView2Host(wv.api).onMessage((m) => got.push(m.type));
    wv.fromHost('{"type":"setup.state","done":false}');
    wv.fromHost({ type: 'aboutme.value', text: 'hi' });
    expect(got).toEqual(['setup.state', 'aboutme.value']);
  });

  it('drops text that is not JSON or not an object with a type', () => {
    const wv = fakeWebView();
    const got: unknown[] = [];
    new WebView2Host(wv.api).onMessage((m) => got.push(m));
    wv.fromHost('{x');
    wv.fromHost('[1,2]');
    wv.fromHost('{"done":true}');
    expect(got).toEqual([]);
  });

  it('the returned function removes the listener', () => {
    const wv = fakeWebView();
    const off = new WebView2Host(wv.api).onMessage(() => {});
    expect(wv.count()).toBe(1);
    off();
    expect(wv.count()).toBe(0);
  });

  it('telemetry is silent zeros, not made-up motion', () => {
    const t = new WebView2Host(fakeWebView().api).telemetry();
    expect(t.length).toBe(8);
    expect(Array.from(t).every((v) => v === 0)).toBe(true);
  });
});
