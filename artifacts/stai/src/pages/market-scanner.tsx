import { useMemo, useState } from 'react';
import { ChevronRight, RefreshCw, Radio } from 'lucide-react';
import {
  useGetMarketScanner,
  getGetMarketScannerQueryKey,
  type MarketScannerRow,
  type BookLevel,
  type CandlePoint,
} from '@workspace/api-client-react';
import {
  formatManilaDateTime,
  formatManilaTime,
  formatUtcDateTime,
} from '@/lib/format';
import {
  fmtAge,
  fmtCompact,
  fmtFixed,
  fmtPct,
  fmtPrice,
  signTone,
} from '@/lib/display-number';
import { cn } from '@/lib/utils';
import { ErrorNote, KV, NotAvailable, PaperLabel } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';

type Filter = 'all' | 'spot' | 'futures';

const STATUS_STYLE: Record<
  string,
  { dot: string; text: string; label: string }
> = {
  fresh: { dot: 'bg-profit', text: 'text-profit', label: 'fresh' },
  stale: { dot: 'bg-warn', text: 'text-warn', label: 'stale' },
  unavailable: { dot: 'bg-loss', text: 'text-loss', label: 'unavailable' },
};

const SCREEN_LABEL: Record<string, string> = {
  watch: 'Watch',
  no_alignment: 'No alignment',
  unavailable: 'Unavailable',
};

function rowKey(r: MarketScannerRow) {
  return `${r.symbol}-${r.marketType}`;
}

function scoreSummary(scores: MarketScannerRow['setupScores']) {
  if (!scores || typeof scores !== 'object') return null;
  const sides = scores.scores;
  if (!sides || typeof sides !== 'object') return null;
  return (
    Object.entries(sides as Record<string, unknown>)
      .filter(([, setup]) => setup && typeof setup === 'object')
      .map(([side, setup]) => {
        const score = (setup as Record<string, unknown>).score;
        return `${side} ${typeof score === 'number' || typeof score === 'string' ? score : 'n/a'}/100`;
      })
      .join(' · ') || null
  );
}

function Val({ v, className }: { v: string | null; className?: string }) {
  return v === null ? (
    <NotAvailable>n/a</NotAvailable>
  ) : (
    <span className={className}>{v}</span>
  );
}

function Freshness({ row }: { row: MarketScannerRow }) {
  const s = STATUS_STYLE[row.status] ?? STATUS_STYLE.unavailable;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-mono text-[11px]',
        s.text,
      )}
      data-testid={`status-row-${rowKey(row)}`}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 rounded-full',
          s.dot,
          row.status === 'fresh' && 'animate-pulse',
        )}
        aria-hidden
      />
      {s.label}
      {row.ageSeconds !== null && (
        <span className="text-muted-foreground">{fmtAge(row.ageSeconds)}</span>
      )}
    </span>
  );
}

function Stamp({ value }: { value: string | null }) {
  if (!value) return <NotAvailable />;
  return (
    <span title={`${formatUtcDateTime(value)} UTC`}>
      {formatManilaDateTime(value)}{' '}
      <span className="text-muted-foreground">MNL</span>
    </span>
  );
}

function Book({ bids, asks }: { bids: BookLevel[]; asks: BookLevel[] }) {
  if (bids.length === 0 && asks.length === 0)
    return (
      <p className="py-3 text-xs text-muted-foreground">
        No order-book levels in this snapshot.
      </p>
    );
  const n = Math.max(bids.length, asks.length);
  return (
    <table className="w-full text-[11.5px]">
      <thead>
        <tr className="text-muted-foreground">
          <th className="eyebrow py-1 text-left font-normal">Bid size</th>
          <th className="eyebrow py-1 text-right font-normal">Bid</th>
          <th className="eyebrow py-1 pl-3 text-left font-normal">Ask</th>
          <th className="eyebrow py-1 text-right font-normal">Ask size</th>
        </tr>
      </thead>
      <tbody className="num">
        {Array.from({ length: n }).map((_, i) => (
          <tr key={i} className="border-t border-border/40">
            <td className="py-0.5 text-muted-foreground">
              {bids[i] ? fmtFixed(bids[i].size, 4) : ''}
            </td>
            <td className="py-0.5 text-right text-profit">
              {bids[i] ? fmtPrice(bids[i].price) : ''}
            </td>
            <td className="py-0.5 pl-3 text-loss">
              {asks[i] ? fmtPrice(asks[i].price) : ''}
            </td>
            <td className="py-0.5 text-right text-muted-foreground">
              {asks[i] ? fmtFixed(asks[i].size, 4) : ''}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Candles({
  title,
  candles,
}: {
  title: string;
  candles: CandlePoint[];
}) {
  const last = candles.slice(-6).reverse();
  return (
    <div>
      <p className="eyebrow mb-1">
        {title}{' '}
        <span className="normal-case tracking-normal">
          ({candles.length} loaded)
        </span>
      </p>
      {last.length === 0 ? (
        <p className="py-2 text-xs text-muted-foreground">
          No candles returned.
        </p>
      ) : (
        <table className="w-full text-[11.5px]">
          <thead>
            <tr className="text-muted-foreground">
              <th className="eyebrow py-1 text-left font-normal">Open (MNL)</th>
              <th className="eyebrow py-1 text-right font-normal">O</th>
              <th className="eyebrow py-1 text-right font-normal">H</th>
              <th className="eyebrow py-1 text-right font-normal">L</th>
              <th className="eyebrow py-1 text-right font-normal">C</th>
            </tr>
          </thead>
          <tbody className="num">
            {last.map((c) => {
              const up = Number(c.close) >= Number(c.open);
              return (
                <tr key={c.openedAt} className="border-t border-border/40">
                  <td className="py-0.5 text-muted-foreground">
                    {formatManilaTime(c.openedAt)}
                    {!c.complete && (
                      <span className="ml-1 text-warn">open</span>
                    )}
                  </td>
                  <td className="py-0.5 text-right">{fmtPrice(c.open)}</td>
                  <td className="py-0.5 text-right">{fmtPrice(c.high)}</td>
                  <td className="py-0.5 text-right">{fmtPrice(c.low)}</td>
                  <td
                    className={cn(
                      'py-0.5 text-right',
                      up ? 'text-profit' : 'text-loss',
                    )}
                  >
                    {fmtPrice(c.close)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

function RowDetail({ row }: { row: MarketScannerRow }) {
  const ind = row.indicators;
  const ins = row.instrument;
  const scores =
    row.setupScores?.scores && typeof row.setupScores.scores === 'object'
      ? (row.setupScores.scores as Record<string, Record<string, unknown>>)
      : {};
  const h1 =
    row.setupScores?.h1Snapshot &&
    typeof row.setupScores.h1Snapshot === 'object'
      ? (row.setupScores.h1Snapshot as Record<string, unknown>)
      : {};
  const m15 =
    row.setupScores?.m15Snapshot &&
    typeof row.setupScores.m15Snapshot === 'object'
      ? (row.setupScores.m15Snapshot as Record<string, unknown>)
      : {};
  const btc =
    row.setupScores?.btcRegime && typeof row.setupScores.btcRegime === 'object'
      ? (row.setupScores.btcRegime as Record<string, unknown>)
      : {};
  return (
    <div className="rise grid gap-5 border-t border-border bg-background/40 px-4 py-4 lg:grid-cols-[1fr_1fr_1.3fr]">
      <div>
        <p className="eyebrow mb-1">Indicators (screening only)</p>
        {ind ? (
          <dl>
            <KV label="Screening">
              {SCREEN_LABEL[ind.screeningState] ?? ind.screeningState}
            </KV>
            <KV label="Trend 1H / 15M">
              {ind.trend} / {ind.trend15M}
            </KV>
            <KV label="RSI">
              {ind.rsi === null ? 'n/a' : ind.rsi.toFixed(1)} {ind.rsiState}
            </KV>
            <KV label="MACD 1H / 15M">
              {ind.macdDirection} / {ind.macdDirection15M}
            </KV>
            <KV label="Volume">{ind.volumeStrength}</KV>
            <KV label="Volatility">
              {ind.volatilityPct === null
                ? 'n/a'
                : `${ind.volatilityPct.toFixed(2)}%`}
            </KV>
            <KV label="Candles">{ind.candleBehavior}</KV>
          </dl>
        ) : (
          <p className="text-xs text-muted-foreground">
            Indicators were not computed for this snapshot.
          </p>
        )}
        <p className="eyebrow mb-1 mt-4">Instrument rules</p>
        {ins ? (
          <dl>
            <KV label="Instrument">{ins.instrumentId}</KV>
            <KV label="Min size">{ins.minSize ?? 'n/a'}</KV>
            <KV label="Lot / tick">
              {ins.lotSize ?? 'n/a'} / {ins.tickSize ?? 'n/a'}
            </KV>
            {row.marketType === 'futures' && (
              <>
                <KV label="Contract value">{ins.contractValue ?? 'n/a'}</KV>
                <KV label="Max leverage">{ins.maxLeverage ?? 'n/a'}</KV>
              </>
            )}
          </dl>
        ) : (
          <p className="text-xs text-muted-foreground">
            Instrument rules not available.
          </p>
        )}
      </div>
      <div>
        <p className="eyebrow mb-1">Evidence</p>
        <dl>
          <KV label="Observed">
            <Stamp value={row.observedAt} />
          </KV>
          <KV label="Exchange time">
            <Stamp value={row.exchangeAt} />
          </KV>
          <KV label="Age">{fmtAge(row.ageSeconds) ?? 'n/a'}</KV>
          {row.marketType === 'futures' && (
            <>
              <KV label="Funding rate">
                <Val
                  v={fmtPct(
                    row.fundingRate === null
                      ? null
                      : Number(row.fundingRate) * 100,
                    4,
                  )}
                  className={signTone(row.fundingRate)}
                />
              </KV>
              <KV label="Next funding">
                <Stamp value={row.nextFundingAt} />
              </KV>
            </>
          )}
        </dl>
        {row.detail && (
          <p className="mt-2 rounded border-l-2 border-warn/70 bg-warn/[0.06] px-2.5 py-1.5 text-[12px]">
            {row.detail}
          </p>
        )}
        <p className="eyebrow mb-1 mt-4">Deterministic screening</p>
        {Object.keys(scores).length > 0 ? (
          <div className="space-y-3">
            <dl>
              <KV label="BTC regime">
                {String(btc.regime ?? 'unavailable')} ·{' '}
                {String(btc.status ?? 'unavailable')}
              </KV>
              <KV label="1H trend">
                {String(h1.ema_alignment ?? 'unavailable')}
              </KV>
              <KV label="15M confirmation">
                {String(m15.ema_alignment ?? 'unavailable')} /{' '}
                {String(m15.macd_direction ?? 'unavailable')} /{' '}
                {String(m15.candle_behavior ?? 'unavailable')}
              </KV>
            </dl>
            {Object.entries(scores).map(([side, setup]) => (
              <div
                key={side}
                className="rounded border border-border/60 px-3 py-2"
                data-testid={`screen-setup-${rowKey(row)}-${side}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-medium uppercase">
                    {side} setup
                  </span>
                  <span className="num text-teal">
                    {String(setup.score ?? 'n/a')} / 100
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  {String(setup.strategy_type ?? 'strategy unavailable')}
                </p>
                <dl className="mt-2">
                  <KV label="Entry zone">
                    {String(setup.entry_zone_low ?? 'n/a')} –{' '}
                    {String(setup.entry_zone_high ?? 'n/a')}
                  </KV>
                  <KV label="Stop reference">
                    {String(setup.stop_loss ?? 'n/a')}
                  </KV>
                  <KV label="First target reference">
                    {String(setup.tp1 ?? 'n/a')}
                  </KV>
                </dl>
                {Array.isArray(setup.reasons) && (
                  <ul className="mt-2 space-y-1 text-[11px] leading-relaxed text-muted-foreground">
                    {setup.reasons.slice(0, 4).map((reason, index) => (
                      <li key={`${side}-${index}`}>{String(reason)}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            No screening score evidence in this snapshot.
          </p>
        )}
        <p className="mt-2 text-[11.5px] leading-relaxed text-muted-foreground">
          Scores are screening evidence only, not trade advice. A scanner row is
          not a proposal.
        </p>
        <dl className="mt-2">
          <KV label="Candidate status">
            {row.candidateStatus ?? 'not qualified'}
          </KV>
          {row.candidateId && <KV label="Candidate ID">{row.candidateId}</KV>}
        </dl>
        <p className="eyebrow mb-1 mt-4">Order book top</p>
        <Book bids={row.bids} asks={row.asks} />
      </div>
      <div className="space-y-4">
        <Candles title="1H candles, latest first" candles={row.candles} />
        <Candles title="15M candles, latest first" candles={row.candles15M} />
      </div>
    </div>
  );
}

function ScannerRow({
  row,
  open,
  onToggle,
}: {
  row: MarketScannerRow;
  open: boolean;
  onToggle: () => void;
}) {
  const k = rowKey(row);
  const dim = row.status === 'unavailable';
  return (
    <>
      <tr
        data-testid={`row-scanner-${k}`}
        onClick={onToggle}
        className={cn(
          'cursor-pointer border-b border-border/50 transition-colors hover:bg-background/40',
          open && 'bg-background/40',
          dim && 'opacity-70',
        )}
      >
        <td className="py-2.5 pl-3 pr-2">
          <button
            type="button"
            data-testid={`button-expand-${k}`}
            aria-expanded={open}
            className="focus-ring flex items-center gap-2 rounded text-left"
            onClick={(e) => {
              e.stopPropagation();
              onToggle();
            }}
          >
            <ChevronRight
              className={cn(
                'h-3.5 w-3.5 text-muted-foreground transition-transform',
                open && 'rotate-90 text-teal',
              )}
              aria-hidden
            />
            <span className="font-medium">{row.symbol}</span>
          </button>
        </td>
        <td className="px-2 py-2.5">
          <span
            className={cn(
              'rounded-[3px] border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider',
              row.marketType === 'futures'
                ? 'border-chart-2/50 text-chart-2'
                : 'border-teal/50 text-teal',
            )}
          >
            {row.marketType === 'futures' ? 'perp' : 'spot'}
          </span>
        </td>
        <td className="num px-2 py-2.5 text-right">
          <Val v={fmtPrice(row.lastPrice)} />
        </td>
        <td className="num px-2 py-2.5 text-right">
          <Val
            v={fmtPct(row.changePct24H)}
            className={signTone(row.changePct24H)}
          />
        </td>
        <td className="num hidden px-2 py-2.5 text-right text-muted-foreground md:table-cell">
          <Val v={fmtCompact(row.volume24H)} />
        </td>
        <td className="num hidden px-2 py-2.5 text-right lg:table-cell">
          <Val v={fmtPrice(row.bid)} className="text-profit/90" />
        </td>
        <td className="num hidden px-2 py-2.5 text-right lg:table-cell">
          <Val v={fmtPrice(row.ask)} className="text-loss/90" />
        </td>
        <td className="num hidden px-2 py-2.5 text-right md:table-cell">
          <Val
            v={fmtFixed(row.spreadPct, 4) && `${fmtFixed(row.spreadPct, 4)}%`}
          />
        </td>
        <td className="num hidden px-2 py-2.5 text-right xl:table-cell">
          {row.marketType === 'futures' ? (
            <Val
              v={fmtPct(
                row.fundingRate === null ? null : Number(row.fundingRate) * 100,
                4,
              )}
              className={signTone(row.fundingRate)}
            />
          ) : (
            <span className="text-muted-foreground/50">-</span>
          )}
        </td>
        <td className="hidden px-2 py-2.5 text-[12px] sm:table-cell">
          {row.indicators ? (
            <span
              className={cn(
                row.indicators.screeningState === 'watch'
                  ? 'text-teal'
                  : 'text-muted-foreground',
              )}
            >
              {SCREEN_LABEL[row.indicators.screeningState] ??
                row.indicators.screeningState}
            </span>
          ) : (
            <NotAvailable>n/a</NotAvailable>
          )}
        </td>
        <td className="hidden px-2 py-2.5 text-right sm:table-cell">
          {scoreSummary(row.setupScores) ? (
            <span
              className="num text-teal"
              title={scoreSummary(row.setupScores) ?? undefined}
              data-testid={`text-screen-score-${k}`}
            >
              {scoreSummary(row.setupScores)}
            </span>
          ) : (
            <NotAvailable>n/a</NotAvailable>
          )}
        </td>
        <td
          className="hidden px-2 py-2.5 text-[11px] md:table-cell"
          data-testid={`status-candidate-${k}`}
        >
          {row.candidateId ? (
            <span className="text-teal">
              {row.candidateStatus ?? 'qualified'}{' '}
              <span className="font-mono text-muted-foreground">
                {row.candidateId}
              </span>
            </span>
          ) : (
            <span className="text-muted-foreground">
              {row.candidateStatus ?? 'not qualified'}
            </span>
          )}
        </td>
        <td className="py-2.5 pl-2 pr-3 text-right">
          <Freshness row={row} />
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={13} className="p-0">
            <RowDetail row={row} />
          </td>
        </tr>
      )}
    </>
  );
}

export default function MarketScannerPage() {
  const q = useGetMarketScanner({
    query: { queryKey: getGetMarketScannerQueryKey(), refetchInterval: 30000 },
  });
  const [filter, setFilter] = useState<Filter>('all');
  const [open, setOpen] = useState<string | null>(null);
  const data = q.data;

  const rows = useMemo(
    () =>
      (data?.rows ?? []).filter(
        (r) => filter === 'all' || r.marketType === filter,
      ),
    [data, filter],
  );
  const counts = useMemo(() => {
    const c = { fresh: 0, stale: 0, unavailable: 0 };
    for (const r of data?.rows ?? []) c[r.status] = (c[r.status] ?? 0) + 1;
    return c;
  }, [data]);
  const allDown =
    !!data && data.rows.length > 0 && counts.unavailable === data.rows.length;

  return (
    <div
      data-testid="page-market-scanner"
      className="mx-auto max-w-[1440px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Live / Phase 2 / Module 03</p>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-semibold tracking-tight">
            Market Scanner <PaperLabel />
          </h1>
          <p className="mt-1 max-w-xl text-[12.5px] text-muted-foreground">
            Public OKX spot and perpetual data. Deterministic scores are
            screening evidence, not trade advice. Only persisted proposals can
            receive owner decisions; the entry engine remains fail-closed.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data && (
            <p
              className="num text-right text-[11.5px] text-muted-foreground"
              data-testid="text-scanned-at"
            >
              Scanned {formatManilaTime(data.scannedAt)} MNL
              <span className="block">{data.provider} / every 30 s</span>
            </p>
          )}
          <button
            type="button"
            data-testid="button-refresh-scanner"
            onClick={() => q.refetch()}
            disabled={q.isFetching}
            className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-border bg-card px-3 text-[13px] transition-colors hover:border-teal/60 disabled:opacity-70"
          >
            <RefreshCw
              className={cn(
                'h-3.5 w-3.5 text-teal',
                q.isFetching && 'animate-spin',
              )}
              aria-hidden
            />
            {q.isFetching ? 'Scanning' : 'Rescan'}
          </button>
        </div>
      </div>

      {q.isError && (
        <div className="mt-5">
          <ErrorNote
            error={q.error}
            title={
              data
                ? 'The latest scan failed. Showing the previous snapshot.'
                : 'Scanner data could not be loaded'
            }
            onRetry={() => q.refetch()}
          />
        </div>
      )}

      {q.isLoading && (
        <div className="panel mt-5 space-y-2 p-4" aria-busy>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-8 w-full bg-muted" />
          ))}
        </div>
      )}

      {data && (
        <div key={q.dataUpdatedAt} className="landed mt-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div
              className="inline-flex rounded-md border border-border bg-card p-0.5"
              role="tablist"
            >
              {(['all', 'spot', 'futures'] as Filter[]).map((f) => (
                <button
                  key={f}
                  type="button"
                  role="tab"
                  aria-selected={filter === f}
                  data-testid={`button-filter-${f}`}
                  onClick={() => setFilter(f)}
                  className={cn(
                    'focus-ring rounded px-3 py-1 text-[12px] transition-colors',
                    filter === f
                      ? 'bg-teal/15 text-teal'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {f === 'all' ? 'All' : f === 'spot' ? 'Spot' : 'Perpetual'}
                </button>
              ))}
            </div>
            <div
              className="num flex gap-4 text-[11.5px]"
              data-testid="text-freshness-counts"
            >
              <span className="text-profit">{counts.fresh} fresh</span>
              <span className="text-warn">{counts.stale} stale</span>
              <span className="text-loss">
                {counts.unavailable} unavailable
              </span>
            </div>
          </div>

          {allDown && (
            <div
              role="alert"
              className="flex items-start gap-3 rounded-md border border-loss/50 bg-loss/[0.08] p-3"
            >
              <Radio className="mt-0.5 h-4 w-4 text-loss" aria-hidden />
              <div>
                <p className="text-sm font-medium">Market data outage</p>
                <p className="text-[12.5px] text-muted-foreground">
                  Every instrument is unavailable from {data.provider}. Nothing
                  on this screen should be read as a current price.
                </p>
              </div>
            </div>
          )}

          <section className="panel overflow-hidden">
            {rows.length === 0 ? (
              <div className="px-4 py-10 text-center">
                <p className="text-[13px]">No instruments in this snapshot.</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  The scanner returned no rows for this market type. It retries
                  every 30 seconds.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[12.5px]">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="eyebrow py-2 pl-3 pr-2 font-normal">
                        Pair
                      </th>
                      <th className="eyebrow px-2 py-2 font-normal">Type</th>
                      <th className="eyebrow px-2 py-2 text-right font-normal">
                        Last
                      </th>
                      <th className="eyebrow px-2 py-2 text-right font-normal">
                        24h
                      </th>
                      <th className="eyebrow hidden px-2 py-2 text-right font-normal md:table-cell">
                        Vol 24h
                      </th>
                      <th className="eyebrow hidden px-2 py-2 text-right font-normal lg:table-cell">
                        Bid
                      </th>
                      <th className="eyebrow hidden px-2 py-2 text-right font-normal lg:table-cell">
                        Ask
                      </th>
                      <th className="eyebrow hidden px-2 py-2 text-right font-normal md:table-cell">
                        Spread
                      </th>
                      <th className="eyebrow hidden px-2 py-2 text-right font-normal xl:table-cell">
                        Funding
                      </th>
                      <th className="eyebrow hidden px-2 py-2 font-normal sm:table-cell">
                        Screen
                      </th>
                      <th className="eyebrow hidden px-2 py-2 text-right font-normal sm:table-cell">
                        Score evidence
                      </th>
                      <th className="eyebrow hidden px-2 py-2 font-normal md:table-cell">
                        Candidate
                      </th>
                      <th className="eyebrow py-2 pl-2 pr-3 text-right font-normal">
                        Data
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <ScannerRow
                        key={rowKey(r)}
                        row={r}
                        open={open === rowKey(r)}
                        onToggle={() =>
                          setOpen(open === rowKey(r) ? null : rowKey(r))
                        }
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          <p className="text-[11.5px] text-muted-foreground">
            Select a row for indicators, instrument rules, order-book levels and
            recent candles. Hover any timestamp for UTC.
          </p>
        </div>
      )}
    </div>
  );
}
