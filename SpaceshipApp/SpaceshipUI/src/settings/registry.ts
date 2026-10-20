import { moduleDefs } from './dynamic';
import type { CategoryId, Control, Level, SettingDef, WizardStep } from './types';

export const CATEGORIES: { id: CategoryId; label: string }[] = [
  { id: 'display', label: 'Display' }, { id: 'layout', label: 'Layout' }, { id: 'apps', label: 'Apps' },
  { id: 'sensors', label: 'Sensors' }, { id: 'performance', label: 'Performance' }, { id: 'assistant', label: 'Assistant' },
  { id: 'integrations', label: 'Integrations' }, { id: 'system', label: 'System' },
];

/** Runtime state; never shown as rows. UseShipImage/FrameOff are reached only through the virtual frameStyle row. */
export const INTERNAL_KEYS = new Set([
  'MasterPrev', 'LastSpeedTest', 'LastAppScan', 'MonX', 'MonY', 'SensorStatus', 'CtlTab', 'CtlPage', 'CtlMod', 'DialSel',
  'UseShipImage', 'FrameOff',
]);
export const WRITABLE_INTERNAL = ['UseShipImage', 'FrameOff'];

// --- compact row DSL: [key, label, help, control, default, flags?]
type Flags = { opt?: 1; w?: WizardStep; virtual?: 1; restart?: 1 };
type Row = [string, string, string, Control, string, Flags?];
const tog: Control = { kind: 'toggle' };
const col: Control = { kind: 'color' };
const sl = (min: number, max: number, step: number): Control => ({ kind: 'slider', min, max, step });
const tx = (pattern: string, max = 64): Control => ({ kind: 'text', pattern, max });
const sel = (...o: string[]): Control => ({ kind: 'select', options: o.map((s) => { const [value, label] = s.split('|'); return { value, label: label ?? value }; }) });
const act = (id: string): Control => ({ kind: 'action', id });
const free = tx('^[^\\r\\n=;\\[\\]#"%]{0,200}$', 200);
const name = tx('^[A-Za-z0-9]{1,24}$', 24);
const label24 = tx('^[A-Za-z0-9. ]{0,24}$', 24); // empty = derive from the name
const font = tx('^[A-Za-z0-9 ._-]{1,40}$', 40);
const path = tx('^[^\\r\\n"%;#=]{0,200}$', 200);

const defs: SettingDef[] = [];
function add(category: CategoryId, group: string, level: Level, rows: Row[]) {
  for (const [key, label, help, control, def, f = {}] of rows) {
    const d: SettingDef = { key, file: 'Settings.inc', label, help, category, group, level, control, default: def };
    if (f.opt) d.optional = true;
    if (f.virtual) d.virtual = true;
    if (f.w) d.wizard = f.w;
    if (f.restart) d.restartRequired = true;
    defs.push(d);
  }
}
const O = { opt: 1 } as const;
const V = { virtual: 1 } as const;

// ---------------------------------------------------------------- Display
add('display', 'Theme', 'normal', [
  ['ColorAccent', 'Accent colour', 'Main HUD colour (r,g,b).', col, '0,210,255', { w: 'look' }],
  ['ColorWarn', 'Warning colour', 'Colour for warnings such as a low battery.', col, '255,130,40'],
  ['GlowAlpha', 'Glow strength', 'How strongly the neon lines glow.', sl(0, 160, 4), '76'],
]);
add('display', 'Theme', 'advanced', [
  ['ColorDim', 'Dim colour', 'Colour for inactive lines and labels.', col, '0,110,150'],
  ['ColorText', 'Text colour', 'Colour for text.', col, '170,235,255'],
  ['ColorAlert', 'Alert colour', 'Colour for alerts.', col, '255,60,70'],
  ['ColorGood', 'Good colour', 'Colour for healthy readings.', col, '60,255,170'],
  ['ColorHighlight', 'Highlight colour', 'Colour for highlighted items.', col, '255,105,135'],
  ['ColorWhite', 'White colour', 'The near-white used for bright details.', col, '215,240,255'],
  ['ColorPanel', 'Panel colour', 'Panel fill as r,g,b,a.', col, '0,30,45,90'],
  ['CoreWhite', 'Hot cores', 'How white-hot the line cores are (1 = white).', sl(0, 1, 0.1), '0.3'],
  ['GlowWidth', 'Glow width', 'Width of the neon glow in pixels.', sl(1, 8, 0.1), '3.0'],
  ['TextGlow', 'Text glow', 'Size of the glow behind text in pixels.', sl(0, 12, 1), '4'],
  ['TextGlowAlpha', 'Text glow strength', 'Opacity of the text glow.', sl(0, 255, 5), '150'],
]);
add('display', 'Frame', 'normal', [
  ['frameStyle', 'Cockpit frame', 'Choose the rendered hull, your own picture, or no frame.', sel('rendered|Rendered', 'picture|Picture', 'none|None'), 'rendered', { w: 'look', virtual: 1 }],
  ['FrameBrightness', 'Frame brightness', 'Brightness of the hull in percent.', sl(0, 100, 5), '95'],
  ['HullAlpha', 'Hull opacity', 'Opacity of the hull, 0 to 255.', sl(0, 255, 5), '255'],
]);
add('display', 'Frame', 'advanced', [
  ['FrameBehindTaskbar', 'Frame behind taskbar', 'Draw the frame under the Windows taskbar.', tog, '1'],
  ['GlassTint', 'Window tint', 'Darkness of the cockpit glass tint.', sl(0, 255, 3), '66'],
  ['GlassGlare', 'Glass glare', 'Strength of smudges and reflections on the glass.', sl(0, 60, 4), '12'],
  ['ScanLines', 'Scanlines', 'Show scanlines over the HUD.', tog, '1'],
  ['ScanAlpha', 'Scanline darkness', 'How dark the scanlines are.', sl(0, 14, 1), '6'],
  ['ShadeAlpha', 'Dark tints', 'Shading behind the HUD on the glass.', sl(0, 255, 5), '155'],
  ['MistAlpha', 'Mist', 'Opacity of the glass mist.', sl(0, 255, 5), '255'],
  ['HullDark', 'Hull dark', 'Darkest hull colour.', col, '10,12,15'],
  ['HullMid', 'Hull mid', 'Mid hull colour.', col, '20,25,30'],
  ['HullLight', 'Hull light', 'Lightest hull colour.', col, '35,40,50'],
  ['HullEdge', 'Hull edge', 'Hull edge colour.', col, '60,70,85'],
  ['ShipImage', 'Picture file', 'File name in Images used by Picture mode.', tx('^[A-Za-z0-9._-]{1,64}$'), 'ship.png'],
]);
add('display', 'Size and text', 'normal', [
  ['Scale', 'HUD size', 'Overall size of the HUD.', sl(0.4, 3, 0.01), '0.67', { w: 'look' }],
  ['HudAlpha', 'HUD opacity', 'Opacity of every line and label.', sl(40, 255, 5), '255'],
  ['AutoFit', 'Auto fit', 'Fit the HUD to the screen automatically.', tog, '0'],
]);
add('display', 'Size and text', 'advanced', [
  ['FontTitle', 'Title font', 'Font for titles.', font, 'B612 Mono'],
  ['FontText', 'Text font', 'Font for body text.', font, 'B612 Mono'],
  ['FontNum', 'Number font', 'Font for numbers.', font, 'B612 Mono'],
  ['TextScaleLarge', 'Large text scale', 'Scale of large text.', sl(0.5, 3, 0.05), '1.45'],
  ['TextScaleSmall', 'Small text scale', 'Scale of small text.', sl(0.5, 3, 0.05), '1.85'],
  ['CaptionStyle', 'Caption style', 'Style of module captions (0 is the plainest).', sl(0, 3, 1), '1'],
  ['HomeMonitor', 'Home monitor', 'Monitor the HUD lives on, or auto.', tx('^[A-Za-z0-9 _.:-]{1,40}$', 40), 'auto'],
  ['HomeSize', 'Home size', 'Home monitor size as WIDTHxHEIGHT.', tx('^[0-9]{3,5}x[0-9]{3,5}$', 11), '2560x1600'],
  ['OriginX', 'Origin X', 'Shift the whole HUD horizontally.', sl(-4000, 4000, 1), '0'],
  ['OriginY', 'Origin Y', 'Shift the whole HUD vertically.', sl(-4000, 4000, 1), '0'],
]);
add('display', 'Startup', 'normal', [
  ['BootAnim', 'Boot animation', 'Play the start-up animation.', tog, '1'],
  ['BootSound', 'Boot sound', 'Play the start-up sound.', tog, '1'],
]);

// ---------------------------------------------------------------- Layout (module keys come from dynamic.ts)
add('layout', 'Edit', 'normal', [
  ['EditMode', 'Edit mode', 'Unlock modules so you can drag them.', act('edit.toggle'), '0'],
  ['presets', 'Presets', 'Save or load a whole layout.', act('presets.open'), '', V],
]);

// ---------------------------------------------------------------- Apps
add('apps', 'Apps', 'normal', [['apps.scan', 'Scan apps', 'Rescan the Start menu for apps.', act('apps.scan'), '', { w: 'apps', virtual: 1 }]]);
add('apps', 'Apps', 'advanced', [['apps.icons', 'Rebuild icons', 'Rebuild the app icon cache.', act('apps.icons'), '', V]]);

// ---------------------------------------------------------------- Sensors
const SRC = ['cpu', 'ram', 'gpu', 'vram', 'cputemp|CPU temp', 'gputemp|GPU temp', 'power', 'disk', 'netdown|Net down', 'netup|Net up', 'battery'];
add('sensors', 'Graphs', 'normal', [
  ['GraphA_Source', 'Graph A source', 'What the first graph shows.', sel(...SRC), 'gpu'],
  ['GraphB_Source', 'Graph B source', 'What the second graph shows.', sel(...SRC), 'netdown'],
  ['Drive1', 'Drive 1', 'First drive letter to monitor.', tx('^[A-Za-z]:$', 2), 'C:'],
  ['Drive2', 'Drive 2', 'Second drive letter to monitor.', tx('^[A-Za-z]:$', 2), 'D:'],
]);
add('sensors', 'Graphs', 'advanced', [['DataDivider', 'Data divider', 'Show the divider line in graphs.', tog, '1']]);
add('sensors', 'Network', 'normal', [
  ['PingHost', 'Ping host', 'Address used for the ping reading.', tx('^[A-Za-z0-9.:-]{1,64}$'), '1.1.1.1'],
  ['AutoSpeedTestHours', 'Speed test every', 'Hours between automatic speed tests (0 = off).', sl(0, 48, 1), '6'],
]);
add('sensors', 'Network', 'advanced', [
  ['LinkDownMbps', 'Link download', 'Your line speed down, in Mbps.', sl(0, 10000, 1), '176'],
  ['LinkUpMbps', 'Link upload', 'Your line speed up, in Mbps.', sl(0, 10000, 1), '423'],
  ['IpMask', 'Mask IP', 'Hide IP addresses in the network block.', tog, '1'],
  ['LocationEnabled', 'Show location', 'Show approximate location.', tog, '1'],
  ['LocationMask', 'Mask location', 'Hide the location text.', tog, '0'],
]);
add('sensors', 'Battery', 'normal', [
  ['WarnBattery', 'Battery warning', 'Warn below this battery percent.', sl(5, 50, 1), '20'],
  ['ChargeLimit', 'Charge limit', 'Target charge limit in percent.', sl(50, 100, 5), '80'],
]);
add('sensors', 'Battery', 'advanced', [['BatteryMinTier', 'Battery minimum tier', 'Lowest performance tier allowed on battery.', sl(0, 3, 1), '1']]);
add('sensors', 'Warnings', 'normal', [
  ['WarnCpuTemp', 'CPU temperature warning', 'Warn above this CPU temperature (C).', sl(50, 110, 1), '92'],
  ['WarnGpuTemp', 'GPU temperature warning', 'Warn above this GPU temperature (C).', sl(50, 110, 1), '85'],
  ['WarnDiskPct', 'Disk usage warning', 'Warn above this disk percent.', sl(50, 100, 1), '90'],
]);
add('sensors', 'HWiNFO labels', 'advanced', ([
  ['HW_ChargeRate', 'Charge rate'], ['HW_CpuPower', 'CPU power'], ['HW_CpuTemp', 'CPU temperature'], ['HW_Fan1', 'Fan 1'], ['HW_Fan2', 'Fan 2'],
  ['HW_FullCap', 'Full capacity'], ['HW_GpuClock', 'GPU clock'], ['HW_GpuPower', 'GPU power'], ['HW_GpuTemp', 'GPU temperature'],
  ['HW_RemainCap', 'Remaining capacity'], ['HW_SsdTemp', 'SSD temperature'], ['HW_Wear', 'Battery wear'],
] as [string, string][]).map(([k, l]): Row => [k, l, 'HWiNFO sensor index for this reading (-1 = not mapped).', sl(-1, 199, 1), '-1']));

// ---------------------------------------------------------------- Performance
add('performance', 'Tier', 'normal', [
  ['PerfTier', 'Current tier', 'The performance tier now in use (0 full, 3 stealth).', sel('0|Full', '1|Lite', '2|Low', '3|Stealth'), '0'],
  ['PerfOverride', 'Tier mode', 'Force a tier, or leave on Auto.', sel('-1|Auto', '0|Full', '1|Lite', '2|Low', '3|Stealth'), '0'],
]);
add('performance', 'Tier', 'advanced', [
  ['TierLite', 'Lite above', 'GPU percent where Lite starts.', sl(10, 95, 5), '50'],
  ['TierLow', 'Low above', 'GPU percent where Low starts.', sl(10, 98, 5), '75'],
  ['TierStealth', 'Stealth above', 'GPU percent where Stealth starts.', sl(10, 100, 5), '85'],
]);
add('performance', 'Hardware control', 'advanced', [
  ['LltPath', 'LLT path', 'Path to the laptop control tool.', path, ''],
  ['LltPowerFeature', 'Power feature', 'Feature name for power mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'power-mode'],
  ['LltPowerModes', 'Power modes', 'Comma list of power modes.', tx('^[A-Za-z0-9,._-]{0,80}$', 80), 'quiet,balance,performance'],
  ['LltRefreshFeature', 'Refresh feature', 'Feature name for refresh rate.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'refresh-rate'],
  ['LltRefreshRates', 'Refresh rates', 'Comma list of refresh rates.', tx('^[0-9,]{0,40}$', 40), '60,165'],
  ['LltHybridFeature', 'Hybrid feature', 'Feature name for GPU mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'hybrid-mode'],
  ['LltHybridAUTO', 'Hybrid auto', 'Value for auto GPU mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'on-auto'],
  ['LltHybridDGPU', 'Hybrid dGPU', 'Value for dedicated GPU mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'off'],
  ['LltHybridECO', 'Hybrid eco', 'Value for integrated GPU mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'on-igpu-only'],
  ['LltHybridHYBRID', 'Hybrid hybrid', 'Value for hybrid GPU mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'on'],
  ['LltBatteryFeature', 'Battery feature', 'Feature name for battery mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'battery'],
  ['LltBatteryNormal', 'Battery normal', 'Value for normal charging.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'normal'],
  ['LltBatteryConserve', 'Battery conserve', 'Value for conservation mode.', tx('^[A-Za-z0-9._-]{0,40}$', 40), 'conservation'],
]);

// ---------------------------------------------------------------- Assistant
add('assistant', 'Identity', 'normal', [
  ['JarvisName', 'Assistant name', 'The name you call your assistant (letters and digits).', name, 'Jarvis', { opt: 1, w: 'assistant' }],
  ['AssistantLabel', 'Assistant label', 'Text shown on the HUD; empty derives it from the name.', label24, '', { opt: 1, w: 'assistant' }],
  ['JarvisCallMe', 'Call me', 'What the assistant calls you.', tx('^[A-Za-z0-9. ]{1,24}$', 24), 'Sir', { w: 'you' }],
  ['JarvisEnabled', 'Assistant enabled', 'Turn the assistant on or off.', tog, '1'],
  ['JarvisAutoStart', 'Start with HUD', 'Start the assistant when the HUD starts.', tog, '1'],
]);
add('assistant', 'Wake word', 'normal', [['JarvisWakeModel', 'Wake model', 'Wake-word model name.', tx('^[A-Za-z0-9_.-]{1,40}$', 40), 'hey_jarvis', { w: 'assistant' }]]);
add('assistant', 'Wake word', 'advanced', [
  ['JarvisWakeSensitivity', 'Wake sensitivity', 'Lower hears you more easily, higher is stricter.', sl(0.2, 0.9, 0.05), '0.5'],
  ['JarvisWakeWord', 'Use wake word', 'Listen for the wake word.', tog, '1'],
  ['JarvisNameAliases', 'Name aliases', 'Other spellings the assistant should answer to.', free, '', O],
  ['JarvisStopKey', 'Stop key', 'Key that stops the assistant talking (off disables).', sel('end|End', 'off|Off'), 'end', O],
  ['JarvisBargeIn', 'Barge in', 'How you may interrupt the assistant.', sel('off|Off', 'wake|Wake word', 'voice|Voice'), 'wake', O],
]);
add('assistant', 'Voice', 'normal', [
  ['JarvisKokoroVoice', 'Voice', 'Which voice the assistant speaks with.', sel('bm_lewis', 'bf_emma', 'am_michael', 'af_heart', 'default'), 'bm_lewis', { w: 'assistant' }],
  ['JarvisVoiceSpeed', 'Voice speed', 'Speaking speed of the voice.', sl(0.8, 1.2, 0.05), '1.0', O],
]);
add('assistant', 'Voice', 'advanced', [
  ['JarvisVoice', 'Voice model file', 'Path of the voice model.', path, 'Jarvis\\kokoro\\kokoro-v1.0.onnx'],
  ['JarvisVoiceRate', 'Voice rate', 'Speaking rate offset.', sl(-5, 5, 1), '1'],
  ['JarvisSpeed', 'Orb speed', 'Animation speed.', sl(0.25, 3, 0.25), '1'],
  ['JarvisSilence', 'Silence wait', 'Seconds of silence before it stops listening.', sl(0.5, 6, 0.1), '1.2'],
  ['JarvisChime', 'Chime', 'Play a chime when listening starts.', tog, '1'],
  ['JarvisChimeVolume', 'Chime volume', 'Chime loudness, 0 to 100.', sl(0, 100, 5), '25', O],
  ['JarvisDuck', 'Duck music', 'Lower other audio while the assistant talks.', tog, '1', O],
  ['JarvisDuckLevel', 'Duck level', 'How far other audio is lowered, in percent.', sl(10, 80, 10), '30', O],
]);
add('assistant', 'Model', 'advanced', [
  ['JarvisModel', 'Model', 'Main language model name (empty = automatic).', tx('^[A-Za-z0-9_.:/-]{0,80}$', 80), ''],
  ['JarvisModelFast', 'Fast model', 'Small model for quick answers.', tx('^[A-Za-z0-9_.:/-]{0,80}$', 80), 'llama3.2:3b'],
  ['JarvisKeepAlive', 'Keep alive', 'Minutes the model stays loaded.', sl(0, 120, 1), '10'],
  ['JarvisWhisper', 'Speech model', 'Speech-recognition model size.', sel('tiny.en', 'base.en', 'small.en', 'medium.en'), 'small.en'],
  ['JarvisWhisperDevice', 'Speech device', 'Where speech recognition runs.', sel('auto', 'cpu', 'cuda'), 'cuda'],
  ['JarvisContext', 'Context size', 'How much conversation the model remembers.', sl(512, 16384, 512), '2048'],
  ['JarvisGPU', 'GPU use', 'Prefer the GPU or require it.', sel('prefer|Prefer', 'require|Require'), 'prefer', O],
  ['JarvisIdleUnload', 'Idle unload', 'Minutes idle before the model unloads (0 = never).', sl(0, 120, 5), '10', O],
  ['JarvisPython', 'Python path', 'Python used to run the assistant (empty = automatic).', path, ''],
  ['JarvisAIRouter', 'AI router', 'Let the AI route requests.', tog, '1', O],
]);
add('assistant', 'Behaviour', 'normal', [
  ['JarvisPrivacy', 'Privacy mode', 'Keep personal details out of the assistant.', tog, '0', { opt: 1, w: 'assistant' }],
  ['JarvisLearn', 'Learn about me', 'Let the assistant remember facts about you.', sel('auto|Auto', 'ask|Ask', 'off|Off'), 'auto', O],
  ['JarvisTalkLess', 'Talk less', 'Keep answers short.', tog, '0', O],
]);
add('assistant', 'Behaviour', 'advanced', [
  ['JarvisRecall', 'Recall', 'Remember earlier conversations.', sel('on|On', 'off|Off'), 'on', O],
  ['JarvisSeriousTopics', 'Serious topics', 'Be serious on heavy topics.', tog, '1', O],
  ['JarvisRoomAsk', 'Ask the room', 'Ask who is in the room.', tog, '0', O],
  ['JarvisFollowUp', 'Follow-up', 'Listen briefly for a follow-up.', tog, '1', O],
  ['JarvisFollowUpWait', 'Follow-up wait', 'Seconds to wait for a follow-up.', sl(3, 30, 1), '3', O],
  ['JarvisFollowNameWindow', 'Name window', 'Seconds a name keeps you in conversation.', sl(3, 60, 1), '10', O],
  ['JarvisFirstWords', 'First words', 'Words spoken before the full answer.', sl(0, 12, 1), '5', O],
  ['JarvisPersonality', 'Personality', 'How the assistant talks.', sel('playful|Playful', 'mirror|Mirror', 'serious|Serious', 'brief|Brief'), 'playful', O],
  ['JarvisSmartSearch', 'Smart search', 'Search the web when it helps.', tog, '1', O],
  ['JarvisQuietCalendar', 'Quiet calendar', 'Calendar name whose events keep it quiet.', free, '', O],
  ['JarvisDiagnose', 'Self-diagnose', 'Let the assistant diagnose problems.', tog, '1', O],
  ['JarvisWatch', 'Watch', 'Let the assistant watch for problems.', tog, '1', O],
  ['JarvisProfile', 'Profile file', 'Path of your about-me file.', path, ''],
]);
add('assistant', 'Orb and panel', 'advanced', [
  ['JarvisOrbBright', 'Orb brightness', 'Brightness of the orb.', sl(0.4, 1.6, 0.1), '1'],
  ['JarvisOrbSize', 'Orb size', 'Size of the orb.', sl(0.8, 1.15, 0.05), '1'],
  ['JarvisOrbits', 'Orbits', 'Show the orbit rings.', tog, '1'],
  ['JarvisShell', 'Shell', 'Show the orb shell.', tog, '1'],
  ['JarvisDial', 'Dial', 'Show the dial.', tog, '1'],
  ['JarvisBars', 'Bars', 'Show the audio bars.', tog, '1'],
  ['JarvisTint', 'Tint', 'Strength of the panel tint.', sl(0, 0.8, 0.01), '0.42'],
  ['JarvisFrameRate', 'Frame rate', 'Orb animation frames per second.', sl(5, 60, 5), '15'],
  ['JarvisBlackBackground', 'Black background', 'Use a solid black panel.', tog, '0'],
  ['JarvisColorIdle', 'Colour: standby', 'Orb colour while idle (empty = follow the theme).', col, ''],
  ['JarvisColorListen', 'Colour: listening', 'Orb colour while listening (empty = follow the theme).', col, ''],
  ['JarvisColorSpeak', 'Colour: speaking', 'Orb colour while speaking (empty = follow the theme).', col, ''],
  ['JarvisMutedPopup', 'Muted popup', 'Show a popup when the mic is muted.', tog, '1'],
  ['JarvisMic', 'Microphone', 'Microphone name (empty = default).', free, '', O],
]);

// ---------------------------------------------------------------- Integrations
add('integrations', 'Obsidian', 'normal', [
  ['ObsidianVault', 'Obsidian vault', 'Folder of your Obsidian vault.', path, '', { w: 'apps' }],
  ['ObsidianTodo', 'Todo note', 'Note file that holds your todos.', path, ''],
  ['ReticleTodo', 'Todo on reticle', 'Show todos on the centre reticle.', tog, '1'],
  ['JarvisVault', 'Assistant vault', 'Vault folder the assistant may read.', path, ''],
]);
add('integrations', 'Mail and calendar', 'normal', [
  ['flow.gmail', 'Gmail', 'Open the Gmail sign-in flow.', act('flow.open'), '', { w: 'apps', virtual: 1 }],
  ['flow.calendar', 'Calendars', 'Open the calendar sign-in flow.', act('flow.open'), '', { w: 'apps', virtual: 1 }],
]);

// ---------------------------------------------------------------- System
add('system', 'Setup', 'normal', [
  ['setup.rerun', 'Run setup again', 'Open the first-run wizard again.', act('setup.rerun'), '', V],
  ['setup.reset', 'Reset setup', 'Mark setup as not done.', act('setup.reset'), '', V],
]);
add('system', 'Setup', 'advanced', [['defaults.all', 'Defaults for everything', 'Reset every setting to its default.', act('defaults.all'), '', V]]);

export const REGISTRY: SettingDef[] = defs;

/** Keys config.set may write: real registry keys, per-module keys, and the frame internals. */
export function allowedKeys(modules: { keys: string[] }): Set<string> {
  return new Set([...REGISTRY.filter((d) => !d.virtual).map((d) => d.key), ...moduleDefs(modules).map((d) => d.key), ...WRITABLE_INTERNAL]);
}
