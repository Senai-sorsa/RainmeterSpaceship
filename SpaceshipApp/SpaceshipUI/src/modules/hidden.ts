/**
 * modules.json key → the layout zones that skin config draws. State.inc Off_<key>=1 hides it (control.lua deactivates
 * the config). Controller has no zone; Frame, LeftLocation and OverlayDrawer are whole modules the Hud skips itself.
 */
const KEY_ZONES: Record<string, string[]> = {
  BottomAudio: ['B_audio'], BottomPanels: ['B_panelL', 'B_panelR'], BottomStorage: ['B_storage'], BottomStrip: ['B_stripL', 'B_stripR'],
  CenterHUD: ['C_hud'], CenterSphere: ['C_sphere'], CenterTarget: ['C_target'],
  LeftCategory: ['L_tabs', 'L_category', 'L_dots'], LeftSlot1: ['L_app1'], LeftSlot2: ['L_app2'], LeftSlot3: ['L_app3'], LeftSlot4: ['L_app4'], LeftUpkeep: ['L_upkeep'],
  RightCategory: ['R_tabs', 'R_category', 'R_dots'], RightSlot5: ['R_app1'], RightSlot6: ['R_app2'], RightSlot7: ['R_app3'], RightSlot8: ['R_app4'],
  RightDev: ['R_dev'], RightSysInfo: ['R_sysinfo'],
  TopAlert: ['T_alert'], TopBattery: ['T_battery'], TopConsole: ['T_settings'], TopGraphA: ['G2_select'], TopGraphB: ['G3_select'],
  TopGraphCPU: ['G1_cpu'], TopGraphRAM: ['G4_ram'], TopPower: ['T_power'],
};

/** The zones the Off_ settings hide, as a comma list: a string, so a module can keep it in its hook deps. */
export function hiddenZones(values: Record<string, string>): string {
  return Object.entries(KEY_ZONES).filter(([k]) => values[`Off_${k}`] === '1').flatMap(([, ids]) => ids).join(',');
}

/** A module's zone table with each hidden zone (and each hidden slot in an array) replaced by undefined. */
export function visible<T extends object>(zones: T, hide: string): T {
  if (!hide) return zones;
  const off = new Set(hide.split(','));
  const keep = (z: unknown) => (z && typeof z === 'object' && off.has((z as { id: string }).id) ? undefined : z);
  return Object.fromEntries(Object.entries(zones).map(([k, z]) => [k, Array.isArray(z) ? z.map(keep) : keep(z)])) as T;
}
