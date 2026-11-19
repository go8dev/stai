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
  type CommitteeOverview,
  type ErrorResponse,
  type LedgerList,
  type LedgerVerification,
  type MtfDirectionalEvidence,
  type MtfIndicatorSnapshot,
  type MtfInstrumentAnalysis,
  type MtfMarketIntelligenceResponse,
  type MtfOpportunity,
  type MtfQuoteStatus,
  type MtfZone,
  type MarketScannerResponse,
  type MarketScannerRow,
  type ProposalCenterOverview,
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
  deadRow('SOL-USDT', SPOT),
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

const MTF_WEIGHTS = { '1d': 15, '4h': 25, '1h': 35, '15m': 25 } as const;
const MTF_INTERVAL_MS = {
  '1d': 24 * 60 * 60_000,
  '4h': 4 * 60 * 60_000,
  '1h': 60 * 60_000,
  '15m': 15 * 60_000,
} as const;

function mtfCandles(
  timeframe: keyof typeof MTF_WEIGHTS,
  price: number,
): CandlePoint[] {
  const intervalMs = MTF_INTERVAL_MS[timeframe];
  const count = timeframe === '1d' ? 31 : 30;
  const start = {
    '1d': Date.parse('2024-12-16T00:00:00.000Z'),
    '4h': Date.parse('2025-01-10T00:00:00.000Z'),
    '1h': Date.parse('2025-01-14T00:00:00.000Z'),
    '15m': Date.parse('2025-01-15T00:00:00.000Z'),
  }[timeframe];
  return Array.from({ length: count }, (_, index) => {
    const close = price - 1 + index * 0.05;
    return {
      openedAt: new Date(start + index * intervalMs).toISOString(),
      open: (close - 0.05).toFixed(3),
      high: (close + 0.2).toFixed(3),
      low: (close - 0.2).toFixed(3),
      close: close.toFixed(3),
      volume: '12.5',
      quoteVolume: (close * 12.5).toFixed(2),
      complete: true,
    };
  });
}

function mtfEvidence(
  status: 'complete' | 'stale' | 'insufficient',
): MtfDirectionalEvidence {
  const components = (
    Object.entries(MTF_WEIGHTS) as [keyof typeof MTF_WEIGHTS, number][]
  ).map(([timeframe, weight]) => {
    const neutral = timeframe === '15m';
    const perIndicator = weight / 2;
    const direction: MtfDirectionalEvidence['components'][number]['smaDirection'] =
      status === 'insufficient' ? 'neutral' : neutral ? 'neutral' : 'bullish';
    return {
      timeframe,
      weight,
      smaDirection: direction,
      smaPoints: status === 'insufficient' ? null : perIndicator,
      rsiDirection: direction,
      rsiPoints: status === 'insufficient' ? null : perIndicator,
    };
  });
  return {
    strategyVersion: 'stai-mtf-balanced-v1',
    status,
    bullishScore: status === 'insufficient' ? null : 75,
    bearishScore: status === 'insufficient' ? null : 0,
    neutralPoints: status === 'insufficient' ? null : 25,
    classification:
      status === 'insufficient' ? 'insufficient' : 'strong_bullish',
    components,
    disagreementReasons: [],
    note:
      status === 'stale'
        ? 'Last-known diagnostic evidence; candle data is stale.'
        : 'Synthetic completed-candle evidence for browser verification.',
  };
}

function mtfZones(price: number): MtfZone[] {
  const pivotAt = '2025-01-14T00:00:00.000Z';
  const confirmedAt = '2025-01-14T01:00:00.000Z';
  return [
    {
      id: 'zone-1h-support',
      sourceTimeframe: '1h',
      kind: 'support',
      lower: price - 1.15,
      upper: price - 0.95,
      pivotAt,
      confirmedAt,
      atrAtCalculation: 8,
      independentReactions: 2,
      state: 'tested',
      distanceFromPrice: 0.95,
      confluenceTimeframes: ['4h'],
      isPriorExtreme: false,
      detail: 'Synthetic confirmed 1H support fixture.',
    },
    {
      id: 'zone-4h-resistance',
      sourceTimeframe: '4h',
      kind: 'resistance',
      lower: price + 0.45,
      upper: price + 0.65,
      pivotAt: '2025-01-13T20:00:00.000Z',
      confirmedAt: '2025-01-14T00:00:00.000Z',
      atrAtCalculation: 10,
      independentReactions: 2,
      state: 'active',
      distanceFromPrice: 0.45,
      confluenceTimeframes: ['1h'],
      isPriorExtreme: false,
      detail: 'Synthetic confirmed 4H resistance fixture.',
    },
    {
      id: 'zone-1d-prior-support',
      sourceTimeframe: '1d',
      kind: 'support',
      lower: price - 2.15,
      upper: price - 1.95,
      pivotAt: '2025-01-13T00:00:00.000Z',
      confirmedAt: '2025-01-14T00:00:00.000Z',
      atrAtCalculation: null,
      independentReactions: 1,
      state: 'active',
      distanceFromPrice: 1.95,
      confluenceTimeframes: [],
      isPriorExtreme: true,
      detail: 'Synthetic prior completed daily extreme.',
    },
  ];
}

function mtfInstrument(
  symbol: string,
  marketType: 'spot' | 'futures',
  status: MtfQuoteStatus,
  lastPrice: number,
): MtfInstrumentAnalysis {
  const available = status !== 'unavailable';
  const evidenceStatus =
    status === 'unavailable'
      ? 'insufficient'
      : status === 'stale'
        ? 'stale'
        : 'complete';
  const evidence = mtfEvidence(evidenceStatus);
  const timeframes: MtfIndicatorSnapshot[] = (
    Object.keys(MTF_WEIGHTS) as (keyof typeof MTF_WEIGHTS)[]
  ).map((timeframe) => {
    const frameStatus = !available
      ? 'unavailable'
      : status === 'stale' && timeframe === '1d'
        ? 'stale'
        : 'fresh';
    const candles = available ? mtfCandles(timeframe, lastPrice) : [];
    return {
      timeframe,
      status: frameStatus,
      latestCompletedAt: available
        ? new Date(
            Date.parse(candles.at(-1)!.openedAt) + MTF_INTERVAL_MS[timeframe],
          ).toISOString()
        : null,
      close: available ? candles.at(-1)!.close : null,
      rsi14: available ? 56.2 : null,
      sma20: available ? lastPrice - 0.5 : null,
      sma50: available ? lastPrice - 1 : null,
      atr14: available ? 8 : null,
      smaDirection: available ? 'bullish' : 'neutral',
      rsiDirection: available ? 'bullish' : 'neutral',
      candles,
      expectedCandles: timeframe === '1d' ? 240 : 240,
      actualCandles: candles.length,
      gapCount: 0,
      detail:
        frameStatus === 'stale'
          ? 'Most recent expected daily candle is missing.'
          : null,
    };
  });
  const zones = available ? mtfZones(lastPrice) : [];
  const quoteAt = '2025-01-15T04:00:00.000Z';
  const opportunity: MtfOpportunity = !available
    ? {
        state: 'insufficient_data',
        direction: null,
        anchorId: null,
        anchorAt: null,
        signalAt: null,
        expiresAt: null,
        researchRuleVersion: 'stai-mtf-research-opportunity-v1',
        detail: 'Market data unavailable; no opportunity evaluated.',
        plan: null,
      }
    : status === 'stale'
      ? {
          state: 'insufficient_data',
          direction: null,
          anchorId: null,
          anchorAt: null,
          signalAt: null,
          expiresAt: null,
          researchRuleVersion: 'stai-mtf-research-opportunity-v1',
          detail:
            'Stale timeframe data prevents current opportunity evaluation.',
          plan: null,
        }
      : marketType === 'futures' && symbol.startsWith('BTC')
        ? {
            state: 'indicative_setup_ready',
            direction: 'long',
            anchorId: 'fixture-anchor-btc-futures',
            anchorAt: '2025-01-15T03:00:00.000Z',
            signalAt: '2025-01-15T04:00:00.000Z',
            expiresAt: '2025-01-15T05:00:00.000Z',
            researchRuleVersion: 'stai-mtf-research-opportunity-v1',
            detail: 'Synthetic closed-candle confirmation; indicative only.',
            plan: {
              direction: 'long',
              entryZoneLower: lastPrice - 1.15,
              entryZoneUpper: lastPrice + 0.2,
              trigger: 'A completed 15M candle confirms the pullback anchor.',
              entryReference: lastPrice,
              stopReference: lastPrice - 1.15,
              targetReference: lastPrice + 0.45,
              grossRewardRisk: 0.4,
              estimatedNetRewardRisk: 0.3,
              supportingZoneIds: ['zone-1h-support', 'zone-4h-resistance'],
              opposingEvidence: [],
              signalAt: '2025-01-15T04:00:00.000Z',
              expiresAt: '2025-01-15T05:00:00.000Z',
              priceBasis: 'indicative_only',
              costNote: 'Synthetic fixture; no executable plan or order.',
            },
          }
        : {
            state: 'waiting_for_pullback',
            direction: 'long',
            anchorId: null,
            anchorAt: null,
            signalAt: null,
            expiresAt: null,
            researchRuleVersion: 'stai-mtf-research-opportunity-v1',
            detail: 'Directional research evidence; waiting for pullback.',
            plan: null,
          };
  return {
    symbol: `${symbol.startsWith('BTC') ? 'BTC' : symbol.startsWith('ETH') ? 'ETH' : 'SOL'}/USDT`,
    marketType,
    instrumentId: `${symbol.replace('-SWAP', '')}${marketType === 'futures' ? '-SWAP' : ''}`,
    quote: {
      lastPrice: available ? lastPrice : null,
      changePct24H: available ? 1.25 : null,
      volume24H: available ? 12345.67 : null,
      exchangeAt: available ? quoteAt : null,
      observedAt: quoteAt,
      status,
    },
    timeframes,
    evidence,
    btcContext: symbol.startsWith('BTC') ? null : mtfEvidence('complete'),
    zones,
    nearestSupport:
      zones.find(
        (zone) => zone.kind === 'support' && zone.sourceTimeframe === '1h',
      ) ?? null,
    nearestResistance:
      zones.find(
        (zone) => zone.kind === 'resistance' && zone.sourceTimeframe === '4h',
      ) ?? null,
    opportunity,
    committeeStatus: 'Persisted history only; no committee review triggered.',
    observedAt: quoteAt,
  };
}

const MTF_ROWS: MtfMarketIntelligenceResponse = {
  provider: 'OKX',
  strategyVersion: 'stai-mtf-balanced-v1',
  observedAt: '2025-01-15T04:00:00.000Z',
  instruments: [
    mtfInstrument('BTC-USDT', 'spot', 'fresh', 43210.5),
    mtfInstrument('ETH-USDT', 'spot', 'stale', 2310.2),
    mtfInstrument('SOL-USDT', 'spot', 'unavailable', 142.5),
    mtfInstrument('BTC-USDT-SWAP', 'futures', 'fresh', 43215),
    mtfInstrument('ETH-USDT-SWAP', 'futures', 'stale', 2311),
    mtfInstrument('SOL-USDT-SWAP', 'futures', 'unavailable', 142.7),
  ],
  limitations: ['Synthetic browser test fixtures; not market advice.'],
};

const MTF_OUTAGE: MtfMarketIntelligenceResponse = {
  ...MTF_ROWS,
  instruments: MTF_ROWS.instruments.map((item) =>
    mtfInstrument(
      item.symbol.replace('/', '-') +
        (item.marketType === 'futures' ? '-SWAP' : ''),
      item.marketType,
      'unavailable',
      0,
    ),
  ),
};

const COMMITTEE_OVERVIEW: CommitteeOverview = {
  roles: [],
  runs: [],
  paidAutomationEnabled: false,
  manualPaidRunsEnabled: false,
  entryGate: 'closed',
  benchmarkState: 'not_started',
  limitsStatus: 'within_limits',
  nextStep: 'No action requested.',
};

const PROPOSAL_OVERVIEW: ProposalCenterOverview = {
  candidates: [],
  proposals: [],
  paidCommitteeEnabled: false,
  ownerApprovalRequired: true,
  strategyThreshold: 60,
  gateStatus: 'closed',
  gateMessage: 'Closed in fixture.',
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
  scannerHits?: number[];
  intelligence?: { status: number; body: unknown };
  intelligenceDelayMs?: number;
  intelligenceHits?: number[];
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
  await page.route(pathIs('/api/market/scanner'), (route) => {
    options.scannerHits?.push(Date.now());
    return json(route, scanner.status, scanner.body);
  });
  const intelligence = options.intelligence ?? {
    status: 200,
    body: MTF_ROWS,
  };
  await page.route(pathIs('/api/market/intelligence'), async (route) => {
    options.intelligenceHits?.push(Date.now());
    if (options.intelligenceDelayMs) {
      await new Promise((resolve) =>
        setTimeout(resolve, options.intelligenceDelayMs),
      );
    }
    return json(route, intelligence.status, intelligence.body);
  });
  await page.route(pathIs('/api/committee'), (route) =>
    json(route, 200, COMMITTEE_OVERVIEW),
  );
  await page.route(pathIs('/api/proposal-center'), (route) =>
    json(route, 200, PROPOSAL_OVERVIEW),
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
    .locator('[data-testid^="row-market-"]')
    .evaluateAll((els) =>
      els.map((el) =>
        (el.getAttribute('data-testid') ?? '').replace('row-market-', ''),
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

async function expectNoTradingActions(page: Page) {
  await expect(
    page.getByRole('button', {
      name: /^(buy|sell|place order|place trade|approve|submit proposal|execute order|start bot|run committee|enable automation)$/i,
    }),
  ).toHaveCount(0);
  await expect(page.locator('form')).toHaveCount(0);
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

test.describe('Market Scanner · MTF research UI (synthetic contract fixtures)', () => {
  test('renders six joined instruments and explicit fresh, stale and unavailable data', async ({
    page,
  }, testInfo) => {
    const scannerHits: number[] = [];
    const intelligenceHits: number[] = [];
    await presentSignedIn(page, { scannerHits, intelligenceHits });
    await page.goto('/market-scanner');
    await expect(page.getByTestId('page-market-scanner')).toBeVisible();

    const rows = page.locator('[data-testid^="row-market-"]');
    await expect(rows).toHaveCount(6);
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '2 fresh quotes',
    );
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '2 stale quotes',
    );
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '2 unavailable',
    );
    await expect(page.getByTestId('row-market-BTC-USDT-spot')).toHaveAttribute(
      'data-freshness',
      'fresh',
    );
    await expect(page.getByTestId('row-market-ETH-USDT-spot')).toHaveAttribute(
      'data-freshness',
      'stale',
    );
    await expect(
      page.getByTestId('row-market-SOL-USDT-SWAP-futures'),
    ).toHaveAttribute('data-freshness', 'unavailable');
    expect(scannerHits).toHaveLength(1);
    expect(intelligenceHits).toHaveLength(1);
    await expectNoPageOverflow(page);
    await testInfo.attach('mtf-screener-six-instrument-fixture', {
      body: await page.screenshot(),
      contentType: 'image/png',
    });
  });

  test('searches, filters, sorts and selects instruments without losing market identity', async ({
    page,
  }) => {
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    await expect(page.locator('[data-testid^="row-market-"]')).toHaveCount(6);

    await page.getByTestId('filter-market-type').selectOption('futures');
    await expect(page.locator('[data-testid^="row-market-"]')).toHaveCount(3);
    await page.getByTestId('input-symbol-search').fill('ETH');
    await expect.poll(() => rowKeys(page)).toEqual(['ETH-USDT-SWAP-futures']);

    await page.getByTestId('input-symbol-search').fill('');
    await page.getByTestId('sort-lastPrice').click();
    await page.getByTestId('sort-lastPrice').click();
    await expect
      .poll(() => rowKeys(page))
      .toEqual([
        'BTC-USDT-SWAP-futures',
        'ETH-USDT-SWAP-futures',
        'SOL-USDT-SWAP-futures',
      ]);

    await page.getByTestId('filter-market-type').selectOption('all');
    await page.getByTestId('filter-direction').selectOption('long');
    await expect(page.locator('[data-testid^="row-market-"]')).toHaveCount(2);
    await page.getByTestId('filter-direction').selectOption('all');
    await page.getByTestId('filter-market-type').selectOption('spot');
    await page.getByTestId('input-symbol-search').fill('SOL');
    await expect.poll(() => rowKeys(page)).toEqual(['SOL-USDT-spot']);

    await page.getByTestId('button-reset-filters').click();
    const selected = page.getByTestId('row-market-BTC-USDT-SWAP-futures');
    await selected.click();
    await expect(selected).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByTestId('market-detail')).toContainText(
      'BTC-USDT-SWAP',
    );
  });

  test('shows selected timeframe candles and confirmed support/resistance levels', async ({
    page,
  }) => {
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    const btc = page.getByTestId('row-market-BTC-USDT-spot');
    await btc.click();

    await page.getByTestId('chart-timeframe-15M').click();
    await expect(page.getByTestId('chart-timeframe-15M')).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    await expect(page.getByTestId('timeframe-15M')).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    await expect(
      page.getByRole('img', {
        name: 'BTC-USDT 15M candlestick chart from OKX',
      }),
    ).toBeVisible();

    await page.getByTestId('chart-timeframe-1H').click();
    await expect(page.getByTestId('chart-zone-zone-1h-support')).toBeVisible();
    await page.getByTestId('chart-zone-zone-1h-support').click();
    await expect(page.getByText(/2 independent reactions/)).toBeVisible();

    await page.getByTestId('tab-structure').click();
    await expect(page.getByTestId('tab-structure')).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await expect(
      page.getByTestId('row-market-BTC-USDT-spot').getByText(/S .* \/ R/),
    ).toBeVisible();
  });

  test('Committee tab shows persisted status only and never invokes AI or trading actions', async ({
    page,
  }) => {
    const writeRequests: string[] = [];
    const aiRequests: string[] = [];
    page.on('request', (request) => {
      const url = new URL(request.url());
      if (!url.pathname.startsWith('/api/')) return;
      if (request.method() !== 'GET') {
        writeRequests.push(`${request.method()} ${url.pathname}`);
      }
      if (/\/api\/(ai|committee\/(run|submit))/i.test(url.pathname)) {
        aiRequests.push(`${request.method()} ${url.pathname}`);
      }
    });
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    await page.getByTestId('tab-committee').click();
    await expect(page.getByTestId('tab-committee')).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await expect(page.getByText(/existing runs 0/)).toBeVisible();
    await expect(page.getByText(/Paid automation disabled/)).toBeVisible();
    await expect(page.getByText(/manual paid runs disabled/)).toBeVisible();
    await expect(page.getByText(/Entry gate closed/)).toBeVisible();
    await expect(
      page.getByText(/new MTF committee submissions disabled/),
    ).toBeVisible();
    await expectNoTradingActions(page);
    expect(writeRequests).toEqual([]);
    expect(aiRequests).toEqual([]);
  });

  test('shows a loading state while the MTF contract request is pending', async ({
    page,
  }) => {
    await presentSignedIn(page, { intelligenceDelayMs: 700 });
    await page.goto('/market-scanner');
    await expect(page.locator('[aria-busy="true"]')).toBeVisible();
    await expect(page.locator('[data-testid^="row-market-"]')).toHaveCount(6);
  });

  test('reports MTF request errors with correlation ID while preserving scanner rows', async ({
    page,
  }) => {
    await presentSignedIn(page, {
      intelligence: {
        status: 503,
        body: {
          error: 'market_data_unavailable',
          message: 'MTF market intelligence is unavailable.',
          correlationId: 'fixture-mtf-0503',
        } satisfies ErrorResponse,
      },
    });
    await page.goto('/market-scanner');
    const alert = page
      .getByRole('alert')
      .filter({ hasText: 'Market intelligence could not be loaded' });
    await expect(alert).toBeVisible({ timeout: 15_000 });
    await expect(alert).toContainText(
      'MTF market intelligence is unavailable.',
    );
    await expect(page.getByTestId('text-error-correlation-id')).toHaveText(
      'fixture-mtf-0503',
    );
    await expect(page.locator('[data-testid^="row-market-"]')).toHaveCount(6);
  });

  test('shows an explicit full outage and keeps unavailable instruments visible', async ({
    page,
  }) => {
    await presentSignedIn(page, {
      scanner: { status: 200, body: SCANNER_OUTAGE },
      intelligence: { status: 200, body: MTF_OUTAGE },
    });
    await page.goto('/market-scanner');
    await expect(
      page.getByRole('alert').filter({ hasText: 'Market data outage' }),
    ).toBeVisible();
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '0 fresh quotes',
    );
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '0 stale quotes',
    );
    await expect(page.getByTestId('text-freshness-counts')).toContainText(
      '6 unavailable',
    );
    await expect(page.locator('[data-testid^="row-market-"]')).toHaveCount(6);
    await expect(
      page.locator(
        '[data-testid^="row-market-"][data-freshness="unavailable"]',
      ),
    ).toHaveCount(6);
  });

  test('is read-only while allowing research filters and tab navigation', async ({
    page,
  }) => {
    await presentSignedIn(page);
    await page.goto('/market-scanner');
    await expect(page.getByTestId('page-market-scanner')).toBeVisible();
    await expectNoTradingActions(page);
    await expect(page.getByTestId('input-symbol-search')).toBeVisible();
    await expect(page.getByTestId('filter-market-type')).toBeVisible();
    await expect(page.getByTestId('filter-timeframe')).toBeVisible();
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
