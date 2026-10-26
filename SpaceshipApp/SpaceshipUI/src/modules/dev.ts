import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { count } from './upkeep';

// Port of the 'dev' block of Skins/Spaceship/@Resources/Scripts/status_block.lua (Kind=dev, mirrored on the right): the
// running WSL distro count (diamond) and the loaded Ollama model count (gear). The Tailscale state is in the Lua hover text
// and is not ported. The host runs Scripts\dev.ps1 (host/statusFeed.ts); until then both show --.

export type DevInput = { wsl?: number; llm?: number };

export function devFrame(input: DevInput, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  const x0 = zone.w - 40, y1 = zone.h * 0.33, y2 = zone.h * 0.72;
  c.poly([[x0 + 8, y1 - 8], [x0 + 16, y1], [x0 + 8, y1 + 8], [x0, y1]], st.hi, 1.8, 255, true);
  c.dot(x0 + 8, y1, 2.5, st.hi);
  c.text(x0 + 22, y1, count(input.wsl), { size: 8, weight: 700, align: 'LeftCenter', color: st.hi });
  c.icon('gear', x0 + 8, y2, 18, st.accent, 1.3);
  c.text(x0 + 22, y2, count(input.llm), { size: 8, weight: 700, align: 'LeftCenter', color: st.accent });
  return c.flush();
}
