import { describe, expect, it } from 'vitest';
import type { Op, Shape, Style } from '../src/draw/canvas';
import { graphFrame, graphState, selectSource, settleSource } from '../src/modules/graph';
import { bytes, mbps, nextSource, normalise, rate, resolveSource, SOURCES } from '../src/modules/sources';

// Fake readings only. Expected values are worked out from graph.lua and sources.lua. Zone 100 x 40.
const st: Style = {
  s: 1, tier: 2, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
  white: [215, 240, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
};
const zone = { x: 0, y: 0, w: 100, h: 40 };
const GIB = 1073741824;

type TextShape = Extract<Shape, { kind: 'text' }>;
const texts = (ops: Op[]): TextShape[] => ops.map((o) => o.shape).filter((s): s is TextShape => s.kind === 'text');

describe('graph labels and readout (graph.lua)', () => {
  it('the label is one line, the source name as sources.lua spells it', () => {
    const f = graphFrame(graphState('cpu'), { mCPU: 10 }, zone, st, 'fixed');
    expect(texts(f.ops)[0].text).toBe('CPU LOAD');
    expect(texts(graphFrame(graphState('disk'), {}, zone, st, 'fixed').ops)[0].text).toBe(SOURCES.disk.label);
  });

  it('readout is the source text split into a large number and a small unit, and the value is the last number', () => {
    const f = graphFrame(graphState('cpu'), { mCPU: 42.4 }, zone, st, 'fixed');
    const [, num, unit] = texts(f.ops);
    expect([num.text, unit.text]).toEqual(['42', '%']);
    expect(num.size).toBeGreaterThan(unit.size * 2);
    expect(f.value).toBe(42.4);
  });

  it('a missing sensor shows -- and adds no history point', () => {
    const state = graphState('cputemp');
    const f = graphFrame(state, {}, zone, st, 'fixed');
    expect(texts(f.ops).at(-1)?.text).toBe('--');
    expect(f.value).toBe(0);
    expect(state.hist).toEqual([]);
  });

  it('select mode adds the two chevrons', () => {
    const fixed = graphFrame(graphState('cpu'), { mCPU: 1 }, zone, st, 'fixed');
    const sel = graphFrame(graphState('cpu'), { mCPU: 1 }, zone, st, 'select');
    expect(sel.ops.length).toBe(fixed.ops.length + 2);
  });
});

describe('graph history', () => {
  it('keeps the last 48 readings, dropping the oldest first', () => {
    const state = graphState('cpu');
    for (let i = 1; i <= 60; i++) graphFrame(state, { mCPU: i }, zone, st, 'fixed');
    expect(state.hist.length).toBe(48);
    expect(state.hist[0]).toBe(13);
    expect(state.hist[47]).toBe(60);
  });

  it('changing the source empties the history and steps the source', () => {
    const state = graphState('cpu');
    graphFrame(state, { mCPU: 5 }, zone, st, 'fixed');
    const next = selectSource(state, 1);
    expect(next).toEqual({ src: 'ram', hist: [] });
  });

  it('an unknown source falls back to cpu', () => {
    expect(graphState('nope').src).toBe('cpu');
  });
});

describe('sources (sources.lua)', () => {
  it('fixed-scale sources map a value onto 0..1 and clamp it', () => {
    expect(normalise(SOURCES.cpu, [50, 150, -5])).toEqual([0.5, 1, 0]);
    expect(normalise(SOURCES.cputemp, [65])).toEqual([0.5]); // 30..100 C
  });

  it('auto-scaled sources divide by 110% of the peak, which starts at 1', () => {
    const out = normalise(SOURCES.disk, [100, 200]);
    expect(out[0]).toBeCloseTo(100 / 220);
    expect(out[1]).toBeCloseTo(200 / 220);
    expect(normalise(SOURCES.disk, [0])).toEqual([0]);
  });

  it('ram text is used GB and the value is a percent of total', () => {
    const r = SOURCES.ram.get({ mRamUsed: 8 * GIB, mRamTotal: 16 * GIB });
    expect(r.value).toBe(50);
    expect(r.text).toBe('8.0 / 16 GB');
  });

  it('power needs a CPU or GPU reading, and sums whichever are there', () => {
    expect(SOURCES.power.get({}).value).toBeUndefined();
    expect(SOURCES.power.get({ mHwGpuPower: 30 })).toEqual({ value: 30, text: '30 W' });
  });

  it('next steps the order in both directions, wraps, and gives cpu for an unknown id', () => {
    expect(nextSource('cpu', 1)).toBe('ram');
    expect(nextSource('cpu', -1)).toBe('battery');
    expect(nextSource('battery', 1)).toBe('cpu');
    expect(nextSource('cpu', 3)).toBe('vram');
    expect(nextSource('cpu', -12)).toBe('battery'); // a big step back still wraps
    expect(nextSource('nope', 1)).toBe('cpu');
  });
});

describe('byte and bit-rate text (lib.lua)', () => {
  it('bytes: whole bytes, one decimal in KB, whole numbers from 100 up', () => {
    expect(bytes(500)).toBe('500 B');
    expect(bytes(5120)).toBe('5.0 KB');
    expect(bytes(200 * 1024)).toBe('200 KB');
    expect(rate(5120)).toBe('5.0 KB/s');
  });

  it('Mbps: long form, one decimal below 99.5', () => {
    expect(mbps(1250000)).toBe('10.0 Mbps'); // 10 Mbit/s
    expect(mbps(20000000)).toBe('160 Mbps');
  });
});

describe('disk source and hidden VRAM source', () => {
  it('disk source follows mDiskIO', () => {
    expect(SOURCES.disk.get({ mDiskIO: 52000 }).value).toBe(52000);
    expect(SOURCES.disk.get({}).value).toBe(0);
  });
  it('vram is not offered without an mVRAM reading, and is offered with one', () => {
    expect(nextSource('gpu', 1, {})).toBe('cputemp');
    expect(nextSource('cputemp', -1, {})).toBe('gpu');
    expect(nextSource('gpu', 1, { mVRAM: 1e9 })).toBe('vram');
  });
  it('a saved vram resolves to a valid source', () => {
    expect(resolveSource('vram', {}, 'gpu')).toBe('gpu');
    expect(resolveSource('vram', { mVRAM: 1e9 }, 'gpu')).toBe('vram');
    expect(resolveSource('cpu', {}, 'gpu')).toBe('cpu');
    expect(nextSource('vram', 1, {})).toBe('cputemp');
  });
});

describe('a saved vram when metrics arrive after mount', () => {
  it('moves to the slot default when the first readings have no mVRAM, keeps vram when they do', () => {
    const saved = graphState('vram'); // restored at mount, before any metrics
    expect(saved.src).toBe('vram');
    expect(settleSource(saved, { mCPU: 5 }, 'gpu').src).toBe('gpu');
    expect(settleSource(saved, { mVRAM: 1e9 }, 'gpu')).toBe(saved);
    const cpu = graphState('cpu');
    expect(settleSource(cpu, {}, 'gpu')).toBe(cpu);
  });
});
