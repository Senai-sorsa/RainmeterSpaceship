import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { WebView2Host, type WebViewApi } from '../src/host/HostBridge';
import { acceptSystemMetrics, readingsFrom, systemMetrics, systemMetricsFrom } from '../src/host/systemMetrics';

const FIXTURES = new URL('../../../contract/fixtures/host-to-ui.json', import.meta.url);

/** Fake window.chrome.webview that lets the test push host messages. */
function fakeWebView() {
  const listeners = new Set<(e: { data: unknown }) => void>();
  const api: WebViewApi = {
    postMessage: () => {},
    addEventListener: (_, cb) => listeners.add(cb),
    removeEventListener: (_, cb) => listeners.delete(cb),
  };
  return { api, fromHost: (data: unknown) => { for (const cb of [...listeners]) cb({ data }); } };
}

describe('host-to-ui fixtures', () => {
  it('every case gets the verdict it declares', () => {
    const fx = JSON.parse(readFileSync(FIXTURES, 'utf8')) as { name: string; valid: boolean; msg: unknown }[];
    expect(fx.length).toBeGreaterThan(5);
    for (const c of fx) expect(systemMetricsFrom(c.msg) !== null, c.name).toBe(c.valid);
  });
});

describe('system metrics signal', () => {
  it('takes a valid reading from the host and keeps the last one', () => {
    const wv = fakeWebView();
    new WebView2Host(wv.api).onMessage(acceptSystemMetrics);
    wv.fromHost('{"type":"system.metrics","seq":1,"cpuPercent":null,"memoryPercent":40,"uptimeMs":0,"onAc":null,"batteryPercent":null,"netDown":null,"netUp":null,"spectrum":null,"processes":{},"hw":{}}');
    wv.fromHost('{"type":"system.metrics","seq":2,"cpuPercent":12.5,"memoryPercent":41,"uptimeMs":10,"onAc":true,"batteryPercent":null,"netDown":1000,"netUp":50,"spectrum":[0.2],"processes":{"Spotify":true},"hw":{"HW_CpuTemp":50}}');
    expect(systemMetrics.value?.seq).toBe(2);
    expect(systemMetrics.value?.hw).toEqual({ HW_CpuTemp: 50 });
  });

  it('ignores an invalid message and keeps the previous reading', () => {
    const wv = fakeWebView();
    new WebView2Host(wv.api).onMessage(acceptSystemMetrics);
    wv.fromHost('{"type":"system.metrics","seq":3,"cpuPercent":"37","memoryPercent":1,"uptimeMs":1,"onAc":null,"batteryPercent":null,"netDown":null,"netUp":null,"spectrum":null,"processes":{},"hw":{}}');
    expect(systemMetrics.value?.seq).toBe(2);
  });

  it('maps the reading to the skin measures, leaving out what is unavailable', () => {
    const m = systemMetricsFrom(JSON.parse('{"type":"system.metrics","seq":4,"cpuPercent":12.5,"memoryPercent":41,"uptimeMs":10,"onAc":true,"batteryPercent":null,"netDown":1000,"netUp":null,"spectrum":null,"processes":{},"hw":{}}'));
    expect(m && readingsFrom(m)).toEqual({ mCPU: 12.5, netDown: 1000 });
  });
});
