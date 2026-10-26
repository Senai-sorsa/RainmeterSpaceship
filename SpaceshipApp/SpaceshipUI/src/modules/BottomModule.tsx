import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { JSX } from 'preact';
import type { Op, Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { scheduler } from '../host/scheduler';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { sysInfo } from '../host/sysInfo';
import { netStatus } from '../host/statusFeed';
import { AUDIO_HITS, audioFrame, audioState, type AudioState } from './audio';
import { HitRect } from './hit';
import { leftRows, panelLeftFrame, panelRightFrame, rightRows } from './panels';
import { type Readings } from './readings';
import { stripLeftFrame, stripRightFrame } from './strip';
import { DialModule } from './DialModule';
import { createDialSetter, DIAL_DEFS, hostDialRunner } from './dialSetter';
import { ActionGate } from '../actions/gate';
import { host, store } from '../settings/instance';
import { visible } from './hidden';
import { SKIN_STATE } from './appsSource';

const dialSetter = createDialSetter(store, new ActionGate(DIAL_DEFS, hostDialRunner(host)));

// DialSel is skin state (State.inc), not a setting: the imported defaults carry it, the store does not
const DIAL_SEL = Number(SKIN_STATE.DialSel ?? 1);
const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the bottom dash, read once. Each is drawn in its own skewed matrix. */
const ZONES = {
  storage: zoneOf('B_storage'), audio: zoneOf('B_audio'), panelL: zoneOf('B_panelL'), panelR: zoneOf('B_panelR'),
  stripL: zoneOf('B_stripL'), stripR: zoneOf('B_stripR'),
};

/** Bottom dash: the systems dial (B_storage), audio dial, the two panels and the two strips. Behind ?module=bottom. */
/** hide (the Off_ settings) leaves those zones empty; for Off_BottomAudio the host also stops its capture. */
export function BottomModule({ style, hide = '' }: { style: Style; hide?: string }) {
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const ping = netStatus.value.ping;
  // the strip's ping comes from net.update, not system.metrics; a lost ping (0) shows --
  const r: Readings = useMemo(() => ({ ...(m ? readingsFrom(m) : {}), ...(ping ? { mPing: ping } : {}) }), [m, ping]);
  const vol = m?.volume == null ? undefined : m.volumeMuted ? -1 : m.volume;
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
    au: style.tier >= 3 ? undefined : Z.audio && audioFrame(audio.current, r, Z.audio, style, Math.floor(Date.now() / 50), vol, m?.audioDevice ?? undefined),
  }), [r, Z, style]);
  // the panels read the clock, so they redraw every second
  const panels = useMemo(() => ({
    pl: Z.panelL && panelLeftFrame(leftRows(now, r, info, style.hi), Z.panelL, style),
    pr: Z.panelR && panelRightFrame(rightRows(r, style, info), Z.panelR, style),
  }), [r, now, Z, info, style]);
  const place = (zone: typeof ZONES.storage, list: Op[] | undefined, name: string, mod: string, hit?: JSX.Element | false | null) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
        {hit}
      </g>
    );
  const open = (what: string) => () => host.send({ type: 'target.open', what });
  // audio.lua OnScroll: ChangeVolume -2 per notch down; through the dial's gate, like the VOL control
  const volStep = (d: number) => { const v = vol === undefined ? undefined : Math.max(0, Math.min(100, (vol < 0 ? 0 : vol) - 2 * d)); if (v !== undefined) void dialSetter.set('vol', v / 100); };
  const audioHits = Z.audio && (() => {
    const z = Z.audio, s = style.s, menu = open('sound');
    return (
      <>
        <HitRect zone={z} s={s} box={AUDIO_HITS.disc} label="Volume" on={{ menu, wheel: volStep }} />
        <HitRect zone={z} s={s} box={AUDIO_HITS.core} label="Mute" on={{ click: open('mute'), menu, wheel: volStep }} />
        {/* shortcut: ToggleNext (next output device) needs an undocumented Windows interface; the click opens sound settings instead */}
        <HitRect zone={z} s={s} box={AUDIO_HITS.readout} label="Sound output" on={{ click: menu, menu, wheel: volStep }} />
        {(['prev', 'playpause', 'next'] as const).map((k, i) => (
          <HitRect zone={z} s={s} box={AUDIO_HITS.keys[i]} label={k} on={{ click: open(k), menu, wheel: volStep }} />
        ))}
      </>
    );
  })();
  return (
    <>
      {Z.storage && <DialModule zone={Z.storage} style={style} setter={dialSetter} sel0={DIAL_SEL} />}
      {place(Z.audio, ops.au, 'au', 'audio', audioHits)}
      {/* the skin's OnClick handlers (panels.lua, strip.lua), as fixed host targets */}
      {place(Z.panelL, panels.pl, 'pl', 'panel-left', Z.panelL && <HitRect zone={Z.panelL} s={style.s} label="Calendar" on={{ click: open('outlookcal') }} />)}
      {place(Z.panelR, panels.pr, 'pr', 'panel-right', Z.panelR && (
        <>
          <HitRect zone={Z.panelR} s={style.s} box={{ x: 0, y: 0, w: Z.panelR.w, h: Z.panelR.h * 0.78 }} label="About this PC" on={{ click: open('about') }} />
          <HitRect zone={Z.panelR} s={style.s} box={{ x: 6, y: Z.panelR.h * 0.8, w: Z.panelR.w - 12, h: Z.panelR.h * 0.16 }} label="Terminal" on={{ click: open('terminal'), menu: open('powershell') }} />
        </>
      ))}
      {place(Z.stripL, ops.sl, 'sl', 'strip-left', Z.stripL && <HitRect zone={Z.stripL} s={style.s} label="Task Manager performance" on={{ click: open('taskperf') }} />)}
      {place(Z.stripR, ops.sr, 'sr', 'strip-right', Z.stripR && (
        <>
          <HitRect zone={Z.stripR} s={style.s} label="Task Manager performance" on={{ click: open('taskperf') }} />
          <HitRect zone={Z.stripR} s={style.s} box={{ x: Z.stripR.w - 4 - 76, y: 0, w: 76, h: Z.stripR.h }} label="Drive" on={{ click: open('drive') }} />
        </>
      ))}
    </>
  );
}
