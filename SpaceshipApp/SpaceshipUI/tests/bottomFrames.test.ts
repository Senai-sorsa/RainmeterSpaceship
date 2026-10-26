import { describe, expect, it } from 'vitest';
import { audioFrame, audioState } from '../src/modules/audio';
import { leftRows, panelLeftFrame, panelRightFrame, rightRows } from '../src/modules/panels';
import { stripLeftFrame, stripRightFrame } from '../src/modules/strip';
import { storageFrame } from '../src/modules/storage';
import { styleFrom } from '../src/modules/style';
import type { Readings } from '../src/modules/readings';

const st = styleFrom({});
const zone = { x: 0, y: 0, w: 188.95, h: 164.73 };
const full: Readings = {
  mD1Total: 931 * 1073741824, mD1Free: 519 * 1073741824, mD2Total: 0, mRead: 1572864, mWrite: 2048, mHwSsdTemp: 41,
  mCPU: 40, mHwCpuTemp: 60, mHwGpuTemp: 70, mHwFan1: 2100, mDiskIO: 4200, mPing: 12, mWifi: 80, mUptime: 7440,
  mRMS: 0.2, mPeak: 0.4, mBand0: 0.3,
};

describe('bottom frames', () => {
  it('storage draws rows, bars and the used share', () => {
    const f = storageFrame(full, zone, st);
    expect(f.ops.length).toBeGreaterThan(0);
    expect(f.used).toBeCloseTo(412 / 931, 2);
  });

  it('strips draw with and without readings', () => {
    expect(stripLeftFrame(full, zone, st).length).toBeGreaterThan(0);
    expect(stripLeftFrame({}, zone, st).length).toBeGreaterThan(0);
    expect(stripRightFrame(full, zone, st).length).toBeGreaterThan(0);
    expect(stripRightFrame({}, zone, st).length).toBeGreaterThan(0);
  });

  it('panels draw the rows and the terminal button', () => {
    const now = new Date(2026, 9, 21, 12, 30, 5);
    expect(leftRows(now, { mUptime: 7440 }).find((r) => r.label === 'UP')?.value).toBe('2:04 H');
    expect(leftRows(now).find((r) => r.label === 'BOOT')?.value).toBe('--');
    expect(panelLeftFrame(leftRows(now, { mUptime: 7440 }), zone, st).length).toBeGreaterThan(0);
    expect(panelRightFrame(rightRows({ mUptime: 7440 }, st), zone, st).length).toBeGreaterThan(0);
  });

  it('panels show the host names, idle, RAM total and screen like panels.lua', () => {
    const info = { user: 'senai', host: 'ship-1', cpu: 'RYZEN AI 9 465', gpu: 'RTX 5070', display: '2560x1600 @240' };
    const left = Object.fromEntries(leftRows(new Date(), { mIdle: 125 }, info).map((r) => [r.label, r.value]));
    expect([left.PILOT, left.IDLE]).toEqual(['SENAI', '2:05']);
    const right = Object.fromEntries(rightRows({ mRamTotal: 32 * 1073741824 }, st, info).map((r) => [r.label, r.value]));
    expect(right).toMatchObject({ HOST: 'SHIP-1', OS: 'WINDOWS', CPU: 'RYZEN AI 9 465', GPU: 'RTX 5070', RAM: '32 GB', DISP: '2560x1600 @240' });
    expect(Object.fromEntries(rightRows({}, st).map((r) => [r.label, r.value]))).toMatchObject({ HOST: '--', RAM: '--', DISP: '--' });
  });

  it('audio draws the ring and steps the followers once per call', () => {
    const s = audioState();
    const ops = audioFrame(s, full, zone, st, 0);
    expect(ops.length).toBeGreaterThan(0);
    expect(s.sm[0]).toBeCloseTo(0.15);
    audioFrame(s, {}, zone, st, 1, 50, 'Speakers (Realtek)');
    expect(s.sm[0]).toBeCloseTo(0.075);
  });
});
