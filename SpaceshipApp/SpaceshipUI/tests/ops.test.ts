import { describe, expect, it } from 'vitest';
import type { Op } from '../src/draw/canvas';
import { OpsView, pathD, textAlign } from '../src/draw/ops';
import { styleFrom } from '../src/modules/style';

describe('ops to svg', () => {
  it('closes a polygon only when asked', () => {
    expect(pathD([[0, 0], [10, 5]], false)).toBe('M0 0L10 5');
    expect(pathD([[0, 0], [10, 5], [0, 5]], true)).toBe('M0 0L10 5L0 5Z');
  });

  it('maps Lua alignment names to SVG anchors', () => {
    expect(textAlign('LeftTop')).toEqual({ anchor: 'start', base: 'hanging' });
    expect(textAlign('RightCenter')).toEqual({ anchor: 'end', base: 'middle' });
    expect(textAlign('CenterBottom')).toEqual({ anchor: 'middle', base: 'alphabetic' });
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

describe('style from settings', () => {
  it('uses the lib.lua defaults when the settings are empty', () => {
    const s = styleFrom({});
    expect(s).toMatchObject({ s: 1, tier: 0, glowA: 46, glowW: 3.2, coreWhite: 0.3, hudA: 255, edit: false, fontText: 'Oxanium' });
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
