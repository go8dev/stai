/**
 * A visitor who is not signed in only ever sees the sign-in screen.
 *
 * These tests use a real browser against the running app and never sign in. The list of
 * screens comes from the app's own module list, so a screen added later is covered
 * without changing this file.
 */
import { expect, test, type Page } from '@playwright/test';
import { MODULES, SYSTEM_STATUS_PATH } from '../artifacts/stai/src/lib/modules';

const SCREENS = [
  '/',
  SYSTEM_STATUS_PATH,
  ...MODULES.map((module) => module.path),
  '/no-such-screen',
];

/** The protected routes the signed-in app reads, and one that does not exist. */
const PROTECTED_API_PATHS = [
  '/api/system/status',
  '/api/audit/events',
  '/api/auth/csrf',
  '/api/no-such-route',
];

/** Records the API paths the page calls. */
function recordApiCalls(page: Page): string[] {
  const calls: string[] = [];
  page.on('request', (request) => {
    const { pathname } = new URL(request.url());
    if (pathname.startsWith('/api/')) calls.push(pathname);
  });
  return calls;
}

async function expectOnlySignIn(page: Page): Promise<void> {
  await expect(page.getByTestId('signin-screen')).toBeVisible();
  await expect(page.getByTestId('button-login')).toHaveText('Log in');
  await expect(page.getByTestId('paper-label')).toBeVisible();
  // Nothing of the signed-in interface is in the page: no navigation, no log out.
  await expect(page.locator('[data-testid^="nav-"]')).toHaveCount(0);
  await expect(page.getByRole('navigation')).toHaveCount(0);
  await expect(page.getByText('Log out')).toHaveCount(0);
}

test.describe('a signed-out visitor', () => {
  for (const path of SCREENS) {
    test(`sees only the sign-in screen at ${path}`, async ({ page }) => {
      const apiCalls = recordApiCalls(page);

      await page.goto(path);
      await expectOnlySignIn(page);
      await page.waitForLoadState('networkidle');

      // The page asked who is signed in and requested nothing else from the server.
      expect([...new Set(apiCalls)]).toEqual(['/api/auth/user']);
      // It stayed on the address that was opened: no screen was routed to.
      expect(new URL(page.url()).pathname).toBe(path);
    });
  }

  test('is told when sign-in was refused, with the refused account ID', async ({
    page,
  }) => {
    await page.goto('/?signin=refused&account=12345678');

    await expectOnlySignIn(page);
    await expect(page.getByTestId('signin-notice')).toHaveAttribute(
      'data-reason',
      'refused',
    );
    await expect(page.getByTestId('text-refused-account-id')).toHaveText(
      '12345678',
    );
  });

  test('sees no provider name on the sign-in screen', async ({ page }) => {
    await page.goto('/');

    await expectOnlySignIn(page);
    await expect(page.locator('body')).not.toContainText(/replit/i);
  });

  test('starts sign-in on the server when pressing Log in', async ({
    page,
  }) => {
    // Answer the first step here, so the test never leaves the app for the sign-in provider.
    await page.route('**/api/login**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<!doctype html><title>Sign-in stopped by the test</title>',
      }),
    );
    await page.goto('/');

    await page.getByTestId('button-login').click();
    await page.waitForURL('**/api/login**');

    const url = new URL(page.url());
    expect(url.pathname).toBe('/api/login');
    expect(url.searchParams.get('returnTo')).toBe('/');
  });

  test('is refused by every protected API route', async ({ request }) => {
    for (const path of PROTECTED_API_PATHS) {
      const response = await request.get(path);
      expect(response.status(), path).toBe(401);
      expect((await response.json()).error, path).toBe('not_authenticated');
    }

    // The one route that changes nothing but is not a read: checking the audit trail.
    const verify = await request.post('/api/audit/verify');
    expect(verify.status()).toBe(401);
    expect((await verify.json()).error).toBe('not_authenticated');
  });

  test('can reach the health check and learn that nobody is signed in', async ({
    request,
  }) => {
    const health = await request.get('/api/healthz');
    expect(health.status()).toBe(200);
    expect(await health.json()).toEqual({ status: 'ok' });

    const session = await request.get('/api/auth/user');
    expect(session.status()).toBe(200);
    expect(await session.json()).toEqual({ user: null });
  });
});
