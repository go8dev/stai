import { useMemo, useState, type KeyboardEvent } from 'react';
import {
  getGetCommitteeOverviewQueryKey,
  getGetMarketIntelligenceQueryKey,
  getGetMarketScannerQueryKey,
  getGetProposalCenterQueryKey,
  useGetCommitteeOverview,
  useGetMarketScanner,
  useGetMarketIntelligence,
  useGetProposalCenter,
  type CommitteeOverview,
  type MtfInstrumentAnalysis,
  type MarketScannerRow,
  type ProposalCenterOverview,
} from '@workspace/api-client-react';
import {
  Activity,
  ArrowDown,
  ArrowUp,
  RefreshCw,
  Search,
  ShieldCheck,
} from 'lucide-react';
import { CandlestickChart } from '@/components/market-screener/candlestick-chart';
import { PullbackResearch } from '@/components/pullback-research';
import { ErrorNote, PaperLabel } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';
import {
  formatManilaDateTime,
  formatManilaTime,
  formatUtcDateTime,
} from '@/lib/format';
import { fmtCompact, fmtPct, fmtPrice, signTone } from '@/lib/display-number';
import { cn } from '@/lib/utils';

type View =
  | 'opportunities'
  | 'overview'
  | 'technicals'
  | 'structure'
  | 'performance'
  | 'committee';
type Market = 'all' | 'spot' | 'futures';
type Direction = 'all' | 'long' | 'short';
type Sort = { key: string; direction: 'asc' | 'desc' };

const VIEWS: { id: View; label: string }[] = [
  { id: 'opportunities', label: 'Opportunities' },
  { id: 'overview', label: 'Overview' },
  { id: 'technicals', label: 'Technicals' },
  { id: 'structure', label: 'Support & Resistance' },
  { id: 'performance', label: 'Performance' },
  { id: 'committee', label: 'AI Committee' },
];
const TIMEFRAMES = ['1D', '4H', '1H', '15M'] as const;
const EMPTY_ROWS: MarketScannerRow[] = [];
const EMPTY_INTELLIGENCE: MtfInstrumentAnalysis[] = [];
const rowKey = (row: MarketScannerRow) => `${row.symbol}-${row.marketType}`;
const asNum = (value: unknown): number | null => {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
};
const scoreData = (row: MarketScannerRow) => {
  const scores = row.setupScores?.scores;
  return scores && typeof scores === 'object'
    ? (scores as Record<string, Record<string, unknown>>)
    : {};
};
const normalized = (value: string) =>
  value.toUpperCase().replace(/[-_/]/g, '').replace(/SWAP$/, '');
const tfId = (value: (typeof TIMEFRAMES)[number]) =>
  value.toLowerCase() as MtfInstrumentAnalysis['timeframes'][number]['timeframe'];
const matchAnalysis = (
  analysis: MtfInstrumentAnalysis[],
  row: MarketScannerRow,
) =>
  analysis.find(
    (item) =>
      normalized(item.symbol) === normalized(row.symbol) &&
      item.marketType === row.marketType,
  );
const metric = (value: number | string | null | undefined, digits = 2) => {
  const parsed = asNum(value);
  return parsed === null ? 'Insufficient data' : parsed.toFixed(digits);
};
const text = (value: unknown, fallback = 'Not available') =>
  typeof value === 'string' || typeof value === 'number'
    ? String(value)
    : fallback;

function Stamp({ value }: { value: string | null }) {
  if (!value)
    return <span className="text-muted-foreground">Not available</span>;
  return (
    <span title={`${formatUtcDateTime(value)} UTC`}>
      {formatManilaDateTime(value)}{' '}
      <small className="text-muted-foreground">MNL</small>
    </span>
  );
}

function ScoreCell({
  score,
  side,
}: {
  score: number | null;
  side: 'long' | 'short';
}) {
  if (score === null) return <span className="text-muted-foreground">—</span>;
  return (
    <span className={cn('num', side === 'long' ? 'text-profit' : 'text-loss')}>
      {score.toFixed(1)}
      <small className="text-muted-foreground"> / 100</small>
    </span>
  );
}

function MarketTable({
  rows,
  intelligence,
  view,
  sort,
  onSort,
  selected,
  onSelect,
  proposal,
  committee,
}: {
  rows: MarketScannerRow[];
  intelligence: MtfInstrumentAnalysis[];
  view: View;
  sort: Sort;
  onSort: (key: string) => void;
  selected: string | null;
  onSelect: (key: string) => void;
  proposal: ProposalCenterOverview | undefined;
  committee: CommitteeOverview | undefined;
}) {
  const headers: [string, string][] =
    view === 'opportunities'
      ? [
          ['symbol', 'Instrument'],
          ['lastPrice', 'Price'],
          ['changePct24H', '24H'],
          ['bullish', 'Bullish score'],
          ['bearish', 'Bearish score'],
          ['status', 'Opportunity status'],
        ]
      : view === 'overview'
        ? [
            ['symbol', 'Instrument'],
            ['lastPrice', 'Price'],
            ['changePct24H', '24H change'],
            ['volume24H', '24H volume'],
            ['marketType', 'Market'],
            ['bias', 'Market bias'],
          ]
        : view === 'technicals'
          ? [
              ['symbol', 'Instrument'],
              ['rsi', 'RSI14 · all TF'],
              ['sma', 'SMA20/50 alignment'],
              ['bias', 'Classification'],
              ['observedAt', 'Snapshot timestamp'],
            ]
          : view === 'structure'
            ? [
                ['symbol', 'Instrument'],
                ['1D', '1D support / resistance'],
                ['4H', '4H support / resistance'],
                ['1H', '1H support / resistance'],
                ['15M', '15M support / resistance'],
                ['nearest', 'Nearest zone'],
              ]
            : view === 'performance'
              ? [
                  ['symbol', 'Instrument'],
                  ['changePct24H', '24H'],
                  ['7d', '7D'],
                  ['30d', '30D'],
                  ['volume24H', 'Volume'],
                  ['bias', 'Market bias'],
                ]
              : [
                  ['symbol', 'Instrument'],
                  ['status', 'Opportunity status'],
                  ['direction', 'Proposed direction'],
                  ['review', 'Committee review'],
                  ['recommendation', 'Recommendation'],
                  ['approval', 'Owner approval'],
                ];

  const pairedProposal = (row: MarketScannerRow) =>
    proposal?.proposals.find(
      (p) =>
        normalized(p.instrument).includes(normalized(row.symbol)) &&
        p.marketType === row.marketType,
    );
  const pairedCandidate = (row: MarketScannerRow) =>
    proposal?.candidates.find(
      (c) =>
        normalized(c.symbol) === normalized(row.symbol) &&
        c.marketType === row.marketType,
    );
  const committeeRun = (row: MarketScannerRow) =>
    committee?.runs.find(
      (r) =>
        normalized(r.symbol) === normalized(row.symbol) &&
        r.marketType === row.marketType,
    );
  const analysis = (row: MarketScannerRow) => matchAnalysis(intelligence, row);

  const cell = (row: MarketScannerRow, key: string) => {
    const mtf = analysis(row);
    if (key === 'symbol')
      return (
        <span className="font-semibold tracking-tight">
          {row.symbol}
          <small className="ml-2 font-mono text-[9px] uppercase text-muted-foreground">
            {row.marketType === 'futures' ? 'perp' : 'spot'}
          </small>
        </span>
      );
    if (key === 'lastPrice')
      return (
        <span className="num">{fmtPrice(mtf?.quote.lastPrice) ?? '—'}</span>
      );
    if (key === 'changePct24H')
      return (
        <span className={cn('num', signTone(mtf?.quote.changePct24H))}>
          {fmtPct(mtf?.quote.changePct24H) ?? '—'}
        </span>
      );
    if (key === 'bullish')
      return (
        <ScoreCell
          score={asNum(analysis(row)?.evidence.bullishScore)}
          side="long"
        />
      );
    if (key === 'bearish')
      return (
        <ScoreCell
          score={asNum(analysis(row)?.evidence.bearishScore)}
          side="short"
        />
      );
    if (key === 'status') {
      const opportunity = analysis(row)?.opportunity;
      if (!opportunity)
        return <span className="text-muted-foreground">Insufficient data</span>;
      const tone =
        opportunity.state === 'indicative_setup_ready'
          ? 'text-profit border-profit/35 bg-profit/5'
          : /waiting|awaiting|watch|entry_zone/i.test(opportunity.state)
            ? 'text-warn border-warn/35 bg-warn/5'
            : /invalid|no_opportunity|insufficient_data/i.test(
                  opportunity.state,
                )
              ? 'text-muted-foreground border-border'
              : 'text-loss border-loss/35 bg-loss/5';
      return (
        <span
          title={opportunity.detail}
          className={cn(
            'inline-flex max-w-[220px] rounded-sm border px-1.5 py-1 text-[10px] uppercase leading-tight tracking-wide',
            tone,
          )}
        >
          {opportunity.state.replaceAll('_', ' ')}
        </span>
      );
    }
    if (key === 'volume24H')
      return (
        <span className="num">
          {fmtCompact(analysis(row)?.quote.volume24H) ?? '—'}
        </span>
      );
    if (key === 'marketType')
      return (
        <span className="uppercase text-muted-foreground">
          {row.marketType === 'futures' ? 'Perpetual' : 'Spot'}
        </span>
      );
    if (key === 'bias') {
      const evidence = analysis(row)?.evidence;
      return (
        <span className="text-muted-foreground">
          {evidence
            ? `${evidence.classification.replaceAll('_', ' ')}${evidence.status === 'stale' ? ' · stale' : ''}`
            : 'Insufficient data'}
        </span>
      );
    }
    if (key === 'rsi')
      return (
        <span className="num whitespace-nowrap">
          {TIMEFRAMES.map(
            (tf) =>
              `${tf} ${metric(analysis(row)?.timeframes.find((item) => item.timeframe === tfId(tf))?.rsi14, 1)}`,
          ).join(' · ')}
        </span>
      );
    if (key === 'sma')
      return (
        <span className="text-muted-foreground">
          {TIMEFRAMES.map(
            (tf) =>
              `${tf} ${analysis(row)?.timeframes.find((item) => item.timeframe === tfId(tf))?.smaDirection ?? 'unavailable'}`,
          ).join(' · ')}
        </span>
      );
    if (key === 'observedAt') return <Stamp value={row.observedAt} />;
    if (['1D', '4H', '1H', '15M', 'nearest'].includes(key)) {
      const tf =
        key === '1D' ? '1d' : key === '4H' ? '4h' : key === '1H' ? '1h' : '15m';
      const item = analysis(row);
      const zones =
        item?.zones
          .filter(
            (zone) =>
              zone.sourceTimeframe === tf && zone.state !== 'invalidated',
          )
          .sort(
            (a, b) =>
              Number(a.distanceFromPrice ?? Infinity) -
              Number(b.distanceFromPrice ?? Infinity),
          )
          .slice(0, 2) ?? [];
      if (key === 'nearest')
        return (
          <span className="text-muted-foreground">
            {item?.nearestSupport
              ? `S ${fmtPrice(item.nearestSupport.lower)}–${fmtPrice(item.nearestSupport.upper)}`
              : 'S —'}{' '}
            /{' '}
            {item?.nearestResistance
              ? `R ${fmtPrice(item.nearestResistance.lower)}–${fmtPrice(item.nearestResistance.upper)}`
              : 'R —'}
          </span>
        );
      return (
        <span className="text-muted-foreground">
          {zones.length
            ? zones
                .map(
                  (zone) =>
                    `${zone.kind === 'support' ? 'S' : 'R'} ${fmtPrice(zone.lower)}–${fmtPrice(zone.upper)}`,
                )
                .join(' · ')
            : 'No confirmed zones'}
        </span>
      );
    }
    if (key === '7d' || key === '30d') {
      const daily =
        analysis(row)?.timeframes.find((item) => item.timeframe === '1d')
          ?.candles ?? [];
      const period = key === '7d' ? 7 : 30;
      const last = daily.at(-1);
      const past = daily.at(-(period + 1));
      if (!last || !past || Number(past.close) === 0)
        return <span className="text-muted-foreground">Insufficient data</span>;
      const change =
        ((Number(last.close) - Number(past.close)) / Number(past.close)) * 100;
      return (
        <span className={cn('num', signTone(change))}>{fmtPct(change)}</span>
      );
    }
    if (key === 'direction')
      return (
        <span className="uppercase">
          {pairedProposal(row)?.side ??
            pairedCandidate(row)?.side ??
            mtf?.opportunity.direction ??
            'Not proposed'}
        </span>
      );
    if (key === 'review')
      return (
        <span>{committeeRun(row)?.status ?? 'Awaiting committee review'}</span>
      );
    if (key === 'recommendation') {
      const details = pairedProposal(row)?.details;
      const recommendation = details?.recommendation;
      return (
        <span className="text-muted-foreground">
          {text(
            recommendation,
            pairedProposal(row)?.decisionReason ?? 'No recommendation returned',
          )}
        </span>
      );
    }
    if (key === 'approval')
      return <span>{pairedProposal(row)?.status ?? 'Not requested'}</span>;
    return '—';
  };
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-left text-[11.5px]">
        <thead className="sticky top-0 z-[1] bg-card">
          <tr className="border-b border-border/80">
            {headers.map(([key, label]) => (
              <th key={key} className="px-3 py-2.5">
                <button
                  type="button"
                  data-testid={`sort-${key}`}
                  onClick={() => onSort(key)}
                  className="focus-ring inline-flex items-center gap-1 whitespace-nowrap text-left font-mono text-[9px] uppercase tracking-[.12em] text-muted-foreground hover:text-foreground"
                >
                  {label}
                  {sort.key === key &&
                    (sort.direction === 'asc' ? (
                      <ArrowUp className="h-3 w-3" />
                    ) : (
                      <ArrowDown className="h-3 w-3" />
                    ))}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const key = rowKey(row);
            return (
              <tr
                key={key}
                data-testid={`row-market-${key}`}
                data-freshness={
                  analysis(row)?.quote.status ?? row.status ?? 'unavailable'
                }
                onClick={() => onSelect(key)}
                className={cn(
                  'cursor-pointer border-b border-border/45 transition-colors hover:bg-teal/[0.035]',
                  selected === key && 'bg-teal/[0.07]',
                  row.status === 'unavailable' && 'opacity-65',
                )}
                aria-selected={selected === key}
              >
                {headers.map(([column]) => (
                  <td key={column} className="px-3 py-3 align-middle">
                    {cell(row, column)}
                  </td>
                ))}
              </tr>
            );
          })}
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={headers.length}
                className="p-8 text-center text-muted-foreground"
              >
                No instruments match these filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function EvidenceCard({
  timeframe,
  analysis,
  active,
  onClick,
}: {
  timeframe: (typeof TIMEFRAMES)[number];
  analysis: MtfInstrumentAnalysis | undefined;
  active: boolean;
  onClick: () => void;
}) {
  const data = analysis?.timeframes.find(
    (item) => item.timeframe === tfId(timeframe),
  );
  const component = analysis?.evidence.components.find(
    (item) => item.timeframe === tfId(timeframe),
  );
  const timestamp = data?.latestCompletedAt ?? null;
  const status = data?.status ?? 'unavailable';
  return (
    <button
      type="button"
      data-testid={`timeframe-${timeframe}`}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'focus-ring min-w-0 rounded-sm border p-3 text-left transition-colors',
        active
          ? 'border-teal/50 bg-teal/[0.08]'
          : 'border-border/70 bg-background/20 hover:border-border',
      )}
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] font-semibold">{timeframe}</span>
        <span
          title={status}
          className={cn(
            'h-1.5 w-1.5 rounded-full',
            status === 'fresh'
              ? 'bg-profit'
              : status === 'stale'
                ? 'bg-warn'
                : 'bg-muted-foreground/40',
          )}
        />
      </div>
      <p className="mt-2 text-[10px] text-muted-foreground">RSI(14)</p>
      <p className="num mt-0.5 text-sm">{metric(data?.rsi14, 1)}</p>
      <p className="mt-2 text-[10px] text-muted-foreground">SMA20 / SMA50</p>
      <p className="num text-[10px]">
        {metric(data?.sma20)} / {metric(data?.sma50)}
      </p>
      <p
        className={cn(
          'mt-2 text-[10px] uppercase',
          data?.smaDirection === 'bullish'
            ? 'text-profit'
            : data?.smaDirection === 'bearish'
              ? 'text-loss'
              : 'text-muted-foreground',
        )}
      >
        {data?.smaDirection ?? 'unavailable'} · {status}
      </p>
      <p className="mt-1 text-[9px] leading-relaxed text-muted-foreground">
        SMA {component?.smaDirection ?? '—'} {metric(component?.smaPoints, 1)}{' '}
        pts · RSI {component?.rsiDirection ?? '—'}{' '}
        {metric(component?.rsiPoints, 1)} pts · weight{' '}
        {component?.weight ?? '—'}
      </p>
      <p
        className="mt-1 truncate text-[9px] text-muted-foreground"
        title={timestamp ? `${formatUtcDateTime(timestamp)} UTC` : undefined}
      >
        {timestamp
          ? `${formatManilaTime(timestamp)} MNL`
          : 'No completed-candle timestamp'}
      </p>
    </button>
  );
}

function DetailPanel({
  row,
  analysis,
  timeframe,
  setTimeframe,
  proposals,
  committee,
}: {
  row: MarketScannerRow;
  analysis: MtfInstrumentAnalysis | null;
  timeframe: (typeof TIMEFRAMES)[number];
  setTimeframe: (value: (typeof TIMEFRAMES)[number]) => void;
  proposals: ProposalCenterOverview | undefined;
  committee: CommitteeOverview | undefined;
}) {
  const scores = scoreData(row);
  const bull = asNum(analysis?.evidence.bullishScore);
  const bear = asNum(analysis?.evidence.bearishScore);
  const frame = analysis?.timeframes.find(
    (item) => item.timeframe === tfId(timeframe),
  );
  const candleData = frame?.candles ?? [];
  const [visibleTimeframes, setVisibleTimeframes] = useState<string[]>([
    '1d',
    '4h',
    '1h',
    '15m',
  ]);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const candidate = proposals?.candidates.find(
    (c) =>
      normalized(c.symbol) === normalized(row.symbol) &&
      c.marketType === row.marketType,
  );
  const run = committee?.runs.find(
    (r) =>
      normalized(r.symbol) === normalized(row.symbol) &&
      r.marketType === row.marketType,
  );
  const legacyEntries = Object.entries(scores);
  const opportunity = analysis?.opportunity;
  const plan = opportunity?.plan;
  const visibleZones = visibleTimeframes.flatMap((tf) =>
    (analysis?.zones ?? [])
      .filter(
        (zone) => zone.sourceTimeframe === tf && zone.state !== 'invalidated',
      )
      .sort(
        (a, b) =>
          Number(a.distanceFromPrice ?? Infinity) -
          Number(b.distanceFromPrice ?? Infinity),
      )
      .slice(0, 6),
  );
  const selectedZone = analysis?.zones.find(
    (zone) => zone.id === selectedZoneId,
  );
  return (
    <section className="panel overflow-hidden" data-testid="market-detail">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-border/70 px-4 py-3">
        <div>
          <p className="eyebrow">
            Market structure analysis · selected instrument
          </p>
          <h2 className="mt-1 text-lg font-semibold">
            {row.symbol}
            <span className="ml-2 text-[10px] font-mono uppercase text-muted-foreground">
              {row.marketType === 'futures' ? 'Perpetual' : 'Spot'}
            </span>
          </h2>
          <p className="mt-1 text-[10px] text-muted-foreground">
            Live price is exchange ticker data. Indicators use completed candles
            only.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border/70 px-2.5 py-1.5 text-[10px]">
          <span
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              analysis?.quote.status === 'fresh'
                ? 'bg-profit'
                : analysis?.quote.status === 'stale'
                  ? 'bg-warn'
                  : 'bg-loss',
            )}
          />
          <span className="uppercase">
            {analysis?.quote.status ?? 'unavailable'}
          </span>
          <span className="text-muted-foreground">
            <Stamp value={analysis?.quote.observedAt ?? null} />
          </span>
        </div>
      </header>
      <div className="grid gap-px bg-border/50 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            title: 'Bullish evidence',
            value: bull === null ? 'Unavailable' : `${bull.toFixed(1)} / 100`,
            note:
              analysis?.evidence.status === 'complete'
                ? 'Balanced v1 · weighted evidence'
                : analysis?.evidence.status === 'stale'
                  ? 'Last-known stale evidence · no readiness'
                  : 'Insufficient timeframe history',
            tone: 'text-profit',
          },
          {
            title: 'Bearish evidence',
            value: bear === null ? 'Unavailable' : `${bear.toFixed(1)} / 100`,
            note:
              analysis?.evidence.status === 'complete'
                ? `Neutral ${metric(analysis.evidence.neutralPoints, 1)} points`
                : analysis?.evidence.status === 'stale'
                  ? 'Last-known stale evidence · no readiness'
                  : 'Insufficient timeframe history',
            tone: 'text-loss',
          },
          {
            title: 'Nearest support zone',
            value: analysis?.nearestSupport
              ? `${fmtPrice(analysis.nearestSupport.lower)} – ${fmtPrice(analysis.nearestSupport.upper)}`
              : 'Unavailable',
            note: analysis?.nearestSupport
              ? `${analysis.nearestSupport.sourceTimeframe.toUpperCase()} · ${analysis.nearestSupport.state}`
              : 'No confirmed zone below quote',
            tone: 'text-foreground',
          },
          {
            title: 'Nearest resistance zone',
            value: analysis?.nearestResistance
              ? `${fmtPrice(analysis.nearestResistance.lower)} – ${fmtPrice(analysis.nearestResistance.upper)}`
              : 'Unavailable',
            note: analysis?.nearestResistance
              ? `${analysis.nearestResistance.sourceTimeframe.toUpperCase()} · ${analysis.nearestResistance.state}`
              : 'No confirmed zone above quote',
            tone: 'text-foreground',
          },
        ].map((item) => (
          <div key={item.title} className="bg-card px-4 py-3">
            <p className="eyebrow">{item.title}</p>
            <p className={cn('num mt-1.5 text-base font-medium', item.tone)}>
              {item.value}
            </p>
            <p className="mt-1 text-[10px] text-muted-foreground">
              {item.note}
            </p>
          </div>
        ))}
      </div>
      {analysis?.btcContext && (
        <div className="border-b border-border/60 bg-background/25 px-4 py-2 text-[10px] text-muted-foreground">
          BTC context ·{' '}
          {analysis.btcContext.classification.replaceAll('_', ' ')} · bull{' '}
          {metric(analysis.btcContext.bullishScore, 1)} / bear{' '}
          {metric(analysis.btcContext.bearishScore, 1)} / neutral{' '}
          {metric(analysis.btcContext.neutralPoints, 1)} · context only, not an
          alignment gate
        </div>
      )}
      <div className="grid lg:grid-cols-[minmax(0,1.6fr)_minmax(275px,.8fr)]">
        <div className="min-w-0 border-b border-border/60 lg:border-b-0 lg:border-r">
          <div className="flex flex-wrap items-center justify-between gap-3 px-3 py-2.5">
            <div>
              <p className="eyebrow">OKX candlestick tape</p>
              <p className="mt-0.5 text-[10px] text-muted-foreground">
                {timeframe} · completed bars only · indicative current ticker
              </p>
            </div>
            <div
              className="flex rounded border border-border/70 p-0.5"
              role="group"
              aria-label="Chart timeframe"
            >
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf}
                  type="button"
                  data-testid={`chart-timeframe-${tf}`}
                  aria-pressed={timeframe === tf}
                  onClick={() => setTimeframe(tf)}
                  className={cn(
                    'focus-ring rounded px-2.5 py-1 font-mono text-[10px]',
                    timeframe === tf
                      ? 'bg-teal/15 text-teal'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>
          <CandlestickChart
            candles={candleData}
            timeframe={timeframe}
            symbol={row.symbol}
            zones={visibleZones}
            currentPrice={analysis?.quote.lastPrice ?? null}
            selectedZoneId={selectedZoneId}
            onSelectZone={setSelectedZoneId}
          />
          <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-[10px] text-muted-foreground">
            <span className="flex flex-wrap gap-1.5">
              Zone overlays ·{' '}
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf}
                  type="button"
                  onClick={() =>
                    setVisibleTimeframes((old) =>
                      old.includes(tfId(tf))
                        ? old.filter((item) => item !== tfId(tf))
                        : [...old, tfId(tf)],
                    )
                  }
                  className={cn(
                    'rounded border px-1.5 py-0.5 font-mono',
                    visibleTimeframes.includes(tfId(tf))
                      ? 'border-teal/40 text-teal'
                      : 'border-border text-muted-foreground',
                  )}
                >
                  {tf}
                </button>
              ))}
            </span>
            <span className="font-mono">
              {selectedZone
                ? `${selectedZone.kind} · ${selectedZone.sourceTimeframe.toUpperCase()} · ${fmtPrice(selectedZone.lower)}–${fmtPrice(selectedZone.upper)} · ${selectedZone.state}`
                : `${visibleZones.length} calculated zones`}
            </span>
          </div>
          {selectedZone && (
            <div className="border-t border-border/50 px-3 py-2 text-[9px] text-muted-foreground">
              Pivot {formatManilaDateTime(selectedZone.pivotAt)} MNL · confirmed{' '}
              {formatManilaDateTime(selectedZone.confirmedAt)} MNL ·{' '}
              {selectedZone.independentReactions} independent reactions
              {selectedZone.confluenceTimeframes.length
                ? ` · confluence ${selectedZone.confluenceTimeframes.join(', ')}`
                : ''}
              {selectedZone.isPriorExtreme ? ' · prior completed extreme' : ''}
            </div>
          )}
        </div>
        <aside className="min-w-0 p-3">
          <div className="flex items-center justify-between">
            <p className="eyebrow">Opportunity assessment</p>
            <span className="rounded border border-warn/30 px-1.5 py-0.5 text-[9px] uppercase text-warn">
              Research only
            </span>
          </div>
          <dl className="mt-2 divide-y divide-border/50">
            {[
              [
                'Market direction',
                analysis?.evidence.classification.replaceAll('_', ' ') ??
                  'Insufficient data',
              ],
              [
                'Entry readiness',
                opportunity?.state.replaceAll('_', ' ') ?? 'Insufficient data',
              ],
              [
                'Indicative entry',
                plan
                  ? (fmtPrice(plan.entryReference) ?? 'Not proposed')
                  : 'Not proposed',
              ],
              [
                'Indicative structural stop',
                plan
                  ? (fmtPrice(plan.stopReference) ?? 'Not proposed')
                  : 'Not proposed',
              ],
              [
                'Indicative target',
                plan
                  ? (fmtPrice(plan.targetReference) ?? 'Not proposed')
                  : 'Not proposed',
              ],
              [
                'Gross / net reward-risk',
                plan
                  ? `${metric(plan.grossRewardRisk, 2)} / ${metric(plan.estimatedNetRewardRisk, 2)}`
                  : 'Not proposed',
              ],
              ['AI Committee', run?.status ?? 'No matching review record'],
            ].map(([label, value]) => (
              <div
                key={label}
                className="flex items-baseline justify-between gap-3 py-2 text-[11px]"
              >
                <dt className="shrink-0 text-muted-foreground">{label}</dt>
                <dd className="text-right font-medium">{value}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 border-l-2 border-warn/50 bg-warn/[0.04] px-2.5 py-2 text-[10px] leading-relaxed text-muted-foreground">
            {opportunity?.detail ?? 'No research opportunity returned.'} Any
            displayed levels are indicative research only, not a trade-ready
            proposal. Existing proposal history above remains separate.
          </p>
          {plan && (
            <div className="mt-2 rounded border border-border/60 p-2 text-[9px] text-muted-foreground">
              <p>
                Anchor{' '}
                {plan.signalAt
                  ? formatManilaDateTime(opportunity?.anchorAt ?? plan.signalAt)
                  : '—'}{' '}
                MNL · expires {formatManilaDateTime(plan.expiresAt)} MNL
              </p>
              <p className="mt-1">{plan.trigger}</p>
              <p className="mt-1">{plan.costNote}</p>
            </div>
          )}
          <p className="eyebrow mb-2 mt-4">
            Legacy setup evidence · diagnostic only
          </p>
          {legacyEntries.length ? (
            legacyEntries.map(([side, setup]) => (
              <div
                key={side}
                className="mb-2 rounded border border-border/60 p-2.5"
              >
                <div className="flex justify-between text-[10px] uppercase">
                  <span>
                    {side} · {text(setup.strategy_type, 'strategy unavailable')}
                  </span>
                  <span className="num text-teal">
                    {text(setup.score, 'n/a')} / 100
                  </span>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-[10px]">
                  <span className="text-muted-foreground">Entry reference</span>
                  <span className="num text-right">
                    {text(setup.entry_zone_low, '—')} –{' '}
                    {text(setup.entry_zone_high, '—')}
                  </span>
                  <span className="text-muted-foreground">Stop reference</span>
                  <span className="num text-right">
                    {text(setup.stop_loss, '—')}
                  </span>
                  <span className="text-muted-foreground">
                    Target reference
                  </span>
                  <span className="num text-right">{text(setup.tp1, '—')}</span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-[10px] text-muted-foreground">
              No legacy setup evidence returned.
            </p>
          )}
          <div className="mt-3 text-[10px] text-muted-foreground">
            Candidate status ·{' '}
            <span className="text-foreground">
              {candidate?.status ?? row.candidateStatus ?? 'No candidate'}
            </span>
            {candidate && <span> · {candidate.id}</span>}
          </div>
        </aside>
      </div>
      <div className="border-t border-border/70 px-3 py-3">
        <div className="mb-2 flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="eyebrow">Multi-timeframe evidence · Balanced v1</p>
            <p className="mt-1 text-[10px] text-muted-foreground">
              {analysis?.evidence.note ?? 'MTF analysis unavailable.'}
            </p>
          </div>
          <span className="text-[9px] text-muted-foreground">
            {analysis?.evidence.disagreementReasons.join(' · ') ||
              'No directional conflicts reported'}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2 xl:grid-cols-4">
          {TIMEFRAMES.map((tf) => (
            <EvidenceCard
              key={tf}
              timeframe={tf}
              analysis={analysis ?? undefined}
              active={timeframe === tf}
              onClick={() => setTimeframe(tf)}
            />
          ))}
        </div>
      </div>
      <div className="border-t border-border/70 p-3">
        <PullbackResearch research={row.entryResearch} />
      </div>
      <footer className="grid gap-3 border-t border-border/70 bg-background/20 p-3 text-[10px] sm:grid-cols-3">
        <div>
          <p className="eyebrow mb-1">Market evidence</p>
          <p>
            Observed <Stamp value={analysis?.observedAt ?? null} />
          </p>
          <p className="mt-1">
            Exchange <Stamp value={analysis?.quote.exchangeAt ?? null} />
          </p>
        </div>
        <div>
          <p className="eyebrow mb-1">Legacy indicators</p>
          <p>
            1H / 15M trend · {row.indicators?.trend ?? 'Unavailable'} /{' '}
            {row.indicators?.trend15M ?? 'Unavailable'}
          </p>
          <p className="mt-1">
            MACD · {row.indicators?.macdDirection ?? 'Unavailable'} /{' '}
            {row.indicators?.macdDirection15M ?? 'Unavailable'} · volume{' '}
            {row.indicators?.volumeStrength ?? 'Unavailable'}
          </p>
        </div>
        <div>
          <p className="eyebrow mb-1">Instrument rules</p>
          <p>{row.instrument?.instrumentId ?? 'Unavailable'}</p>
          <p className="mt-1">
            Min size {text(row.instrument?.minSize, '—')} · lot{' '}
            {text(row.instrument?.lotSize, '—')} · tick{' '}
            {text(row.instrument?.tickSize, '—')}
          </p>
        </div>
      </footer>
    </section>
  );
}

export default function MarketScannerPage() {
  const marketQuery = useGetMarketScanner({
    query: { queryKey: getGetMarketScannerQueryKey(), refetchInterval: 30000 },
  });
  const intelligenceQuery = useGetMarketIntelligence({
    query: {
      queryKey: getGetMarketIntelligenceQueryKey(),
      refetchInterval: 60000,
    },
  });
  const committeeQuery = useGetCommitteeOverview({
    query: {
      queryKey: getGetCommitteeOverviewQueryKey(),
      refetchInterval: 30000,
    },
  });
  const proposalQuery = useGetProposalCenter({
    query: { queryKey: getGetProposalCenterQueryKey(), refetchInterval: 30000 },
  });
  const [view, setView] = useState<View>('opportunities');
  const [market, setMarket] = useState<Market>('all');
  const [direction, setDirection] = useState<Direction>('all');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [minimum, setMinimum] = useState('0');
  const [timeframe, setTimeframe] = useState<(typeof TIMEFRAMES)[number]>('1H');
  const [sort, setSort] = useState<Sort>({ key: 'symbol', direction: 'asc' });
  const [picked, setPicked] = useState<string | null>(null);
  const allRows = marketQuery.data?.rows ?? EMPTY_ROWS;
  const intelligence =
    intelligenceQuery.data?.instruments ?? EMPTY_INTELLIGENCE;
  const rows = useMemo(() => {
    const filtered = allRows.filter((row) => {
      const intelligenceRow = matchAnalysis(intelligence, row);
      if (market !== 'all' && row.marketType !== market) return false;
      if (search && !row.symbol.toLowerCase().includes(search.toLowerCase()))
        return false;
      if (!intelligenceRow) {
        return direction === 'all' && status === 'all' && !asNum(minimum);
      }
      if (
        (direction !== 'all' || (asNum(minimum) ?? 0) > 0) &&
        intelligenceRow.evidence.status !== 'complete'
      )
        return false;
      const bull = asNum(intelligenceRow.evidence.bullishScore);
      const bear = asNum(intelligenceRow.evidence.bearishScore);
      if (
        direction === 'long' &&
        (bull === null || bull <= (bear ?? -Infinity))
      )
        return false;
      if (
        direction === 'short' &&
        (bear === null || bear <= (bull ?? -Infinity))
      )
        return false;
      const score =
        direction === 'short'
          ? bear
          : direction === 'long'
            ? bull
            : Math.max(bull ?? -Infinity, bear ?? -Infinity);
      if (asNum(minimum) && (score === null || score < Number(minimum)))
        return false;
      if (status !== 'all') {
        if (
          !intelligenceRow.opportunity.state
            .toLowerCase()
            .includes(status.toLowerCase())
        )
          return false;
      }
      return true;
    });
    const valueFor = (row: MarketScannerRow): string | number => {
      const proposal = proposalQuery.data?.proposals.find(
        (p) =>
          normalized(p.instrument).includes(normalized(row.symbol)) &&
          p.marketType === row.marketType,
      );
      const candidate = proposalQuery.data?.candidates.find(
        (c) =>
          normalized(c.symbol) === normalized(row.symbol) &&
          c.marketType === row.marketType,
      );
      const run = committeeQuery.data?.runs.find(
        (r) =>
          normalized(r.symbol) === normalized(row.symbol) &&
          r.marketType === row.marketType,
      );
      switch (sort.key) {
        case 'symbol':
          return row.symbol;
        case 'lastPrice':
          return (
            asNum(
              matchAnalysis(intelligence, row)?.quote.lastPrice ??
                row.lastPrice,
            ) ?? -Infinity
          );
        case 'changePct24H':
          return (
            asNum(
              matchAnalysis(intelligence, row)?.quote.changePct24H ??
                row.changePct24H,
            ) ?? -Infinity
          );
        case 'volume24H':
          return (
            asNum(
              matchAnalysis(intelligence, row)?.quote.volume24H ??
                row.volume24H,
            ) ?? -Infinity
          );
        case 'bullish':
          return (
            asNum(matchAnalysis(intelligence, row)?.evidence.bullishScore) ??
            -Infinity
          );
        case 'bearish':
          return (
            asNum(matchAnalysis(intelligence, row)?.evidence.bearishScore) ??
            -Infinity
          );
        case 'rsi':
          return (
            matchAnalysis(intelligence, row)?.timeframes.find(
              (item) => item.timeframe === '1h',
            )?.rsi14 ?? -Infinity
          );
        case 'marketType':
          return row.marketType;
        case 'bias':
          return (
            matchAnalysis(intelligence, row)?.evidence.classification ?? ''
          );
        case 'observedAt':
          return row.observedAt ?? '';
        case 'status':
          return matchAnalysis(intelligence, row)?.opportunity.state ?? '';
        case 'direction':
          return proposal?.side ?? candidate?.side ?? '';
        case 'review':
          return run?.status ?? '';
        case 'recommendation':
          return text(
            proposal?.details?.recommendation,
            proposal?.decisionReason ?? '',
          );
        case 'approval':
          return proposal?.status ?? '';
        default:
          return '';
      }
    };
    return filtered.sort((a, b) => {
      const aa = valueFor(a);
      const bb = valueFor(b);
      const result =
        typeof aa === 'string' && typeof bb === 'string'
          ? aa.localeCompare(bb)
          : Number(aa) - Number(bb);
      return sort.direction === 'asc' ? result : -result;
    });
  }, [
    allRows,
    intelligence,
    committeeQuery.data,
    direction,
    market,
    minimum,
    proposalQuery.data,
    search,
    sort,
    status,
  ]);
  const selectedKey =
    picked && rows.some((row) => rowKey(row) === picked)
      ? picked
      : rows[0]
        ? rowKey(rows[0])
        : null;
  const selectedRow =
    allRows.find((row) => rowKey(row) === selectedKey) ?? null;
  const statusOptions = Array.from(
    new Set(intelligence.map((row) => row.opportunity.state)),
  );
  const freshness = intelligence.reduce(
    (counts, row) => {
      const status = row.quote.status;
      return { ...counts, [status]: counts[status] + 1 };
    },
    { fresh: 0, stale: 0, unavailable: 0 },
  );
  const marketDataOutage =
    intelligence.length === 6 &&
    intelligence.every((item) => item.quote.status === 'unavailable');
  const selectedAnalysis = selectedRow
    ? (matchAnalysis(intelligence, selectedRow) ?? null)
    : null;
  const onSortColumn = (key: string) =>
    setSort((old) =>
      old.key === key
        ? { key, direction: old.direction === 'asc' ? 'desc' : 'asc' }
        : { key, direction: 'asc' },
    );
  const resetFilters = () => {
    setMarket('all');
    setDirection('all');
    setSearch('');
    setStatus('all');
    setMinimum('0');
  };
  const onTabKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const index = VIEWS.findIndex((item) => item.id === view);
    const next =
      event.key === 'Home'
        ? 0
        : event.key === 'End'
          ? VIEWS.length - 1
          : (index + (event.key === 'ArrowRight' ? 1 : -1) + VIEWS.length) %
            VIEWS.length;
    setView(VIEWS[next].id);
    document
      .querySelector<HTMLButtonElement>(`[data-testid="tab-${VIEWS[next].id}"]`)
      ?.focus();
  };

  return (
    <main
      data-testid="page-market-scanner"
      className="mx-auto min-h-[100dvh] max-w-[1600px] px-3 py-4 sm:px-5 lg:px-7 lg:py-6"
    >
      <div className="desk-grid rounded-sm border border-border/70 bg-card/45 p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">STAI · Market intelligence / 03</p>
            <h1 className="mt-1 flex flex-wrap items-center gap-2 text-[23px] font-semibold tracking-tight sm:text-[27px]">
              Market Scanner <PaperLabel />
            </h1>
            <p className="mt-1 text-[11px] tracking-wide text-muted-foreground">
              Multi-Timeframe Market Intelligence{' '}
              <span className="mx-1.5 text-border">/</span> Public OKX market
              data
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-2 rounded border border-teal/30 bg-teal/[0.06] px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-teal">
              <span className="h-1.5 w-1.5 rounded-full bg-teal" />
              OKX
            </span>
            <span className="rounded border border-warn/35 bg-warn/[0.05] px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-warn">
              Paper · research only
            </span>
            <button
              type="button"
              data-testid="button-refresh-scanner"
              onClick={() => {
                void marketQuery.refetch();
                void intelligenceQuery.refetch();
                void committeeQuery.refetch();
                void proposalQuery.refetch();
              }}
              disabled={marketQuery.isFetching || intelligenceQuery.isFetching}
              className="focus-ring inline-flex h-8 items-center gap-2 rounded border border-border bg-card px-3 text-[10px] hover:border-teal/50 disabled:opacity-60"
            >
              <RefreshCw
                className={cn(
                  'h-3 w-3 text-teal',
                  (marketQuery.isFetching || intelligenceQuery.isFetching) &&
                    'animate-spin',
                )}
              />
              {marketQuery.isFetching || intelligenceQuery.isFetching
                ? 'Refreshing'
                : 'Refresh'}
            </button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-3">
          <div
            data-testid="text-freshness-counts"
            className="flex flex-wrap gap-x-5 gap-y-2 text-[10px]"
          >
            <span className="inline-flex items-center gap-1.5 text-profit">
              <i className="h-1.5 w-1.5 rounded-full bg-profit" />
              {freshness.fresh} fresh quotes
            </span>
            <span className="inline-flex items-center gap-1.5 text-warn">
              <i className="h-1.5 w-1.5 rounded-full bg-warn" />
              {freshness.stale} stale quotes
            </span>
            <span className="inline-flex items-center gap-1.5 text-loss">
              <i className="h-1.5 w-1.5 rounded-full bg-loss" />
              {freshness.unavailable} unavailable
            </span>
            <span className="text-muted-foreground">
              {intelligenceQuery.data ? (
                <>
                  MTF snapshot{' '}
                  <span
                    title={`${formatUtcDateTime(intelligenceQuery.data.observedAt)} UTC`}
                  >
                    {formatManilaTime(intelligenceQuery.data.observedAt)} MNL
                  </span>{' '}
                  · {intelligenceQuery.data.provider}
                </>
              ) : (
                'Waiting for market intelligence'
              )}
            </span>
          </div>
          <p className="inline-flex items-center gap-1.5 text-[9px] uppercase tracking-wider text-muted-foreground">
            <ShieldCheck className="h-3 w-3 text-teal" />
            Private owner terminal · paper only
          </p>
        </div>
      </div>

      {marketDataOutage && (
        <div
          role="alert"
          className="mt-3 rounded-md border border-loss/40 bg-loss/[0.07] p-3 text-sm"
        >
          <p className="font-medium">Market data outage</p>
          <p className="mt-0.5 text-muted-foreground">
            All six MTF instruments are unavailable. No values are substituted.
          </p>
        </div>
      )}

      {(marketQuery.isError ||
        intelligenceQuery.isError ||
        committeeQuery.isError ||
        proposalQuery.isError) && (
        <div className="mt-3">
          <ErrorNote
            error={
              intelligenceQuery.error ??
              marketQuery.error ??
              committeeQuery.error ??
              proposalQuery.error
            }
            title={
              marketQuery.isError
                ? 'Scanner data could not be loaded'
                : intelligenceQuery.isError
                  ? 'Market intelligence could not be loaded'
                  : 'A refresh failed. Showing the last successful snapshot.'
            }
            onRetry={() => {
              void marketQuery.refetch();
              void intelligenceQuery.refetch();
              void committeeQuery.refetch();
              void proposalQuery.refetch();
            }}
          />
        </div>
      )}
      {(marketQuery.isLoading || intelligenceQuery.isLoading) && (
        <div className="panel mt-3 space-y-2 p-4" aria-busy="true">
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-9 bg-muted" />
          ))}
        </div>
      )}

      {marketQuery.data && (
        <>
          <div
            className="mt-4 border-b border-border/80"
            role="tablist"
            aria-label="Market screener views"
            onKeyDown={onTabKeyDown}
          >
            <div className="flex gap-1 overflow-x-auto">
              {VIEWS.map((item) => (
                <button
                  key={item.id}
                  id={`tab-${item.id}`}
                  type="button"
                  role="tab"
                  aria-selected={view === item.id}
                  aria-controls="screener-view-panel"
                  tabIndex={view === item.id ? 0 : -1}
                  data-testid={`tab-${item.id}`}
                  onClick={() => setView(item.id)}
                  className={cn(
                    'focus-ring shrink-0 border-b-2 px-3 py-2.5 text-[11px] transition-colors',
                    view === item.id
                      ? 'border-teal text-teal'
                      : 'border-transparent text-muted-foreground hover:text-foreground',
                  )}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          <section
            id="screener-view-panel"
            role="tabpanel"
            aria-labelledby={`tab-${view}`}
            className="mt-3"
          >
            <div className="panel mb-3 p-3">
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-[minmax(180px,1.25fr)_repeat(5,minmax(115px,.7fr))_auto]">
                <label className="relative block">
                  <span className="sr-only">Search symbol</span>
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    data-testid="input-symbol-search"
                    type="search"
                    placeholder="Search instrument"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="focus-ring h-8 w-full rounded border border-input bg-background pl-8 pr-2 text-[11px]"
                  />
                </label>
                <label className="sr-only" htmlFor="market-filter">
                  Market type
                </label>
                <select
                  id="market-filter"
                  data-testid="filter-market-type"
                  value={market}
                  onChange={(e) => setMarket(e.target.value as Market)}
                  className="focus-ring h-8 rounded border border-input bg-background px-2 text-[11px]"
                >
                  <option value="all">All markets</option>
                  <option value="spot">Spot</option>
                  <option value="futures">Perpetual</option>
                </select>
                <label className="sr-only" htmlFor="direction-filter">
                  Direction
                </label>
                <select
                  id="direction-filter"
                  data-testid="filter-direction"
                  value={direction}
                  onChange={(e) => setDirection(e.target.value as Direction)}
                  className="focus-ring h-8 rounded border border-input bg-background px-2 text-[11px]"
                >
                  <option value="all">All directions</option>
                  <option value="long">Long evidence</option>
                  <option value="short">Short evidence</option>
                </select>
                <label className="sr-only" htmlFor="timeframe-filter">
                  Timeframe
                </label>
                <select
                  id="timeframe-filter"
                  data-testid="filter-timeframe"
                  value={timeframe}
                  onChange={(e) =>
                    setTimeframe(e.target.value as typeof timeframe)
                  }
                  className="focus-ring h-8 rounded border border-input bg-background px-2 text-[11px]"
                >
                  <option value="1D">1D</option>
                  <option value="4H">4H</option>
                  <option value="1H">1H</option>
                  <option value="15M">15M</option>
                </select>
                <label className="sr-only" htmlFor="status-filter">
                  Opportunity status
                </label>
                <select
                  id="status-filter"
                  data-testid="filter-status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="focus-ring h-8 rounded border border-input bg-background px-2 text-[11px]"
                >
                  <option value="all">All statuses</option>
                  {statusOptions.map((item) => (
                    <option key={item} value={item}>
                      {item.replaceAll('_', ' ')}
                    </option>
                  ))}
                </select>
                <label className="flex h-8 items-center gap-2 rounded border border-input bg-background px-2 text-[10px] text-muted-foreground">
                  <span className="whitespace-nowrap">Min score</span>
                  <input
                    data-testid="filter-min-score"
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={minimum}
                    onChange={(e) => setMinimum(e.target.value)}
                    className="num w-full bg-transparent text-right text-[11px] text-foreground outline-none"
                  />
                </label>
                <button
                  type="button"
                  data-testid="button-reset-filters"
                  onClick={resetFilters}
                  className="focus-ring h-8 rounded border border-border px-3 text-[10px] text-muted-foreground hover:text-foreground"
                >
                  Reset
                </button>
              </div>
              <div className="mt-2 flex items-center justify-between gap-2 text-[9px] text-muted-foreground">
                <span>
                  Balanced scores are research classifications; they are not
                  probabilities or trading eligibility.
                </span>
                <span className="num">
                  {rows.length} / {allRows.length} rows
                </span>
              </div>
            </div>

            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between gap-3 border-b border-border/70 px-3 py-2.5">
                <div>
                  <p className="eyebrow">
                    {VIEWS.find((item) => item.id === view)?.label} · live
                    screener
                  </p>
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    {view === 'opportunities'
                      ? 'Versioned research states; indicative setups never become proposals.'
                      : view === 'committee'
                        ? 'Persisted committee history/status only. No review is triggered.'
                        : 'Read-only OKX observations; indicators use completed candles.'}
                  </p>
                </div>
                <span className="inline-flex items-center gap-1.5 font-mono text-[9px] uppercase text-muted-foreground">
                  <Activity className="h-3 w-3 text-teal" />
                  60s MTF
                </span>
              </div>
              <MarketTable
                rows={rows}
                intelligence={intelligence}
                view={view}
                sort={sort}
                onSort={onSortColumn}
                selected={selectedKey}
                onSelect={setPicked}
                proposal={proposalQuery.data}
                committee={committeeQuery.data}
              />
              {view === 'committee' && committeeQuery.data && (
                <div className="grid gap-2 border-t border-border/60 p-3 text-[10px] text-muted-foreground sm:grid-cols-3">
                  <div>
                    Roles {committeeQuery.data.roles.length} · existing runs{' '}
                    {committeeQuery.data.runs.length}
                  </div>
                  <div>
                    Paid automation{' '}
                    {committeeQuery.data.paidAutomationEnabled
                      ? 'enabled'
                      : 'disabled'}{' '}
                    · manual paid runs{' '}
                    {committeeQuery.data.manualPaidRunsEnabled
                      ? 'enabled'
                      : 'disabled'}
                  </div>
                  <div>
                    Entry gate {committeeQuery.data.entryGate} · new MTF
                    committee submissions disabled
                  </div>
                </div>
              )}
            </div>
            {allRows.length > 0 && selectedRow && (
              <div className="mt-3">
                <DetailPanel
                  row={selectedRow}
                  analysis={selectedAnalysis}
                  timeframe={timeframe}
                  setTimeframe={setTimeframe}
                  proposals={proposalQuery.data}
                  committee={committeeQuery.data}
                />
              </div>
            )}
            {allRows.length === 0 && (
              <div className="panel mt-3 px-5 py-10 text-center">
                <p className="text-sm font-medium">No market rows returned</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  The public market scanner has no instruments in this snapshot.
                  Nothing is substituted.
                </p>
              </div>
            )}
            <p className="mt-3 text-[9px] leading-relaxed text-muted-foreground">
              Research disclosure: Balanced v1 scores, 0.25 ATR structure, and
              the new opportunity state machine are unvalidated research
              hypotheses; they do not alter EMA screening, the structural
              challenger, trade gates, committee controls, or execution. No AI
              call is made. Timestamps display in Manila time; hover for UTC.
            </p>
          </section>
        </>
      )}
    </main>
  );
}
