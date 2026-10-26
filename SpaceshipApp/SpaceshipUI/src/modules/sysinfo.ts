import { Canvas, mix, type Op, type Style, type Zone } from '../draw/canvas';

// Port of Skins/Spaceship/@Resources/Scripts/sysinfo.lua: the network block (PING, LAN, WAN, live down and up in Mbps)
// with the Wi-Fi emblem. PING, LAN and WAN come from the host's net.update
// (host/statusFeed.ts netRows, which applies the IP mask) and show -- until the first reading. The speed-test box shows --
// (its test is an action, not ported). Clicks and the speed test are not wired.
// shortcut: text widths are estimated from the character count, not measured, so right-aligned clips may differ slightly.

const SXR = 2560 / 1260, SYR = 1600 / 709; // the skin's design-to-zone scale (sysinfo.lua)

export type SysInput = { ping?: number; wifi?: number; down?: number; up?: number; lan?: string; wan?: string; link?: number };

const mbps = (bps: number) => {
  const v = (bps * 8) / 1000000;
  return v >= 99.5 ? v.toFixed(0) : v.toFixed(1);
};

export function sysinfoFrame(input: SysInput, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  const { w, h } = zone;
  const X = (rx: number) => w - (rx - 34) * SXR;
  const Y = (ry: number) => (ry - 220) * SYR;
  const A1 = st.accent, W = st.white, D = st.dim;
  c.line(X(40), Y(228), X(226), Y(228), A1, 1.3, 220);
  c.dot(X(40), Y(228), 3, A1); c.dot(X(226), Y(228), 3, A1);
  // emblem: ring with three Wi-Fi arcs, lit up to the level, and the speed-test box
  const gx = X(100), gy = Y(256);
  const wifi = input.wifi ?? 0;
  c.circle(gx, gy, 40, W, 1, 90);
  for (let i = 1; i <= 3; i++) {
    const lit = wifi >= i * 30;
    c.arc(gx, gy + 12, 9 + i * 8, 225, 315, lit ? W : D, 1.6, lit ? 255 : 120);
  }
  c.dot(gx, gy + 12, 2.6, W);
  c.rect(gx + 30, gy + 12, 40, 22, A1, 1.5);
  // the box shows the saved line speed (LinkDownMbps) or TEST; the speed test itself is not ported
  c.text(gx + 50, gy + 23, input.link ? String(Math.round(input.link)) : 'TEST', { size: 6.4, weight: 700, align: 'CenterCenter', color: A1, font: st.fontNum });
  // rows: label on the inner side, value on the outer side
  const pingTxt = input.ping === undefined ? '--' : input.ping <= 0 || input.ping >= 2999 ? 'LOST' : `${input.ping} MS`;
  const pcol = input.ping === undefined ? D : pingTxt === 'LOST' ? st.alert : input.ping! >= 150 ? st.warn : W;
  const rows: [string, string, typeof W][] = [
    ['PING', pingTxt, pcol],
    ['LAN', input.lan ?? '--', input.lan ? W : D],
    ['WAN', input.wan ?? '--', input.wan ? W : D],
  ];
  const ys = [243.5, 252.5, 261.5, 270.5];
  rows.forEach(([label, value, col], i) => {
    const y = Y(ys[i]);
    c.text(X(151), y, label, { size: 6.2, weight: 700, align: 'LeftCenter', color: col });
    c.text(X(157), y, value, { size: 5.6, weight: 700, align: 'RightCenter', color: col, font: st.fontNum, clip: X(157) - X(224) });
  });
  // MBPS row: up and down with arrows
  const y = Y(ys[3]);
  c.text(X(151), y, 'MBPS', { size: 6.2, weight: 700, align: 'LeftCenter', color: mix(A1, W, 0.3) });
  const up = input.up === undefined ? '--' : mbps(input.up);
  const down = input.down === undefined ? '--' : mbps(input.down);
  const xu = X(157);
  c.text(xu, y, up, { size: 5.6, weight: 700, align: 'RightCenter', color: W, font: st.fontNum });
  const xa = xu - up.length * 5.6 * 0.62 - 5;
  c.fillPoly([[xa - 3.5, y + 2.5], [xa + 3.5, y + 2.5], [xa, y - 3.5]], A1, 235);
  const xd = xa - 9;
  c.text(xd, y, down, { size: 5.6, weight: 700, align: 'RightCenter', color: W, font: st.fontNum });
  const xb = xd - down.length * 5.6 * 0.62 - 5;
  c.fillPoly([[xb - 3.5, y - 2.5], [xb + 3.5, y - 2.5], [xb, y + 3.5]], A1, 235);
  // two rails along the bottom
  const ly = (rx: number, base: number) => base - (10 / 196 - 4 / 187) * (rx - 34) * SYR;
  c.line(X(35), ly(35, h - 9), X(222), ly(222, h - 9), A1, 1.3, 220);
  c.line(X(35), ly(35, h - 2.5), X(222), ly(222, h - 2.5), A1, 1, 160);
  return c.flush();
}
