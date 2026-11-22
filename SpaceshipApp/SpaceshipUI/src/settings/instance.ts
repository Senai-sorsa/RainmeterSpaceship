import { chooseHost } from '../host/HostBridge';
import modulesJson from '../generated/modules.json';
import { REGISTRY } from './registry';
import { moduleDefs } from './dynamic';
import { createSettingsStore } from './store';
import { frameVirtuals } from './frameStyle';

export const host = chooseHost(); // UI code only ever sees HostBridge
export const DEFS = [...REGISTRY, ...moduleDefs(modulesJson as { keys: string[] })];
export const store = createSettingsStore(host, DEFS, { virtuals: frameVirtuals });
