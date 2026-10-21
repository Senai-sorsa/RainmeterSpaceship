import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';

// Port of the 'upkeep' rows of Skins/Spaceship/@Resources/Scripts/status_block.lua: the pending Windows update count
// (diamond) and the Gmail unread count (envelope). Unknown values show as '--', never as zero. No host channel supplies
// these yet, so the caller passes them. The winget count and the antivirus line sit in the Lua hover text, not ported.
// Clicks are not wired (they open Windows Update, Gmail and Windows Security through the action gate later).

export type UpkeepInput = {
  updates?: number; // pending Windows updates, undefined when unknown
  mail?: number; // Gmail unread count
  mailWhy?: string; // why mail is missing (ERR text or 'off'), set when mail is undefined
};

const count = (v: number | undefined) => (v === undefined || v < 0 ? '--' : String(v));

export function upkeepFrame(input: UpkeepInput, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  const { h } = zone;
  const x0 = 4, y1 = h * 0.33, y2 = h * 0.72;
  const mail = input.mail;
  const hasMail = mail !== undefined;
  const mailCol = mail !== undefined && mail > 0 ? st.white : st.accent;
  // pink diamond with the update count
  c.poly([[x0 + 8, y1 - 8], [x0 + 16, y1], [x0 + 8, y1 + 8], [x0, y1]], st.hi, 1.8, 255, true);
  c.dot(x0 + 8, y1, 2.5, st.hi);
  c.text(x0 + 22, y1, count(input.updates), { size: 8, weight: 700, align: 'LeftCenter', color: st.hi });
  // envelope: brighter when there is unread mail
  c.icon('mail', x0 + 8, y2, 18, mailCol, 1.3);
  const mailText = hasMail ? count(mail) : input.mailWhy === 'off' ? '-' : '!';
  const mailColour = hasMail || input.mailWhy === 'off' ? mailCol : st.warn;
  c.text(x0 + 22, y2, mailText, { size: 8, weight: 700, align: 'LeftCenter', color: mailColour });
  return c.flush();
}
