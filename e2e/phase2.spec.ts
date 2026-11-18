/**
 * Phase 2 read-only screens: the Market Scanner and the Portfolio.
 *
 * UI FIXTURE TESTING, NOT SIGN-IN. The signed-in pages are shown with page.route fixtures
 * shaped like the generated contract in lib/api-client-react/src/generated/api.schemas.ts.
 * Every value is synthetic, including the account, the prices and the ledger. The real
 * backend is not asked for signed-in data, and the owner account is never used. The
 * signed-out tests at the end use the real backend, because that is the gate they test.
 *
 * Runs on the desktop and phone projects in playwright.config.ts.
 */
import { expect, test, type Page, type Route } from '@playwright/test';
import {
  AllocationBalanceMarketType,
  LedgerEventMarketType,
  MarketIndicatorsScreeningState,
  MarketScannerRowMarketType,
  MarketScannerRowStatus,
  type CandlePoint,
  type ErrorResponse,
  type LedgerList,
  type LedgerVerification,
  type MarketScannerResponse,
  type MarketScannerRow,
  type PortfolioSummary,
} from '../lib/api-client-react/src/generated/api.schemas';

// ---------------------------------------------------------------------------
// Synthetic fixtures. Prices are fixture values, never live market data.
// ---------------------------------------------------------------------------

const CANDLES: CandlePoint[] = [
  {
    openedAt: '2025-01-15T03:00:00.000Z',
    open: '43100.0',
    high: '43250.0',
    low: '43080.0',
    close: '43210.5',
    volume: '120.5',
    quoteVolume: '5200000.0',
    complete: true,
  },
  {
    openedAt: '2025-01-15T04:00:00.000Z',
    open: '43210.5',
    high: '43260.0',
    low: '43190.0',
    close: '43228.0',
    volume: '44.2',
    quoteVolume: '1910000.0',
    complete: false,
  },
];

function liveRow(
  symbol: string,
  marketType: MarketScannerRowMarketType,
  status: MarketScannerRowStatus,
  ageSeconds: number,
  price: string,
  screeningState: MarketIndicatorsScreeningState,
): MarketScannerRow {
  const perp = marketType === MarketScannerRowMarketType.futures;
  return {
    symbol,
    marketType,
    status,
    observedAt: '2025-01-15T04:00:00.000Z',
    exchangeAt: '2025-01-15T03:59:59.000Z',
    ageSeconds,
    lastPrice: price,
    changePct24H: '1.25',
    volume24H: '12345.67',
    bid: price,
    ask: price,
    spreadPct: '0.0005',
    fundingRate: perp ? '0.0001' : null,
    nextFundingAt: perp ? '2025-01-15T08:00:00.000Z' : null,
    instrument: {
      instrumentId: symbol,
      minSize: '0.00001',
      lotSize: '0.00001',
      tickSize: '0.1',
      contractValue: perp ? '0.01' : null,
      maxLeverage: perp ? '125' : null,
    },
    indicators: {
      trend: 'up',
      trend15M: 'up',
      rsi: 58.2,
      rsiState: 'neutral',
      macdDirection: 'up',
      macdDirection15M: 'up',
      volumeStrength: 'strong',
      volatilityPct: 1.2,
      candleBehavior: 'bullish',
      screeningState,
    },
    candles: CANDLES,
    candles15M: CANDLES,
    bids: [{ price, size: '0.5' }],
    asks: [{ price, size: '0.4' }],
    detail:
      status === MarketScannerRowStatus.stale
        ? 'Last tick is older than the freshness limit.'
        : null,
    setupScores: null,
    candidateId: null,
    candidateStatus: null,
    entryResearch: null,
  };
}

function deadRow(
  symbol: string,
  marketType: MarketScannerRowMarketType,
): MarketScannerRow {
  return {
    symbol,
    marketType,
    status: MarketScannerRowStatus.unavailable,
    observedAt: null,
    exchangeAt: null,
    ageSeconds: null,
    lastPrice: null,
    changePct24H: null,
    volume24H: null,
    bid: null,
    ask: null,
    spreadPct: null,
    fundingRate: null,
    nextFundingAt: null,
    instrument: null,
    indicators: null,
    candles: [],
    candles15M: [],
    bids: [],
    asks: [],
    detail: 'Instrument not returned by the provider.',
    setupScores: null,
    candidateId: null,
    candidateStatus: null,
    entryResearch: null,
  };
}

const SPOT = MarketScannerRowMarketType.spot;
const PERP = MarketScannerRowMarketType.futures;
const { fresh, stale } = MarketScannerRowStatus;

/** Two fresh, two stale and two unavailable, split across spot and perpetual. */
const SCANNER_ROWS: MarketScannerRow[] = [
  liveRow(
    'BTC-USDT',
    SPOT,
    fresh,
    3.2,
    '43210.5',
    MarketIndicatorsScreeningState.watch,
  ),
  liveRow(
    'ETH-USDT',
    SPOT,
    stale,
    412,
    '2310.2',
    MarketIndicatorsScreeningState.no_alignment,
  ),
  deadRow('LTC-USDT', SPOT),
  liveRow(
    'BTC-USDT-SWAP',
    PERP,
    fresh,
    1.8,
    '43215.0',
    MarketIndicatorsScreeningState.watch,
  ),
  liveRow(
    'ETH-USDT-SWAP',
    PERP,
    stale,
    95,
    '2311.0',
    MarketIndicatorsScreeningState.no_alignment,
  ),
  deadRow('SOL-USDT-SWAP', PERP),
];

const SCANNER_OK: MarketScannerResponse = {
  provider: 'OKX (fixture)',
  scannedAt: '2025-01-15T04:00:00.000Z',
  rows: SCANNER_ROWS,
};

/** The same six instruments, every one unavailable: the provider cannot be reached. */
const SCANNER_OUTAGE: MarketScannerResponse = {
  ...SCANNER_OK,
  rows: SCANNER_ROWS.map((row) => ({
    ...deadRow(row.symbol, row.marketType),
    detail: 'Provider unreachable.',
  })),
};

/** Fund of 1000 split 600 spot and 400 futures; no positions; two dry-run bots with the gate closed. */
const PORTFOLIO: PortfolioSummary = {
  fundId: 1,
  currency: 'USDT',
  initialBalance: '1000.00',
  equity: '1000.00',
  allocations: [
    {
      marketType: AllocationBalanceMarketType.spot,
      initialBalance: '600.00',
      balance: '600.00',
      collateral: '0.00',
      availableBalance: '600.00',
      exposure: '0.00',
    },
    {
      marketType: AllocationBalanceMarketType.futures,
      initialBalance: '400.00',
      balance: '400.00',
      collateral: '0.00',
      availableBalance: '400.00',
      exposure: '0.00',
    },
  ],
  positions: [],
  bots: [
    {
      botId: 'spot-dry-run',
      status: 'idle',
      dryRun: true,
      entryGate: 'closed',
      reconciliation: 'reconciled',
      savedAt: '2025-01-15T03:59:00.000Z',
    },
    {
      botId: 'futures-dry-run',
      status: 'idle',
      dryRun: true,
      entryGate: 'closed',
      reconciliation: 'reconciled',
      savedAt: '2025-01-15T03:59:00.000Z',
    },
  ],
  fees: '0.00',
  funding: '0.00',
  realizedPnl: '0.00',
  unrealizedPnl: '0.00',
  ledgerVerified: true,
  ledgerEvents: 2,
  updatedAt: '2025-01-15T04:00:00.000Z',
};

const LEDGER: LedgerList = {
  total: 2,
  events: [
    {
      seq: 2,
      occurredAt: '2025-01-15T03:00:01.000Z',
      eventType: 'fund_allocation',
      marketType: LedgerEventMarketType.futures,
      amount: '400.00',
      idempotencyKey: 'fixture-allocation-futures',
      reference: 'fixture-futures',
      details: { note: 'synthetic fixture' },
      hash: 'b'.repeat(64),
    },
    {
      seq: 1,
      occurredAt: '2025-01-15T03:00:00.000Z',
      eventType: 'fund_allocation',
      marketType: LedgerEventMarketType.spot,
      amount: '600.00',
      idempotencyKey: 'fixture-allocation-spot',
      reference: 'fixture-spot',
      details: { note: 'synthetic fixture' },
      hash: 'a'.repeat(64),
    },
  ],
};

const VERIFY_INTACT: LedgerVerification = {
  ok: true,
  eventsChecked: 2,
  firstSeq: 1,
  lastSeq: 2,
  headHash: 'c'.repeat(64),
  firstBreakSeq: null,
  reason: null,
  durationMs: 1.5,
  verifiedAt: '2025-01-15T04:00:02.000Z',
};

const VERIFY_BROKEN: LedgerVerification = {
  ...VERIFY_INTACT,
  ok: false,
  firstBreakSeq: 2,
  reason: 'hash_mismatch',
};

// ---------------------------------------------------------------------------
// Fixture plumbing
// ---------------------------------------------------------------------------

const json = (route: Route, status: number, body: unknown) =>
  route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });

const pathIs = (name: string) => (url: URL) => url.pathname === name;

interface PresentOptions {
  scanner?: { status: number; body: unknown };
  verify?: LedgerVerification;
  /** Receives one entry per request to the verify route, so on-demand use can be checked. */
  verifyHits?: number[];
}

/**
 * Presents the signed-in app with synthetic data. Registered in this order: the catch-all
 * first, so every specific route below takes precedence and nothing reaches the real backend.
 */
async function presentSignedIn(page: Page, options: PresentOptions = {}) {
  await page.route(
    (url) => url.pathname.startsWith('/api/'),
    (route) =>
      json(route, 404, {
        error: 'fixture_not_mocked',
        message: 'This request is not part of the synthetic fixture.',
        correlationId: 'fixture',
      } satisfies ErrorResponse),
  );
  await page.route(pathIs('/api/auth/user'), (route) =>
    json(route, 200, {
      user: {
        id: 'fixture-user-0001',
        username: 'fixture-user',
        firstName: 'Fixture',
        lastName: 'User',
        profileImageUrl: null,
      },
    }),
  );
  const scanner = options.scanner ?? { status: 200, body: SCANNER_OK };
  await page.route(pathIs('/api/market/scanner'), (route) =>
    json(route, scanner.status, scanner.body),
  );
  await page.route(pathIs('/api/portfolio/summary'), (route) =>
    json(route, 200, PORTFOLIO),
  );
  await page.route(pathIs('/api/portfolio/ledger'), (route) =>
    json(route, 200, LEDGER),
  );
  await page.route(pathIs('/api/portfolio/ledger/verify'), (route) => {
    options.verifyHits?.push(Date.now());
    return json(route, 200, options.verify ?? VERIFY_INTACT);
  });
}

/** The keys of the scanner rows currently listed, for example "BTC-USDT-spot". */
const rowKeys = (page: Page) =>
  page
    .locator('[data-testid^="row-scanner-"]')
    .evaluateAll((els) =>
      els.map((el) =>
        (el.getAttribute('data-testid') ?? '').replace('row-scanner-', ''),
      ),
    );

async function expectNoPageOverflow(page: Page) {
  const widths = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }));
  expect(widths.scroll, 'page must not scroll sideways').toBeLessThanOrEqual(
    widths.client,
  );
}

/** Actions that would change money, approve a trade or reset state. None may exist. */
const FORBIDDEN_CONTROL =
  /order|approve|reset|buy|sell|place|submit|start|halt|trade|enable|entry/i;

async function expectReadOnly(page: Page) {
  await expect(
    page.getByRole('button', { name: FORBIDDEN_CONTROL }),
  ).toHaveCount(0);
  await expect(page.locator('form, input, select, textarea')).toHaveCount(0);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('a signed-out visitor never sees Phase 2 data', () => {
  for (const path of ['/market-scanner', '/portfolio']) {
    test(`${path} shows only the sign-in screen`, async ({ page }) => {
      const dataCalls: string[] = [];
      page.on('request', (request) => {
        const { pathname } = new URL(request.url());
        if (/^\/api\/(market|portfolio)/.test(pathname))
          dataCalls.push(pathname);
      });

      await page.goto(path);

      await expect(page.getByTestId('signin-screen')).toBeVisible();
      await expect(page.getByTestId('page-market-scanner')).toHaveCount(0);
      await expect(page.getByTestId('page-portfolio')).toHaveCount(0);
      await expect(page.getByTestId('text-equity')).toHaveCount(0);
      await expect(page.getByTestId('button-verify-ledger')).toHaveCount(0);
      await page.waitForLoadState('networkidle');
      expect(dataCalls, 'no market or portfolio data is requested').toEqual([]);
    });
  }
});

test.describe('Market Scanner (synthetic fixtures)', () => {
  test('lists six rows with fresh, stale and unavailable statuses', async ({
    page,
  }, testInfo) => {
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    await expect(page.getByTestId('page-market-scanner')).toBeVisible();

    await expect(page.locator('[data-testid^="row-scanner-"]')).toHaveCount(6);
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '2 fresh',
    );
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '2 stale',
    );
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '2 unavailable',
    );
    await expect(page.getByTestId('status-row-BTC-USDT-spot')).toContainText(
      'fresh',
    );
    await expect(page.getByTestId('status-row-ETH-USDT-spot')).toContainText(
      'stale',
    );
    await expect(
      page.getByTestId('status-row-SOL-USDT-SWAP-futures'),
    ).toContainText('unavailable');
    await expect(
      page.getByRole('alert').filter({ hasText: 'Market data outage' }),
    ).toHaveCount(0);
    await expectNoPageOverflow(page);
    await testInfo.attach('scanner-fixture-six-rows', {
      body: await page.screenshot(),
      contentType: 'image/png',
    });
  });

  test('filters to All, Spot and Perpetual', async ({ page }) => {
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    await expect(page.getByTestId('page-market-scanner')).toBeVisible();

    await page.getByTestId('button-filter-spot').click();
    await expect(page.getByTestId('button-filter-spot')).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await expect
      .poll(() => rowKeys(page))
      .toEqual(['BTC-USDT-spot', 'ETH-USDT-spot', 'LTC-USDT-spot']);

    await page.getByTestId('button-filter-futures').click();
    await expect
      .poll(() => rowKeys(page))
      .toEqual([
        'BTC-USDT-SWAP-futures',
        'ETH-USDT-SWAP-futures',
        'SOL-USDT-SWAP-futures',
      ]);

    await page.getByTestId('button-filter-all').click();
    await expect.poll(() => rowKeys(page)).toHaveLength(6);
  });

  test('expands a row to its screening, evidence and stale warning', async ({
    page,
  }) => {
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    const expand = page.getByTestId('button-expand-ETH-USDT-SWAP-futures');

    await expand.click();
    await expect(expand).toHaveAttribute('aria-expanded', 'true');
    await expect(
      page.getByText('Legacy indicators (diagnostic only)'),
    ).toBeVisible();
    await expect(page.getByText('Order book top')).toBeVisible();
    await expect(
      page.getByText('Last tick is older than the freshness limit.'),
    ).toBeVisible();

    await expand.click();
    await expect(expand).toHaveAttribute('aria-expanded', 'false');
    await expect(
      page.getByText('Legacy indicators (diagnostic only)'),
    ).toHaveCount(0);
  });

  test('shows an explicit outage when every instrument is unavailable', async ({
    page,
  }) => {
    await presentSignedIn(page, {
      scanner: { status: 200, body: SCANNER_OUTAGE },
    });
    await page.goto('/market-scanner');

    await expect(
      page.getByRole('alert').filter({ hasText: 'Market data outage' }),
    ).toBeVisible();
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '0 fresh',
    );
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '6 unavailable',
    );
    await expect(page.locator('[data-testid^="row-scanner-"]')).toHaveCount(6);
  });

  test('shows an error note with the correlation ID when the scan fails', async ({
    page,
  }) => {
    await presentSignedIn(page, {
      scanner: {
        status: 503,
        body: {
          error: 'market_data_unavailable',
          message: 'Market data is unavailable right now.',
          correlationId: 'fixture-corr-0503',
        } satisfies ErrorResponse,
      },
    });
    await page.goto('/market-scanner');

    // The client retries a server error twice before it gives up.
    const alert = page
      .getByRole('alert')
      .filter({ hasText: 'Scanner data could not be loaded' });
    await expect(alert).toBeVisible({ timeout: 15_000 });
    await expect(alert).toContainText('Market data is unavailable right now.');
    await expect(page.getByTestId('text-error-correlation-id')).toHaveText(
      'fixture-corr-0503',
    );
    await expect(page.locator('[data-testid^="row-scanner-"]')).toHaveCount(0);
  });

  test('is read-only and has no order or approval control', async ({
    page,
  }) => {
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    await expect(page.getByTestId('page-market-scanner')).toBeVisible();
    await expectReadOnly(page);
  });
});

test.describe('Portfolio (synthetic fixtures)', () => {
  test('shows a 1000 fund split 600 spot and 400 futures, no positions, two gate-closed dry-run bots', async ({
    page,
  }) => {
    await presentSignedIn(page);
    await page.goto('/portfolio');
    await expect(page.getByTestId('page-portfolio')).toBeVisible();

    await expect(page.getByTestId('text-equity')).toContainText('1,000.00');
    await expect(page.getByTestId('card-allocation-spot')).toContainText(
      '600.00',
    );
    await expect(page.getByTestId('card-allocation-futures')).toContainText(
      '400.00',
    );
    await expect(page.getByTestId('list-positions-empty')).toBeVisible();
    await expect(page.getByTestId('list-positions')).toHaveCount(0);

    const bots = page.getByTestId('list-bots').getByRole('listitem');
    await expect(bots).toHaveCount(2);
    for (let i = 0; i < 2; i++) {
      await expect(bots.nth(i)).toContainText('entryGate');
      await expect(bots.nth(i)).toContainText('closed');
      await expect(bots.nth(i)).toContainText('dryRun');
    }

    await expect(page.getByTestId('row-ledger-1')).toBeVisible();
    await expect(page.getByTestId('row-ledger-2')).toBeVisible();
    await expect(page.getByTestId('status-ledger-verified')).toHaveText(
      'Ledger chain verified',
    );
    await expectNoPageOverflow(page);
  });

  test('runs Verify Ledger on demand and reports an intact chain', async ({
    page,
  }) => {
    const verifyHits: number[] = [];
    await presentSignedIn(page, { verify: VERIFY_INTACT, verifyHits });
    await page.goto('/portfolio');
    await expect(page.getByTestId('page-portfolio')).toBeVisible();
    await expect(page.getByTestId('row-ledger-1')).toBeVisible();
    expect(verifyHits, 'the chain is not checked until asked').toHaveLength(0);

    await page.getByTestId('button-verify-ledger').click();
    const result = page.getByTestId('result-ledger-verification');
    await expect(result).toHaveAttribute('data-ok', 'true');
    await expect(result).toContainText('Chain intact');
    await expect(result).toContainText('#1 to #2');
    expect(verifyHits).toHaveLength(1);
  });

  test('reports a broken chain with the first break', async ({ page }) => {
    await presentSignedIn(page, { verify: VERIFY_BROKEN });
    await page.goto('/portfolio');
    await expect(page.getByTestId('page-portfolio')).toBeVisible();

    await page.getByTestId('button-verify-ledger').click();
    const result = page.getByTestId('result-ledger-verification');
    await expect(result).toHaveAttribute('data-ok', 'false');
    await expect(result).toContainText('Chain broken');
    await expect(result).toContainText('hash_mismatch (at #2)');
    await expect(result).toHaveAttribute('role', 'alert');
  });

  test('is read-only and has no order, approval or reset control', async ({
    page,
  }, testInfo) => {
    await presentSignedIn(page);
    await page.goto('/portfolio');
    await expect(page.getByTestId('page-portfolio')).toBeVisible();
    await expectReadOnly(page);
    await expect(
      page.getByRole('button', { name: 'Verify Ledger' }),
    ).toBeVisible();
    await testInfo.attach('portfolio-fixture', {
      body: await page.screenshot({ fullPage: true }),
      contentType: 'image/png',
    });
  });
});
