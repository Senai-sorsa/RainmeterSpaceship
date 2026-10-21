import { useEffect, useState } from 'preact/hooks';
import { emptyText, firstLevel, rowTip, rows } from './calendar';
import type { CalendarSource } from './calendarSource';
import { scheduler } from '../host/scheduler';

type Zone = { x: number; y: number; w: number; h: number; matrix: number[] };

const LEVEL = { good: 'var(--good)', alert: 'var(--alert)', warn: 'var(--warn)', accent: 'var(--accent)' } as const;
const TICK_MS = 30000; // the rows change by the minute at most; 30 s keeps NOW and the countdown colours current

/** Mission clock: the next three calendar events inside the L_location zone. Drawn in the zone's own skewed frame. */
export function MissionClock({ zone, source, captions }: { zone: Zone; source: CalendarSource; captions: boolean }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    return scheduler.every(TICK_MS, () => setNow(Date.now()));
  }, []);
  const state = source.read(now);
  const { x, y, w, h } = zone;
  const lvl = LEVEL[firstLevel(state, now)];
  const list = rows(state, now);
  const shown = list.length ? list : [{ ...emptyText(state), live: false, allday: false }];
  const feed = state.errors > 0 ? `${state.errors} calendar feed${state.errors > 1 ? 's' : ''} failed` : undefined;
  return (
    <g transform={`matrix(${zone.matrix.join(' ')})`} data-module="clock" data-tip={captions ? feed : undefined}>
      {!captions && feed && <title>{feed}</title>}
      {shown.map((r, i) => {
        const yy = y + h * (0.3 + i * 0.25);
        const label = list.length ? (r.live && !r.allday ? 'NOW' : r.when) : emptyText(state).when;
        const colour = i === 0 ? lvl : 'var(--accent)';
        const tip = list.length ? rowTip(state, now, i) : undefined;
        const tipAttr = captions ? tip : undefined;
        return (
          <g key={i} data-row={i + 1} data-tip={tipAttr}>
            {!captions && tip && <title>{tip}</title>}
            <text x={x + w * 0.2} y={yy} text-anchor="end" dominant-baseline="middle" font-size="13" font-weight="700" style={{ fill: colour }}>{label}</text>
            <text x={x + w * 0.23} y={yy} dominant-baseline="middle" font-size="13" font-weight="700" style={{ fill: i === 0 ? 'var(--white)' : 'var(--text)' }}>{r.title}</text>
          </g>
        );
      })}
    </g>
  );
}
