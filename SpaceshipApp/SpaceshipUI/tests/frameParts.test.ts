import { describe, expect, it } from 'vitest';
import { cssColor, evalExpr, partShapes } from '../src/ui/frameParts';

describe('frame parts', () => {
  it('evaluates the formulas the parts use', () => {
    expect(evalExpr('(76*0.38)')).toBeCloseTo(28.88);
    expect(evalExpr('(235*0.3*0.8)')).toBeCloseTo(56.4);
    expect(evalExpr('(Min(255,400*0.75))')).toBe(255);
    expect(evalExpr('(Clamp(0+(1),0,1))')).toBe(1);
    expect(evalExpr('2+3*4-1')).toBe(13);
    expect(evalExpr('#Missing#*2')).toBeNaN();
    expect(evalExpr('alert(1)')).toBeNaN();
  });

  it('reads colours with formula alphas, and clear ones as none', () => {
    expect(cssColor('0,210,255,(Min(255,66*0.75))')).toBe('rgb(0 210 255 / 0.1941)');
    expect(cssColor('0,0,0,0')).toBe('none');
    expect(cssColor('10,20,30')).toBe('rgb(10 20 30 / 1)');
  });

  it('turns shapes, paths and gradients into SVG data with the skin variables', () => {
    const sec = {
      P1: '0,0 | LineTo 10,0 | LineTo 10,10 | ClosePath 1',
      G1: '90 | 45,115,205,80 ; 0.00 | 30,85,170,55 ; 1.00',
      Shape: 'Ellipse 1280.0,1326.9,170.0,33.0 | Fill Color 0,0,0,230 | Stroke Color #ColorAccent#,120 | StrokeWidth 2',
      Shape2: 'Path P1 | Fill Color 0,0,0,0 | Stroke Color #ColorAccent#,(#GlowAlpha#*0.5) | StrokeWidth (#GlowWidth#*2) | StrokeLineJoin Round',
      Shape3: 'Path P1 | Fill LinearGradient G1 | StrokeWidth 0',
      Shape10: 'Rectangle 1209.0,832.5,10.0,14.0 | Fill Color #ColorAccent#,170 | StrokeWidth 0',
      Shape4: 'Rectangle 0,0,0,0 | Fill Color 0,0,0,0 | StrokeWidth 0',
    };
    const s = partShapes(sec, { ColorAccent: '0,210,255', GlowAlpha: '76', GlowWidth: '3' });
    expect(s.map((x) => x.kind)).toEqual(['ellipse', 'path', 'path', 'rect']); // Shape10 after Shape3, the empty rectangle dropped
    expect(s[0]).toMatchObject({ geo: { cx: 1280, cy: 1326.9, rx: 170, ry: 33 }, stroke: 'rgb(0 210 255 / 0.4706)', width: 2, join: 'miter' });
    expect(s[1]).toMatchObject({ geo: { d: 'M0 0L10 0L10 10Z' }, fill: 'none', width: 6, join: 'round' });
    expect(s[2].fill).toMatchObject({ x1: 0.5, y1: 0, x2: 0.5, y2: 1, stops: [{ off: 0 }, { off: 1 }] });
    expect(s[2].stroke).toBe('none');
  });
});
