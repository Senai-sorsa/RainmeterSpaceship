import { describe, expect, it } from 'vitest';
import { launch } from '../src/modules/hit';
import { host } from '../src/settings/instance';
import type { MockHost } from '../src/host/HostBridge';
import { messageProblem } from '../src/host/contract';
import type { App } from '../src/modules/apps';

describe('launch', () => {
  it('sends only the app id, which the contract accepts, and skips missing apps', () => {
    const sent = (host as MockHost).sent;
    const app = { id: 'chrome', missing: false } as App;
    launch(app);
    launch({ ...app, missing: true });
    launch(undefined);
    const msgs = sent.filter((m) => m.type === 'app.launch');
    expect(msgs).toEqual([{ type: 'app.launch', id: 'chrome' }]);
    expect(messageProblem(msgs[0])).toBeNull();
  });
});
