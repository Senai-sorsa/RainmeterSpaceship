import { useEffect, useState } from 'preact/hooks';
import { Canvas, type Op, type Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import type { RGBA } from '../lib/theme';
import { emptyText, firstLevel, rowTip, rows, type CalState } from './calendar';
import type { CalendarSource } from './calendarSource';
import { scheduler } from '../host/scheduler';

type Zone = { x: number; y: number; w: number; h: number; matrix: number[] };

const TICK_MS = 30000; // the rows change by the minute at most; 30 s keeps NOW and the countdown colours current
// location.lua authors in a 1260x709 reference box offset by (34, 220)
const SXR = 2560 / 1260, SYR = 1600 / 709;
const X = (rx: number) => (rx - 34) * SXR, Y = (ry: number) => (ry - 220) * SYR;
const ROW_Y = [242, 253, 264];

/** Draw ops of location.lua Update: the top rule with its end dots, three when + title rows and the two slanted base rules. */
export function clockFrame(state: CalState, now: number, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st), A1 = st.accent;
  c.line(X(40), Y(228), X(226), Y(228), A1, 1.3, 220);
  c.dot(X(40), Y(228), 3, A1); c.dot(X(226), Y(228), 3, A1);
  const lvl = firstLevel(state, now);
  const col: RGBA = lvl === 'good' ? st.good : lvl === 'alert' ? st.alert : lvl === 'warn' ? st.warn : A1;
  const list = rows(state, now);
  const shown = list.length ? list.map((r, i) => ({ when: r.when, title: r.title, lc: r.live ? st.good : i === 0 ? col : A1, tc: i === 0 ? st.white : ([160, 185, 200, 255] as RGBA) }))
    : [{ ...emptyText(state), lc: A1, tc: st.dim }];
  shown.forEach((r, i) => {
    const y = Y(ROW_Y[i]);
    c.text(X(80), y, r.when, { size: 5.4, weight: 700, align: 'RightCenter', color: r.lc, font: st.fontNum });
    c.text(X(84), y, r.title, { size: 5.4, weight: 700, align: 'LeftCenter', color: r.tc, clip: X(228) - X(84) });
  });
  const ly = (rx: number, base: number) => base - (10 / 196 - 4 / 187) * (rx - 34) * SYR;
  c.line(X(35), ly(35, zone.h - 9), X(222), ly(222, zone.h - 9), A1, 1.3, 220);
  c.line(X(35), ly(35, zone.h - 2.5), X(222), ly(222, zone.h - 2.5), A1, 1, 160);
  return c.flush();
}

/** Mission clock: the next three calendar events inside the L_location zone, drawn in the zone's own skewed frame. */
export function MissionClock({ zone, source, captions, style }: { zone: Zone; source: CalendarSource; captions: boolean; style: Style }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    return scheduler.every(TICK_MS, () => setNow(Date.now()));
  }, []);
  const state = source.read(now);
  const feed = state.errors > 0 ? `${state.errors} calendar feed${state.errors > 1 ? 's' : ''} failed` : undefined;
  const s = style.s, rowH = 11 * SYR * s;
  return (
    <g transform={`matrix(${zone.matrix.join(' ')})`} data-module="clock" data-tip={captions ? feed : undefined}>
      {!captions && feed && <title>{feed}</title>}
      <OpsView ops={clockFrame(state, now, zone, style)} name="clock" />
      {ROW_Y.map((ry, i) => {
        const tip = rowTip(state, now, i);
        // invisible hover box per row, so a cut title shows its full text
        return tip && (
          <rect key={i} data-row={i + 1} data-tip={captions ? tip : undefined} x={zone.x * s} y={(zone.y + Y(ry)) * s - rowH / 2}
            width={zone.w * s} height={rowH} fill="transparent">
            {!captions && <title>{tip}</title>}
          </rect>
        );
      })}
    </g>
  );
}
