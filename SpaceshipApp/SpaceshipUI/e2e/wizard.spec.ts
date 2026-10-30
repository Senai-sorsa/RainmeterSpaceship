import { expect, test, type Page } from '@playwright/test';
import { STEPS } from '../src/wizard/wizard';

const fresh = '/?host=mock&fresh=1';
const sent = (page: Page, type: string) => page.evaluate((t) => (window as unknown as { __host: { sent: Record<string, unknown>[] } }).__host.sent.filter((m) => m.type === t), type);
const btn = (page: Page, name: string) => page.getByRole('button', { name, exact: true });
const wizard = (page: Page) => page.getByRole('dialog', { name: 'Setup' });

test('fresh host shows the wizard, not the HUD', async ({ page }) => {
  await page.goto(fresh);
  await expect(wizard(page)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Open Control Center' })).toHaveCount(0);
  await expect(page.locator('g.zone')).toHaveCount(0);
});

test('Launch with no edits writes nothing and shows the HUD for good', async ({ page }) => {
  await page.goto(fresh);
  await expect(page.getByLabel('Your changes')).toContainText('No changes');
  await btn(page, 'Launch CSpace').click();
  await expect(wizard(page)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Open Control Center' })).toBeVisible();
  expect(await sent(page, 'config.set')).toEqual([]);
  expect((await sent(page, 'setup.finish'))[0]).toMatchObject({ mode: 'custom' });
  await page.goto('/?host=mock'); // not fresh=1, which would wipe the saved flag
  await expect(page.getByRole('button', { name: 'Open Control Center' })).toBeVisible();
});

test('Use defaults finishes at once and the wizard never reappears', async ({ page }) => {
  await page.goto(fresh);
  await btn(page, 'Use defaults').click();
  await expect(wizard(page)).toHaveCount(0);
  expect((await sent(page, 'setup.finish'))[0]).toMatchObject({ mode: 'defaults' });
  await page.goto('/?host=mock'); // not fresh=1, which would wipe the saved flag
  await expect(wizard(page)).toHaveCount(0);
});

test('customizing writes only the edited keys, Confirm lights the module and the list shows the change', async ({ page }) => {
  await page.goto(fresh);
  const call = page.getByRole('textbox', { name: 'Call me' });
  await call.fill('Captain');
  await call.press('Enter');
  await page.getByRole('textbox', { name: 'About me' }).fill('I like space.');
  await expect(page.getByLabel('Your changes')).toContainText('Call me');
  await btn(page, 'Confirm').click();
  await expect(page.locator('.wiz-mod').first()).toContainText('Ready');
  await expect(page.locator('.wiz-mod').nth(1)).toHaveAttribute('aria-current', 'step');
  await btn(page, 'Launch CSpace').click();
  await expect(wizard(page)).toHaveCount(0);
  expect((await sent(page, 'config.set')).map((m) => m.key)).toEqual(['JarvisCallMe']);
  expect((await sent(page, 'aboutme.set'))[0]).toMatchObject({ text: 'I like space.' });
});

test('label preview is live and an invalid label shows the reason', async ({ page }) => {
  await page.goto(fresh);
  const preview = page.locator('[data-preview]');
  await expect(preview).toContainText('J.A.R.V.I.S');
  await page.getByRole('textbox', { name: 'Assistant name' }).fill('Friday');
  await expect(preview).toContainText('F.R.I.D.A.Y');
  await page.getByRole('textbox', { name: 'Assistant label' }).fill('A!B');
  await expect(preview).toContainText('Use 1-24 letters, digits, dots or spaces.');
});

test('Advanced disclosure on the assistant step starts closed and expands', async ({ page }) => {
  await page.goto(fresh);
  const adv = page.locator('details[data-advanced]');
  await expect(adv).toHaveJSProperty('open', false);
  await adv.locator('> summary').click();
  await expect(adv).toHaveJSProperty('open', true);
});

test('with localStorage blocked the wizard still gates from host state', async ({ browser }) => {
  const page = await browser.newPage();
  await page.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } }); });
  await page.goto('/?host=mock');
  await expect(wizard(page)).toBeVisible();
  await btn(page, 'Use defaults').click();
  await expect(wizard(page)).toHaveCount(0);
  await page.close();
});

test('apps step opens the secure flows through the host; System > Reset setup clears the flag', async ({ page }) => {
  await page.goto(fresh);
  await page.locator('.wiz-mod').nth(3).click();
  await btn(page, 'Connect Gmail').click();
  expect((await sent(page, 'flow.open'))[0]).toMatchObject({ flow: 'gmail' });
  await btn(page, 'Use defaults').click();
  await page.getByRole('button', { name: 'Open Control Center' }).click();
  await page.getByRole('button', { name: 'System', exact: true }).click();
  await page.getByRole('button', { name: 'Run setup again' }).click();
  await expect(wizard(page)).toBeVisible();
});

test('every module opens, the page never scrolls at 1280x800 and the Systems module lists the HUD modules (screenshots)', async ({ page }) => {
  await page.goto(fresh);
  for (let n = 0; n < STEPS.length; n++) {
    await page.locator('.wiz-mod').nth(n).click();
    expect(await page.locator('.wiz').evaluate((e) => e.scrollHeight <= e.clientHeight), `module ${STEPS[n].id} scrolls the page`).toBe(true);
    await page.screenshot({ path: `artifacts/wizard-${n + 1}.png` });
  }
  await page.locator('.wiz-mod').nth(2).click();
  expect(await page.locator('[data-step="systems"] .row').count()).toBeGreaterThan(3);
});

test('stacks below 1100px without hiding Launch', async ({ page }) => {
  await page.setViewportSize({ width: 1000, height: 800 });
  await page.goto(fresh);
  await expect(btn(page, 'Launch CSpace')).toBeVisible();
  await page.screenshot({ path: 'artifacts/wizard-narrow.png' });
});
