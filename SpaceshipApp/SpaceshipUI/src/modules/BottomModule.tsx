import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Op, Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { scheduler } from '../host/scheduler';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { sysInfo } from '../host/sysInfo';
import { audioFrame, audioState, type AudioState } from './audio';
import { leftRows, panelLeftFrame, panelRightFrame, rightRows } from './panels';
import { type Readings } from './readings';
import { stripLeftFrame, stripRightFrame } from './strip';
import { DialModule } from './DialModule';
import { createDialSetter, DIAL_DEFS, hostDialRunner } from './dialSetter';
import { ActionGate } from '../actions/gate';
import { host, store } from '../settings/instance';
import { visible } from './hidden';

const dialSetter = createDialSetter(store, new ActionGate(DIAL_DEFS, hostDialRunner(host)));

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the bottom dash, read once. Each is drawn in its own skewed matrix. */
const ZONES = {
  storage: zoneOf('B_storage'), audio: zoneOf('B_audio'), panelL: zoneOf('B_panelL'), panelR: zoneOf('B_panelR'),
  stripL: zoneOf('B_stripL'), stripR: zoneOf('B_stripR'),
};

/** Bottom dash: the systems dial (B_storage), audio dial, the two panels and the two strips. Behind ?module=bottom. The audio dial's clicks are not wired yet. */
/** hide (the Off_ settings) leaves those zones empty; for Off_BottomAudio the host also stops its capture. */
export function BottomModule({ style, hide = '' }: { style: Style; hide?: string }) {
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const r: Readings = useMemo(() => (m ? readingsFrom(m) : {}), [m]);
  const info = sysInfo.value;
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    return scheduler.every(1000, () => setNow(new Date()));
  }, []);
  // the audio followers step once per host reading, so they live outside the render and are not in the deps of the other frames
  const audio = useRef<AudioState>(audioState());
  // style is in the deps: the first render can come before the saved Scale arrives, and a quiet host would keep that size
  const ops = useMemo(() => ({
    sl: Z.stripL && stripLeftFrame(r, Z.stripL, style),
    sr: Z.stripR && stripRightFrame(r, Z.stripR, style),
    au: style.tier >= 3 ? undefined : Z.audio && audioFrame(audio.current, r, Z.audio, style, Math.floor(Date.now() / 50)),
  }), [r, Z, style]);
  // the panels read the clock, so they redraw every second
  const panels = useMemo(() => ({
    pl: Z.panelL && panelLeftFrame(leftRows(now, r, info), Z.panelL, style),
    pr: Z.panelR && panelRightFrame(rightRows(r, style, info), Z.panelR, style),
  }), [r, now, Z, info]);
  const place = (zone: typeof ZONES.storage, list: Op[] | undefined, name: string, mod: string) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
      </g>
    );
  return (
    <>
      {Z.storage && <DialModule zone={Z.storage} style={style} setter={dialSetter} />}
      {place(Z.audio, ops.au, 'au', 'audio')}
      {place(Z.panelL, panels.pl, 'pl', 'panel-left')}
      {place(Z.panelR, panels.pr, 'pr', 'panel-right')}
      {place(Z.stripL, ops.sl, 'sl', 'strip-left')}
      {place(Z.stripR, ops.sr, 'sr', 'strip-right')}
    </>
  );
}
