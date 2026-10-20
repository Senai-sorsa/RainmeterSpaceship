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

test('Next x5 with no edits reaches Review; Finish writes nothing and shows the HUD for good', async ({ page }) => {
  await page.goto(fresh);
  for (let n = 0; n < 5; n++) await btn(page, 'Next').click();
  await expect(page.getByLabel('Your changes')).toContainText('No changes');
  await btn(page, 'Finish').click();
  await expect(wizard(page)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Open Control Center' })).toBeVisible();
  expect(await sent(page, 'config.set')).toEqual([]);
  expect((await sent(page, 'setup.finish'))[0]).toMatchObject({ mode: 'custom' });
  await page.goto('/?host=mock'); // not fresh=1, which would wipe the saved flag
  await expect(page.getByRole('button', { name: 'Open Control Center' })).toBeVisible();
});

test('Use defaults on step 2 finishes at once and the wizard never reappears', async ({ page }) => {
  await page.goto(fresh);
  await btn(page, 'Next').click();
  await btn(page, 'Use defaults').click();
  await expect(wizard(page)).toHaveCount(0);
  expect((await sent(page, 'setup.finish'))[0]).toMatchObject({ mode: 'defaults' });
  await page.goto('/?host=mock'); // not fresh=1, which would wipe the saved flag
  await expect(wizard(page)).toHaveCount(0);
});

test('customizing writes only the edited keys and Review lists them', async ({ page }) => {
  await page.goto(fresh);
  await btn(page, 'Next').click(); // you
  const call = page.getByRole('textbox', { name: 'Call me' });
  await call.fill('Captain');
  await call.press('Enter');
  await page.getByRole('textbox', { name: 'About me' }).fill('I like space.');
  await btn(page, 'Next').click();
  for (let n = 0; n < 3; n++) await btn(page, 'Next').click();
  await expect(page.getByLabel('Your changes')).toContainText('Call me');
  await btn(page, 'Finish').click();
  await expect(wizard(page)).toHaveCount(0);
  expect((await sent(page, 'config.set')).map((m) => m.key)).toEqual(['JarvisCallMe']);
  expect((await sent(page, 'aboutme.set'))[0]).toMatchObject({ text: 'I like space.' });
});

test('label preview is live and an invalid label shows the reason', async ({ page }) => {
  await page.goto(fresh);
  await btn(page, 'Next').click();
  await btn(page, 'Next').click(); // assistant
  const preview = page.locator('[data-preview]');
  await expect(preview).toContainText('J.A.R.V.I.S');
  await page.getByRole('textbox', { name: 'Assistant name' }).fill('Friday');
  await expect(preview).toContainText('F.R.I.D.A.Y');
  await page.getByRole('textbox', { name: 'Assistant label' }).fill('A!B');
  await expect(preview).toContainText('Use 1-24 letters, digits, dots or spaces.');
});

test('Advanced disclosure on the assistant step starts closed and expands', async ({ page }) => {
  await page.goto(fresh);
  await btn(page, 'Next').click();
  await btn(page, 'Next').click();
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
  for (let n = 0; n < 4; n++) await btn(page, 'Next').click();
  await btn(page, 'Connect Gmail').click();
  expect((await sent(page, 'flow.open'))[0]).toMatchObject({ flow: 'gmail' });
  await btn(page, 'Use defaults').click();
  await page.getByRole('button', { name: 'Open Control Center' }).click();
  await page.getByRole('button', { name: 'System', exact: true }).click();
  await page.getByRole('button', { name: 'Run setup again' }).click();
  await expect(wizard(page)).toBeVisible();
});

test('all six steps fit 1280x800 without scrolling (screenshots)', async ({ page }) => {
  await page.goto(fresh);
  for (let n = 0; n < STEPS.length; n++) {
    const main = page.locator('.wiz-main');
    expect(await main.evaluate((e) => e.scrollHeight <= e.clientHeight), `step ${STEPS[n].id} scrolls`).toBe(true);
    await page.screenshot({ path: `artifacts/wizard-${n + 1}.png` });
    if (n < STEPS.length - 1) await btn(page, 'Next').click();
  }
});
