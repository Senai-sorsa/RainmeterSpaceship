import { useEffect, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { transformBox, type Matrix } from '../lib/geometry';
import { feedFrom, jarvisFrame, jarvisLogFrame, type Feed } from './jarvis';

const FRAME_MS = 33; // the Lua orb's 30 fps
const sphere = layout.zones.find((z) => z.id === 'C_sphere');
const offline = feedFrom(undefined, 0);

/**
 * The Jarvis core, behind ?module=jarvis. Centred on the old globe's zone (C_sphere). No feed is wired yet, so it
 * shows OFFLINE until a feed is given. The orb sprite, the voice echo and the clicks are not ported.
 */
export function JarvisModule({ style, feed = offline }: { style: Style; feed?: Feed }) {
  const [f, setF] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setF((n) => n + 1), FRAME_MS);
    return () => clearInterval(t);
  }, []);
  if (!sphere) return null;
  const q = transformBox(sphere.matrix as Matrix, sphere.x, sphere.y, sphere.w, sphere.h);
  const cx = (q[0][0] + q[2][0]) / 2, cy = (q[0][1] + q[2][1]) / 2;
  const ops = jarvisFrame(f, feed, style, { x: 0, y: 0, w: layout.canvas.w, h: layout.canvas.h }, cx, cy);
  return <OpsView ops={ops} name="jarvis" />;
}

/**
 * The conversation log, behind ?module=jarvislog. It reads the log and reply text it is given (the Data files are not
 * wired yet, so it shows the empty state). Placed at the top left of the canvas until a zone is set for it.
 */
export function JarvisLogModule({ style, log = '', live = '', muted = false, assistant = 'Clover' }: {
  style: Style; log?: string; live?: string; muted?: boolean; assistant?: string;
}) {
  const ops = jarvisLogFrame(log, live, muted, assistant, style, { x: 0, y: 0, w: 1200, h: 616 });
  return (
    <g transform="translate(40 40)" data-module="jarvislog">
      <OpsView ops={ops} name="jarvislog" />
    </g>
  );
}
