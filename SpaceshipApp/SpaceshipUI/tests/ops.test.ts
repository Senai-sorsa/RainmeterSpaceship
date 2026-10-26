import { describe, expect, it } from 'vitest';
import type { Op } from '../src/draw/canvas';
import { OpsView, pathD, textAlign } from '../src/draw/ops';
import { styleFrom } from '../src/modules/style';
import { clockFrame } from '../src/modules/MissionClock';

describe('ops to svg', () => {
  it('closes a polygon only when asked', () => {
    expect(pathD([[0, 0], [10, 5]], false)).toBe('M0 0L10 5');
    expect(pathD([[0, 0], [10, 5], [0, 5]], true)).toBe('M0 0L10 5L0 5Z');
  });

  it('maps Lua alignment names to SVG anchors', () => {
    expect(textAlign('LeftTop')).toEqual({ anchor: 'start', base: 'text-before-edge' });
    expect(textAlign('RightCenter')).toEqual({ anchor: 'end', base: 'central' });
    expect(textAlign('CenterBottom')).toEqual({ anchor: 'middle', base: 'text-after-edge' });
  });

  it('draws one element per op, in order', () => {
    const ops: Op[] = [
      { shape: { kind: 'rect', x: 0, y: 0, w: 4, h: 4, r: 0 }, fill: [1, 2, 3, 255] },
      { shape: { kind: 'poly', pts: [[0, 0], [1, 1]], closed: false } },
    ];
    const el = OpsView({ ops, name: 't' });
    expect(el.props.children.map((c: { props: { op: Op } }) => c.props.op.shape.kind)).toEqual(['rect', 'poly']);
  });
});

describe('text as Rainmeter draws it', () => {
  it('draws FontSize points as 4/3 px and the glow copy as a blur only', () => {
    const op: Op = { shape: { kind: 'text', x: 0, y: 0, text: 'A', size: 12, align: 'LeftTop', weight: 700, font: 'Oxanium', blur: 4 }, fill: [1, 2, 3, 255] };
    const g = OpsView({ ops: [op], name: 't' }).props.children[0];
    const el = g.type(g.props);
    expect(el.props['font-size']).toBe(16);
    expect(el.props.style.filter).toBe('blur(4px)'); // the halo alone; drop-shadow would paint the letters a second time
  });

  it('the mission clock draws the empty state in the number font, like location.lua', () => {
    const st = styleFrom({});
    const ops = clockFrame({ ok: false, calendars: 0, errors: 0, events: [] }, 0, { x: 0, y: 0, w: 400, h: 100, matrix: [1, 0, 0, 1, 0, 0] }, st);
    const texts = ops.flatMap((o) => (o.shape.kind === 'text' && !o.shape.blur ? [[o.shape.text, o.shape.font]] : []));
    expect(texts).toEqual([['SETUP', 'B612 Mono'], ['CONTROL CENTER > DATA', 'Oxanium']]);
  });
});

describe('style from settings', () => {
  it('uses the lib.lua defaults when the settings are empty', () => {
    const s = styleFrom({});
    expect(s).toMatchObject({ s: 1, tier: 0, glowA: 46, glowW: 3.2, coreWhite: 0.3, hudA: 255, edit: false, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma' });
    expect(s.accent).toEqual([0, 210, 255, 255]);
    expect(s.panel).toEqual([0, 30, 45, 90]);
  });

  it('reads the settings values over the defaults', () => {
    const s = styleFrom({ Scale: '1.5', EditMode: '1', ColorAccent: '255,0,0' });
    expect(s.s).toBe(1.5);
    expect(s.edit).toBe(true);
    expect(s.accent).toEqual([255, 0, 0, 255]);
  });
});
