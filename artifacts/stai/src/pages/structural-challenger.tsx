import { useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Check,
  ChevronDown,
  Clock3,
  Database,
  LockKeyhole,
  ShieldCheck,
  Target,
} from 'lucide-react';
import {
  getGetStructuralChallengerBacktestQueryKey,
  getGetStructuralChallengerOverviewQueryKey,
  getListStructuralChallengerBacktestsQueryKey,
  useCreateStructuralChallengerBacktest,
  useGetStructuralChallengerBacktest,
  useGetStructuralChallengerOverview,
  useListStructuralChallengerBacktests,
  type StructuralBacktestInput,
  type StructuralBacktestResult,
  type StructuralCandidateEvidence,
  type StructuralEntryOrder,
  type StructuralRunListItem,
  type StructuralSegment,
  type StructuralStrategyConfiguration,
  type StructuralTrade,
  type StructuralWindow,
} from '@workspace/api-client-react';
import { cn } from '@/lib/utils';
import { ErrorNote } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';
import './structural-challenger.css';

const INSTRUMENTS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'] as const;
type Instrument = (typeof INSTRUMENTS)[number];

function numberOf(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null;
  const valueAsNumber = Number(value);
  return Number.isFinite(valueAsNumber) ? valueAsNumber : null;
}

function numeric(value: number | string | null | undefined, digits = 2) {
  const number = numberOf(value);
  return number === null
    ? '—'
    : number.toLocaleString('en-US', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
}

function amount(value: number | string | null | undefined, digits = 2) {
  const number = numberOf(value);
  if (number === null) return '—';
  return `${number < 0 ? '−' : ''}${Math.abs(number).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })} USDT`;
}

function pct(value: number | string | null | undefined) {
  const number = numberOf(value);
  return number === null ? '—' : `${number.toFixed(2)}%`;
}

function dateLabel(value: string | null | undefined) {
  if (!value) return 'Pending';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

function dateTime(value: string | null | undefined) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  });
}

function tone(value: number | string | null | undefined) {
  const number = numberOf(value);
  return number === null
    ? 'text-muted-foreground'
    : number > 0
      ? 'text-profit'
      : number < 0
        ? 'text-loss'
        : 'text-foreground';
}

function entryLabel(value: string) {
  return value === 'anchor_limit' ? 'Anchor limit' : 'Next-candle market';
}

function methodKey(segment: StructuralSegment) {
  return [
    segment.marketType,
    segment.side,
    segment.entryMethod,
    segment.maxHoldMinutes,
  ].join('|');
}

function SegmentName({ segment }: { segment: StructuralSegment }) {
  const Icon = segment.side === 'long' ? ArrowUpRight : ArrowDownRight;
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <span className="capitalize">{segment.marketType}</span>
      <span className="text-muted-foreground">/</span>
      <span className={segment.side === 'long' ? 'text-profit' : 'text-loss'}>
        <Icon className="mr-0.5 inline h-3 w-3" aria-hidden />
        <span className="capitalize">{segment.side}</span>
      </span>
      <span className="text-muted-foreground">/</span>
      <span>{entryLabel(segment.entryMethod)}</span>
      <span className="text-muted-foreground">/</span>
      <span className="sc-tabular">{segment.maxHoldMinutes}m</span>
    </span>
  );
}

function WindowCard({
  window,
  label,
  testId,
}: {
  window: StructuralWindow;
  label: string;
  testId: string;
}) {
  const pending = window.status === 'pending';
  return (
    <article
      className={cn(
        'rounded border p-3.5',
        pending
          ? 'border-warn/30 bg-warn/[0.045]'
          : 'border-border/70 bg-background/25',
      )}
      data-testid={testId}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="eyebrow">{label}</p>
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded border px-1.5 py-1 font-mono text-[9px] uppercase tracking-[0.12em]',
            pending
              ? 'border-warn/35 bg-warn/[0.06] text-warn'
              : 'border-profit/30 bg-profit/[0.06] text-profit',
          )}
          data-testid={`status-${testId}`}
        >
          {pending ? (
            <LockKeyhole className="h-3 w-3" aria-hidden />
          ) : (
            <Check className="h-3 w-3" aria-hidden />
          )}
          {pending ? 'Pending' : 'Ready'}
        </span>
      </div>
      <p className="sc-tabular mt-2 text-[12px] font-medium">
        {dateLabel(window.startsAt)}{' '}
        <span className="text-muted-foreground">—</span>{' '}
        {dateLabel(window.endsAt)}
      </p>
      <p className="mt-1 text-[10.5px] leading-relaxed text-muted-foreground">
        {window.note}
      </p>
    </article>
  );
}

function StrategyDefinition({
  strategy,
}: {
  strategy: StructuralStrategyConfiguration;
}) {
  const rows = [
    [
      'Structure',
      `${strategy.trendTimeframe} regime · ${strategy.entryTimeframe} entry`,
    ],
    ['Entry comparison', strategy.entryMethods.map(entryLabel).join(' vs ')],
    [
      'Structural stop',
      `${numeric(strategy.structuralStopBufferAtr)} ATR beyond zone`,
    ],
    [
      'Target placement',
      `${numeric(strategy.targetOffsetBeforeZoneAtr)} ATR before opposing zone`,
    ],
    [
      'Net reward / risk gate',
      `${numeric(strategy.minimumNetRewardRisk)} : 1 minimum`,
    ],
    [
      'Maximum holds',
      strategy.holdingPeriodsMinutes
        .map((minutes) => `${minutes}m`)
        .join(' · '),
    ],
    [
      'Market-cost sweep',
      strategy.marketCostSensitivityBps.map((bps) => `${bps} bps`).join(' · '),
    ],
    [
      'Sizing assumptions',
      `${numeric(strategy.notionalUsdt, 0)} USDT · ${numeric(strategy.leverage, 0)}×`,
    ],
  ];
  return (
    <section
      className="overflow-hidden rounded border border-border/70 bg-card/80"
      data-testid="section-structural-strategy"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-[hsl(var(--sc-lime))]" aria-hidden />
          <h2 className="text-[12.5px] font-semibold">
            Approved fixed definition
          </h2>
        </div>
        <span
          className="sc-tabular rounded border border-[hsl(var(--sc-lime)/.32)] bg-[hsl(var(--sc-lime)/.07)] px-2 py-1 text-[10px] text-[hsl(var(--sc-lime))]"
          data-testid="text-structural-strategy-version"
        >
          {strategy.strategyVersion}
        </span>
      </header>
      <dl className="grid gap-x-7 px-4 py-1 sm:grid-cols-2 xl:grid-cols-4">
        {rows.map(([label, value]) => (
          <div
            key={label}
            className="border-b border-border/40 py-2.5 last:border-0"
          >
            <dt className="eyebrow">{label}</dt>
            <dd className="mt-1 text-[11.5px] leading-relaxed">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="border-t border-border/50 bg-background/25 px-4 py-2.5">
        <p
          className="text-[10.5px] leading-relaxed text-muted-foreground"
          data-testid="text-structural-no-lookahead"
        >
          {strategy.noLookaheadRule}
          {strategy.executionAssumptions.length > 0 &&
            ` Assumptions: ${strategy.executionAssumptions.join(' · ')}`}
        </p>
      </div>
    </section>
  );
}

function RunOption({ run }: { run: StructuralRunListItem }) {
  return (
    <>
      {run.symbol} · {run.samplePeriod.replaceAll('_', ' ')} ·{' '}
      {dateLabel(run.createdAt)} · {run.completedTrades} fills
    </>
  );
}

function SummaryMatrix({ segments }: { segments: StructuralSegment[] }) {
  if (!segments.length) {
    return (
      <div
        className="px-4 py-8 text-center"
        data-testid="empty-structural-segments"
      >
        <BarChart3
          className="mx-auto h-5 w-5 text-muted-foreground/60"
          aria-hidden
        />
        <p className="mt-2 text-[12px] font-medium">
          No segment results returned
        </p>
        <p className="mt-1 text-[10.5px] text-muted-foreground">
          This run contains no market, side, entry or hold combinations.
        </p>
      </div>
    );
  }
  return (
    <div className="sc-table-scroll overflow-x-auto">
      <table
        className="w-full min-w-[1450px] text-left text-[10.5px]"
        data-testid="table-structural-summary"
      >
        <thead className="bg-background/25">
          <tr>
            {[
              'Market / side / entry / hold',
              'Cost',
              'Candidates',
              'R/R rejected',
              'Orders placed',
              'Filled / unfilled',
              'Untestable',
              'Overlap skipped',
              'Expectancy',
              'Net P&L',
              'Win rate',
              'Drawdown',
              'Fees',
              'Funding',
              'Market costs',
            ].map((label) => (
              <th
                scope="col"
                key={label}
                className="eyebrow whitespace-nowrap border-b border-border/60 px-3 py-2.5 font-normal first:pl-4 last:pr-4"
              >
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {segments.flatMap((segment, segmentIndex) =>
            segment.costResults.map((cost) => {
              const key = `${methodKey(segment)}|${cost.marketCostBps}`;
              return (
                <tr
                  key={key}
                  className="border-b border-border/35 transition-colors hover:bg-background/25"
                  data-testid={`row-structural-summary-${segmentIndex}-${cost.marketCostBps}`}
                >
                  <td className="px-3 py-2.5 pl-4">
                    <SegmentName segment={segment} />
                  </td>
                  <td className="sc-tabular whitespace-nowrap px-3 py-2.5">
                    {cost.marketCostBps} bps
                  </td>
                  <td className="sc-tabular px-3 py-2.5">
                    {segment.candidateCount.toLocaleString()}
                  </td>
                  <td className="sc-tabular px-3 py-2.5">
                    {segment.rewardRiskRejected.toLocaleString()}
                  </td>
                  <td className="sc-tabular px-3 py-2.5">
                    {segment.ordersPlaced.toLocaleString()}
                  </td>
                  <td className="sc-tabular whitespace-nowrap px-3 py-2.5">
                    {segment.ordersFilled} / {segment.unfilledLimits}
                  </td>
                  <td className="sc-tabular px-3 py-2.5">
                    {segment.untestableCandidates.toLocaleString()}
                  </td>
                  <td className="sc-tabular px-3 py-2.5">
                    {segment.overlappingSignalsSkipped.toLocaleString()}
                  </td>
                  <td
                    className={cn(
                      'sc-tabular whitespace-nowrap px-3 py-2.5',
                      tone(cost.metrics.expectancyUsdt),
                    )}
                  >
                    {amount(cost.metrics.expectancyUsdt)}
                  </td>
                  <td
                    className={cn(
                      'sc-tabular whitespace-nowrap px-3 py-2.5',
                      tone(cost.metrics.cumulativePnlUsdt),
                    )}
                  >
                    {amount(cost.metrics.cumulativePnlUsdt)}
                  </td>
                  <td className="sc-tabular px-3 py-2.5">
                    {pct(cost.metrics.winRatePct)}
                  </td>
                  <td className="sc-tabular whitespace-nowrap px-3 py-2.5 text-loss">
                    {amount(cost.metrics.maxDrawdownUsdt)}{' '}
                    <span className="text-muted-foreground">
                      · {pct(cost.metrics.maxDrawdownPct)}
                    </span>
                  </td>
                  <td className="sc-tabular whitespace-nowrap px-3 py-2.5">
                    {amount(cost.metrics.totalFeesUsdt)}
                  </td>
                  <td
                    className={cn(
                      'sc-tabular whitespace-nowrap px-3 py-2.5',
                      tone(cost.metrics.totalFundingUsdt),
                    )}
                  >
                    {amount(cost.metrics.totalFundingUsdt)}
                  </td>
                  <td className="sc-tabular whitespace-nowrap px-3 py-2.5 pr-4">
                    {amount(
                      numberOf(cost.metrics.totalSpreadCostUsdt) === null &&
                        numberOf(cost.metrics.totalSlippageCostUsdt) === null
                        ? null
                        : (numberOf(cost.metrics.totalSpreadCostUsdt) ?? 0) +
                            (numberOf(cost.metrics.totalSlippageCostUsdt) ?? 0),
                    )}
                  </td>
                </tr>
              );
            }),
          )}
        </tbody>
      </table>
    </div>
  );
}

function TradeTable({ trades }: { trades: StructuralTrade[] }) {
  if (!trades.length) {
    return (
      <div
        className="px-4 py-9 text-center"
        data-testid="empty-structural-trades"
      >
        <p className="text-[12px] font-medium">
          No filled trades in this slice
        </p>
        <p className="mt-1 text-[10.5px] text-muted-foreground">
          Unfilled anchor orders are listed separately and are not counted as
          trades.
        </p>
      </div>
    );
  }
  return (
    <div className="sc-table-scroll overflow-x-auto">
      <table
        className="w-full min-w-[1320px] text-left text-[10px]"
        data-testid="table-structural-trades"
      >
        <thead>
          <tr>
            {[
              'Signal / entry',
              'Side',
              'Entry method',
              'Proposed / fill',
              'Stop',
              'Target',
              'Exit / reason',
              'Hold',
              'Gross',
              'Fees',
              'Funding',
              'Modeled cost',
              'Net',
            ].map((label) => (
              <th
                key={label}
                className="eyebrow whitespace-nowrap border-b border-border/60 bg-background/25 px-2.5 py-2.5 font-normal first:pl-4 last:pr-4"
              >
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, index) => (
            <tr
              key={`${trade.candidateId}-${trade.enteredAt}-${index}`}
              className="border-b border-border/35 hover:bg-background/20"
              data-testid={`row-structural-trade-${index}`}
            >
              <td className="sc-tabular whitespace-nowrap px-2.5 py-2.5 pl-4">
                {dateTime(trade.signalAt)}
                <span className="block text-muted-foreground">
                  {dateTime(trade.enteredAt)}
                </span>
              </td>
              <td
                className={cn(
                  'px-2.5 py-2.5 capitalize',
                  trade.side === 'long' ? 'text-profit' : 'text-loss',
                )}
              >
                {trade.side}
              </td>
              <td className="px-2.5 py-2.5 whitespace-nowrap">
                {entryLabel(trade.entryMethod)}
              </td>
              <td className="sc-tabular whitespace-nowrap px-2.5 py-2.5">
                {numeric(trade.proposedEntryPrice, 4)}
                <span className="block text-muted-foreground">
                  {numeric(trade.entryPrice, 4)} fill
                </span>
              </td>
              <td className="sc-tabular px-2.5 py-2.5 text-loss">
                {numeric(trade.stopPrice, 4)}
              </td>
              <td className="sc-tabular px-2.5 py-2.5 text-profit">
                {numeric(trade.targetPrice, 4)}
              </td>
              <td className="sc-tabular whitespace-nowrap px-2.5 py-2.5">
                {numeric(trade.exitPrice, 4)}
                <span className="block capitalize text-muted-foreground">
                  {trade.exitReason.replaceAll('_', ' ')} ·{' '}
                  {dateTime(trade.exitedAt)}
                </span>
              </td>
              <td className="sc-tabular px-2.5 py-2.5">
                {trade.holdingMinutes}m
              </td>
              <td
                className={cn(
                  'sc-tabular whitespace-nowrap px-2.5 py-2.5',
                  tone(trade.grossPnlUsdt),
                )}
              >
                {amount(trade.grossPnlUsdt)}
              </td>
              <td className="sc-tabular whitespace-nowrap px-2.5 py-2.5">
                {amount(trade.feesUsdt)}
              </td>
              <td
                className={cn(
                  'sc-tabular whitespace-nowrap px-2.5 py-2.5',
                  tone(trade.fundingUsdt),
                )}
              >
                {amount(trade.fundingUsdt)}
              </td>
              <td className="sc-tabular whitespace-nowrap px-2.5 py-2.5">
                {amount(trade.modeledMarketCostUsdt)}
              </td>
              <td
                className={cn(
                  'sc-tabular whitespace-nowrap px-2.5 py-2.5 pr-4 font-medium',
                  tone(trade.netPnlUsdt),
                )}
              >
                {amount(trade.netPnlUsdt)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UnfilledOrders({ orders }: { orders: StructuralEntryOrder[] }) {
  const notFilled = orders.filter((order) => order.status !== 'filled');
  return (
    <section
      className="border-t border-border/55"
      data-testid="section-structural-orders"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
        <div>
          <h3 className="text-[11.5px] font-medium">Entry orders not filled</h3>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            Limit misses, cancellations, rejections and untestable candidates
            are excluded from trade metrics.
          </p>
        </div>
        <span className="sc-tabular text-[10px] text-muted-foreground">
          {notFilled.length} unfilled / non-fill
        </span>
      </header>
      {!notFilled.length ? (
        <p className="border-t border-border/35 px-4 py-3 text-[10.5px] text-muted-foreground">
          No unfilled orders were returned for this segment.
        </p>
      ) : (
        <div className="sc-table-scroll overflow-x-auto">
          <table
            className="w-full min-w-[820px] text-left text-[10px]"
            data-testid="table-structural-orders"
          >
            <thead>
              <tr>
                {[
                  'Signal',
                  'Side',
                  'Entry method',
                  'Proposed price',
                  'Net R:R',
                  'Expires',
                  'Status',
                  'Reason',
                ].map((label) => (
                  <th
                    key={label}
                    className="eyebrow border-y border-border/40 px-3 py-2 font-normal first:pl-4"
                  >
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {notFilled.map((order, index) => (
                <tr
                  key={`${order.candidateId}-${order.signalAt}-${index}`}
                  className="border-b border-border/30"
                  data-testid={`row-structural-order-${index}`}
                >
                  <td className="sc-tabular whitespace-nowrap px-3 py-2 pl-4">
                    {dateTime(order.signalAt)}
                  </td>
                  <td
                    className={cn(
                      'px-3 py-2 capitalize',
                      order.side === 'long' ? 'text-profit' : 'text-loss',
                    )}
                  >
                    {order.side}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    {entryLabel(order.entryMethod)}
                  </td>
                  <td className="sc-tabular px-3 py-2">
                    {numeric(order.proposedPrice, 4)}
                  </td>
                  <td className="sc-tabular px-3 py-2">
                    {numeric(order.plannedNetRewardRisk)} : 1
                  </td>
                  <td className="sc-tabular whitespace-nowrap px-3 py-2">
                    {dateTime(order.expiresAt)}
                  </td>
                  <td className="px-3 py-2 capitalize">{order.status}</td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {order.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function EvidenceList({
  evidence,
}: {
  evidence: StructuralCandidateEvidence[];
}) {
  return (
    <section
      className="overflow-hidden rounded border border-border/70 bg-card/80"
      data-testid="section-candidate-evidence"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 px-4 py-3">
        <div className="flex items-center gap-2">
          <Database className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
          <h2 className="text-[11.5px] font-semibold">
            Candidate evidence snapshots
          </h2>
        </div>
        <span className="sc-tabular text-[10px] text-muted-foreground">
          {evidence.length} records · committee not run
        </span>
      </header>
      {!evidence.length ? (
        <p
          className="px-4 py-5 text-[10.5px] text-muted-foreground"
          data-testid="empty-candidate-evidence"
        >
          No candidate evidence snapshots returned for this run.
        </p>
      ) : (
        <div className="max-h-[340px] divide-y divide-border/35 overflow-auto">
          {evidence.map((item, index) => (
            <details
              key={item.candidateId}
              className="group px-4 py-2.5"
              data-testid={`evidence-candidate-${index}`}
            >
              <summary className="flex cursor-pointer list-none flex-wrap items-center gap-x-3 gap-y-1 text-[10.5px]">
                <span className="sc-tabular font-medium">{item.symbol}</span>
                <span className="capitalize text-muted-foreground">
                  {item.marketType} · {item.side}
                </span>
                <span>{entryLabel(item.entryMethod)}</span>
                <span className="sc-tabular text-muted-foreground">
                  {item.candidateId.slice(0, 12)}
                </span>
                <span className="sc-tabular ml-auto text-muted-foreground">
                  {dateTime(item.signalAt)}
                </span>
                <ChevronDown
                  className="h-3.5 w-3.5 text-muted-foreground transition-transform group-open:rotate-180"
                  aria-hidden
                />
              </summary>
              <dl className="mt-2 grid gap-x-5 gap-y-1.5 border-t border-border/35 pt-2 text-[10px] sm:grid-cols-3">
                <div>
                  <dt className="eyebrow">Anchor</dt>
                  <dd className="sc-tabular mt-0.5">
                    {numeric(item.anchorPrice, 4)}
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow">Entry / stop</dt>
                  <dd className="sc-tabular mt-0.5">
                    {numeric(item.proposedEntryPrice, 4)} /{' '}
                    {numeric(item.stopPrice, 4)}
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow">Target · net R:R</dt>
                  <dd className="sc-tabular mt-0.5">
                    {numeric(item.targetPrice, 4)} ·{' '}
                    {numeric(item.plannedNetRewardRisk)} : 1
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow">Confirmation</dt>
                  <dd className="sc-tabular mt-0.5">
                    {dateTime(item.confirmationAt)}
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow">Planned loss</dt>
                  <dd className="sc-tabular mt-0.5">
                    {amount(item.plannedLossUsdt)}
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow">Committee</dt>
                  <dd className="mt-0.5 text-muted-foreground">
                    {item.committeeStatus ?? 'not_run'}
                  </dd>
                </div>
              </dl>
              {Object.keys(item.evidence).length > 0 && (
                <pre className="sc-tabular mt-2 max-h-32 overflow-auto whitespace-pre-wrap break-words border-t border-border/35 pt-2 text-[9px] leading-relaxed text-muted-foreground">
                  {JSON.stringify(item.evidence, null, 2)}
                </pre>
              )}
            </details>
          ))}
        </div>
      )}
    </section>
  );
}

function ResultPanel({
  result,
  onSelectRun,
  runs,
}: {
  result: StructuralBacktestResult;
  onSelectRun: (id: string) => void;
  runs: StructuralRunListItem[];
}) {
  const [segmentKey, setSegmentKey] = useState('');
  const [costBps, setCostBps] = useState('');
  const segment =
    result.segments.find((item) => methodKey(item) === segmentKey) ??
    result.segments[0];
  const cost =
    segment?.costResults.find(
      (item) => String(item.marketCostBps) === costBps,
    ) ?? segment?.costResults[0];
  const run = runs.find((item) => item.id === result.id);
  const fillTotal = result.segments.reduce(
    (sum, item) => sum + item.ordersFilled,
    0,
  );
  return (
    <div className="space-y-4" data-testid="section-structural-result">
      <section className="sc-hero sc-grid overflow-hidden rounded border border-[hsl(var(--sc-line)/.75)]">
        <div className="grid gap-4 p-4 sm:p-5 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className="sc-tabular text-[18px] font-semibold tracking-tight"
                data-testid="text-structural-result-symbol"
              >
                {result.symbol}
              </span>
              <span className="rounded border border-[hsl(var(--sc-lime)/.32)] bg-[hsl(var(--sc-lime)/.07)] px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-[hsl(var(--sc-lime))]">
                Deterministic research
              </span>
              <span className="rounded border border-warn/35 bg-warn/[0.06] px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-warn">
                {result.samplePeriod === 'future_validation'
                  ? 'Future validation'
                  : 'Development'}
              </span>
            </div>
            <p
              className="sc-tabular mt-1.5 text-[10px] text-muted-foreground"
              data-testid="text-structural-run-window"
            >
              {dateLabel(result.requestedStart)} —{' '}
              {dateLabel(result.requestedEnd)} · run {result.id}
            </p>
            {run && (
              <p className="mt-1 text-[10px] text-muted-foreground">
                Saved {dateTime(run.createdAt)} · {run.completedTrades}{' '}
                completed trades
              </p>
            )}
          </div>
          <label className="block min-w-0 lg:w-[360px]">
            <span className="eyebrow">Saved run</span>
            <select
              aria-label="Select saved structural run"
              className="focus-ring mt-1 block h-9 w-full rounded border border-border bg-background px-2.5 text-[11px]"
              data-testid="select-structural-saved-run"
              value={result.id}
              onChange={(event) => onSelectRun(event.target.value)}
            >
              {runs.map((item) => (
                <option value={item.id} key={item.id}>
                  <RunOption run={item} />
                </option>
              ))}
              {!runs.some((item) => item.id === result.id) && (
                <option value={result.id}>
                  {result.symbol} · current result
                </option>
              )}
            </select>
          </label>
        </div>
        <div className="grid grid-cols-2 border-t border-border/45 bg-background/20 sm:grid-cols-4">
          {[
            ['Segment fills', String(fillTotal), 'text-foreground'],
            ['Segments', String(result.segments.length), 'text-foreground'],
            [
              'Market cost cases',
              String(
                [
                  ...new Set(
                    result.segments.flatMap((item) =>
                      item.costResults.map(
                        (scenario) => scenario.marketCostBps,
                      ),
                    ),
                  ),
                ].length,
              ),
              'text-foreground',
            ],
            [
              'Committee review',
              result.committeeReviewStatus.replaceAll('_', ' '),
              'text-warn',
            ],
          ].map(([label, value, color]) => (
            <div
              key={label}
              className="border-r border-border/35 px-4 py-2.5 last:border-0"
            >
              <p className="eyebrow">{label}</p>
              <p
                className={cn(
                  'sc-tabular mt-1 text-[12px] font-medium capitalize',
                  color,
                )}
                data-testid={`text-result-${label.toLowerCase().replaceAll(' ', '-')}`}
              >
                {value}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section
        className="rounded border border-warn/35 bg-warn/[0.045] px-4 py-3"
        data-testid="notice-committee-not-run"
      >
        <div className="flex items-start gap-2.5">
          <AlertTriangle
            className="mt-0.5 h-4 w-4 shrink-0 text-warn"
            aria-hidden
          />
          <div>
            <p className="text-[11.5px] font-semibold">
              AI Committee review was not run
            </p>
            <p className="mt-1 text-[10.5px] leading-relaxed text-muted-foreground">
              {result.committeeNotice} Deterministic historical results are
              separate from any AI assessment; this view makes no AI calls.
            </p>
          </div>
        </div>
      </section>

      <section
        className="overflow-hidden rounded border border-border/70 bg-card/80"
        data-testid="section-structural-segment-summary"
      >
        <header className="border-b border-border/55 px-4 py-3">
          <div className="flex items-center gap-2">
            <BarChart3
              className="h-3.5 w-3.5 text-[hsl(var(--sc-lime))]"
              aria-hidden
            />
            <h2 className="text-[12px] font-semibold">Scenario ledger</h2>
          </div>
          <p className="mt-1 text-[10px] text-muted-foreground">
            Independent slices by market, side, entry method, hold and modeled
            cost. R/R rejections and untestable signals explain zero-fill rows;
            rows are not combined into a portfolio.
          </p>
        </header>
        <SummaryMatrix segments={result.segments} />
      </section>

      {segment && (
        <section
          className="overflow-hidden rounded border border-border/70 bg-card/80"
          data-testid="section-selected-structural-slice"
        >
          <header className="flex flex-wrap items-end justify-between gap-3 border-b border-border/55 px-4 py-3">
            <div className="min-w-0">
              <p className="eyebrow">Inspect underlying fills</p>
              <h2 className="mt-1 text-[12px] font-semibold">
                <SegmentName segment={segment} />
              </h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <label>
                <span className="sr-only">Segment slice</span>
                <select
                  className="focus-ring h-8 max-w-[300px] rounded border border-border bg-background px-2 text-[10.5px]"
                  data-testid="select-structural-segment"
                  value={methodKey(segment)}
                  onChange={(event) => {
                    setSegmentKey(event.target.value);
                    setCostBps('');
                  }}
                >
                  {result.segments.map((item) => (
                    <option key={methodKey(item)} value={methodKey(item)}>
                      {item.marketType} · {item.side} ·{' '}
                      {entryLabel(item.entryMethod)} · {item.maxHoldMinutes}m
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="sr-only">Modeled market cost</span>
                <select
                  className="focus-ring h-8 rounded border border-border bg-background px-2 text-[10.5px]"
                  data-testid="select-structural-cost-scenario"
                  value={cost?.marketCostBps ?? ''}
                  onChange={(event) => setCostBps(event.target.value)}
                  disabled={!segment.costResults.length}
                >
                  {segment.costResults.map((scenario) => (
                    <option
                      key={scenario.marketCostBps}
                      value={scenario.marketCostBps}
                    >
                      {scenario.marketCostBps} bps costs
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </header>
          {cost && (
            <>
              <div
                className="grid grid-cols-2 gap-y-4 border-b border-border/45 px-4 py-3 sm:grid-cols-4 xl:grid-cols-9"
                data-testid="grid-structural-metrics"
              >
                <Metric
                  label="Fills"
                  value={String(cost.metrics.tradeCount)}
                  testId="text-structural-fills"
                />
                <Metric
                  label="Unfilled limits"
                  value={String(segment.unfilledLimits)}
                  testId="text-structural-unfilled"
                />
                <Metric
                  label="Expectancy"
                  value={amount(cost.metrics.expectancyUsdt)}
                  color={tone(cost.metrics.expectancyUsdt)}
                  testId="text-structural-expectancy"
                />
                <Metric
                  label="Net P&L"
                  value={amount(cost.metrics.cumulativePnlUsdt)}
                  color={tone(cost.metrics.cumulativePnlUsdt)}
                  testId="text-structural-net-pnl"
                />
                <Metric
                  label="Win rate"
                  value={pct(cost.metrics.winRatePct)}
                  testId="text-structural-win-rate"
                />
                <Metric
                  label="Max drawdown"
                  value={amount(cost.metrics.maxDrawdownUsdt)}
                  color="text-loss"
                  testId="text-structural-drawdown"
                />
                <Metric
                  label="Fees"
                  value={amount(cost.metrics.totalFeesUsdt)}
                  testId="text-structural-fees"
                />
                <Metric
                  label="Funding"
                  value={amount(cost.metrics.totalFundingUsdt)}
                  color={tone(cost.metrics.totalFundingUsdt)}
                  testId="text-structural-funding"
                />
                <Metric
                  label={`${cost.marketCostBps} bps modeled`}
                  value={amount(
                    cost.metrics.totalSpreadCostUsdt === null
                      ? cost.metrics.totalSlippageCostUsdt
                      : (numberOf(cost.metrics.totalSpreadCostUsdt) ?? 0) +
                          (numberOf(cost.metrics.totalSlippageCostUsdt) ?? 0),
                  )}
                  testId="text-structural-market-cost"
                />
              </div>
              <TradeTable trades={cost.trades} />
            </>
          )}
          {!cost && (
            <p className="px-4 py-5 text-[10.5px] text-muted-foreground">
              No cost scenarios returned for this segment.
            </p>
          )}
          <UnfilledOrders orders={segment.orders} />
          <div className="border-t border-border/45 bg-background/20 px-4 py-2 text-[9.5px] text-muted-foreground">
            Rejected by 2:1 net reward/risk gate: {segment.rewardRiskRejected} ·
            orders placed: {segment.ordersPlaced} · overlapping signals skipped:{' '}
            {segment.overlappingSignalsSkipped} · untestable:{' '}
            {segment.untestableCandidates}
          </div>
        </section>
      )}
      <EvidenceList evidence={result.candidateEvidence} />
      <section
        className="grid gap-2 sm:grid-cols-2"
        data-testid="section-result-coverage"
      >
        <div className="rounded border border-border/65 bg-card/60 p-3">
          <p className="eyebrow">Historical candle coverage</p>
          {result.candleCoverage.length ? (
            <ul className="mt-2 space-y-1.5">
              {result.candleCoverage.map((item, index) => (
                <li
                  key={`${item.marketType}-${item.timeframe}-${index}`}
                  className="flex flex-wrap items-center justify-between gap-2 text-[10px]"
                  data-testid={`coverage-structural-${index}`}
                >
                  <span className="capitalize">
                    {item.symbol} · {item.marketType} · {item.timeframe}
                  </span>
                  <span className="sc-tabular text-muted-foreground">
                    {pct(item.coveragePct)} · {item.missingCandles} gaps
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-[10px] text-muted-foreground">
              No coverage details returned.
            </p>
          )}
        </div>
        <div
          className="rounded border border-border/65 bg-card/60 p-3"
          data-testid="text-structural-funding-coverage"
        >
          <p className="eyebrow">Futures funding records</p>
          <p className="mt-2 text-[10.5px] leading-relaxed">
            <span className="capitalize">
              {result.fundingCoverage.status.replaceAll('_', ' ')}
            </span>
            <span className="text-muted-foreground">
              {' '}
              · {result.fundingCoverage.records.toLocaleString()} records ·{' '}
              {result.fundingCoverage.note}
            </span>
          </p>
        </div>
      </section>
      <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-border/45 pt-3 text-[9.5px] text-muted-foreground">
        <span>
          Fingerprint ·{' '}
          <span className="sc-tabular break-all">{result.dataSha256}</span>
        </span>
        <span>
          Historical OKX data · no live scanner, proposals, approvals, permits
          or orders
        </span>
      </footer>
    </div>
  );
}

function Metric({
  label,
  value,
  color,
  testId,
}: {
  label: string;
  value: string;
  color?: string;
  testId: string;
}) {
  return (
    <div className="border-l border-border/55 pl-3 first:border-0 first:pl-0">
      <p className="eyebrow truncate">{label}</p>
      <p
        className={cn(
          'sc-tabular mt-1 truncate text-[12px] font-medium',
          color,
        )}
        data-testid={testId}
      >
        {value}
      </p>
    </div>
  );
}

export function StructuralChallenger() {
  const queryClient = useQueryClient();
  const overviewQuery = useGetStructuralChallengerOverview({
    query: { queryKey: getGetStructuralChallengerOverviewQueryKey() },
  });
  const listQuery = useListStructuralChallengerBacktests({
    query: { queryKey: getListStructuralChallengerBacktestsQueryKey() },
  });
  const createRun = useCreateStructuralChallengerBacktest();
  const [instrument, setInstrument] = useState<Instrument>('BTCUSDT');
  const [samplePeriod, setSamplePeriod] = useState<
    'development' | 'future_validation'
  >('development');
  const [selectedId, setSelectedId] = useState('');
  const runs = useMemo(
    () => listQuery.data ?? overviewQuery.data?.recentRuns ?? [],
    [listQuery.data, overviewQuery.data?.recentRuns],
  );
  const activeRunId = selectedId || runs[0]?.id || '';
  const detailQuery = useGetStructuralChallengerBacktest(activeRunId, {
    query: {
      queryKey: getGetStructuralChallengerBacktestQueryKey(activeRunId),
      enabled: Boolean(activeRunId),
    },
  });
  const result =
    detailQuery.data ??
    (createRun.data?.id === activeRunId ? createRun.data : undefined);
  const existingValidationRun = useMemo(
    () =>
      runs.some(
        (run) =>
          run.symbol === instrument && run.samplePeriod === 'future_validation',
      ),
    [runs, instrument],
  );
  const isNoRuns =
    !listQuery.isLoading &&
    !listQuery.isFetching &&
    !listQuery.isError &&
    runs.length === 0;
  const strategy = overviewQuery.data?.strategy;
  const development = overviewQuery.data?.developmentWindow;
  const validation = overviewQuery.data?.futureValidationWindow;
  const validationReady = validation?.status === 'ready';
  const validationUnavailable =
    samplePeriod === 'future_validation' &&
    (!validationReady || existingValidationRun);

  const startRun = () => {
    if (createRun.isPending || validationUnavailable) return;
    const input: StructuralBacktestInput = {
      symbol: instrument,
      samplePeriod,
    };
    createRun.reset();
    createRun.mutate(
      { data: input },
      {
        onSuccess: (saved) => {
          setSelectedId(saved.id);
          void queryClient.invalidateQueries({
            queryKey: getGetStructuralChallengerOverviewQueryKey(),
          });
          void queryClient.invalidateQueries({
            queryKey: getListStructuralChallengerBacktestsQueryKey(),
          });
        },
      },
    );
  };

  return (
    <div
      className="structural-challenger space-y-4"
      data-testid="page-structural-challenger"
    >
      <section
        className="sc-hero sc-grid overflow-hidden rounded border border-[hsl(var(--sc-line)/.75)]"
        data-testid="section-challenger-intro"
      >
        <div className="grid gap-5 p-4 sm:p-6 lg:grid-cols-[1fr_310px] lg:items-end">
          <div>
            <p className="eyebrow text-[hsl(var(--sc-lime)/.8)]">
              Isolated research instrument / 02
            </p>
            <h2 className="mt-2 max-w-3xl font-serif text-[30px] leading-[1.03] tracking-tight sm:text-[38px]">
              Structural pullback
              <span className="block text-[hsl(var(--sc-lime))]">
                challenger
              </span>
            </h2>
            <p className="mt-3 max-w-2xl text-[11.5px] leading-relaxed text-muted-foreground sm:text-[12px]">
              A deterministic counterfactual: enter at the next candle, or wait
              for the structural anchor. Historical OKX candles only. Not
              connected to execution.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-1">
            <div className="rounded border border-border/55 bg-background/30 px-3 py-2.5">
              <p className="eyebrow">Review state</p>
              <p
                className="mt-1 flex items-center gap-1.5 text-[10.5px] font-medium text-warn"
                data-testid="status-structural-committee"
              >
                <LockKeyhole className="h-3 w-3" aria-hidden /> Committee not
                run
              </p>
            </div>
            <div className="rounded border border-border/55 bg-background/30 px-3 py-2.5">
              <p className="eyebrow">Execution boundary</p>
              <p className="mt-1 flex items-center gap-1.5 text-[10.5px] font-medium text-[hsl(var(--sc-lime))]">
                <ShieldCheck className="h-3 w-3" aria-hidden /> Research only
              </p>
            </div>
          </div>
        </div>
        <div className="grid border-t border-border/45 bg-background/20 sm:grid-cols-3">
          {[
            ['Entry A', 'Next-candle market'],
            ['Entry B', 'Structural anchor limit'],
            ['Cost sweep', '0 / 5 / 10 bps'],
          ].map(([label, value], index) => (
            <div
              key={label}
              className={cn(
                'px-4 py-2.5',
                index > 0 &&
                  'border-t border-border/35 sm:border-l sm:border-t-0',
              )}
            >
              <p className="eyebrow">{label}</p>
              <p className="sc-tabular mt-1 text-[10.5px]">{value}</p>
            </div>
          ))}
        </div>
      </section>

      {overviewQuery.isError && (
        <ErrorNote
          error={overviewQuery.error}
          title="Challenger definition could not be loaded"
          onRetry={() => overviewQuery.refetch()}
        />
      )}
      {listQuery.isError && (
        <ErrorNote
          error={listQuery.error}
          title="Saved challenger runs could not be loaded"
          onRetry={() => listQuery.refetch()}
        />
      )}

      {overviewQuery.isLoading || listQuery.isLoading ? (
        <div
          className="space-y-3"
          aria-busy="true"
          data-testid="loading-structural-challenger"
        >
          <Skeleton className="h-24 bg-muted" />
          <Skeleton className="h-40 bg-muted" />
          <Skeleton className="h-72 bg-muted" />
        </div>
      ) : (
        <>
          {(development || validation) && (
            <section
              className="grid gap-2 md:grid-cols-2"
              data-testid="section-structural-windows"
            >
              {development && (
                <WindowCard
                  window={development}
                  label="Fixed development sample"
                  testId="window-development"
                />
              )}
              {validation && (
                <WindowCard
                  window={validation}
                  label="Future validation"
                  testId="window-future-validation"
                />
              )}
            </section>
          )}

          {strategy && <StrategyDefinition strategy={strategy} />}

          <section
            className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_330px]"
            data-testid="section-structural-run-controls"
          >
            <div className="rounded border border-border/70 bg-card/80 p-4">
              <div className="flex items-center gap-2">
                <Activity
                  className="h-3.5 w-3.5 text-[hsl(var(--sc-lime))]"
                  aria-hidden
                />
                <h2 className="text-[12px] font-semibold">
                  {samplePeriod === 'development'
                    ? 'Development replay'
                    : 'Future validation replay'}
                </h2>
              </div>
              <p className="mt-1.5 text-[10.5px] leading-relaxed text-muted-foreground">
                Both sample windows have fixed dates. Development can be rerun;
                the reserved holdout is available once per instrument after it
                closes.
              </p>
              <div className="mt-3 flex flex-wrap items-end gap-2.5">
                <label className="min-w-[190px] flex-1 sm:max-w-[260px]">
                  <span className="eyebrow">Instrument</span>
                  <select
                    className="focus-ring mt-1 block h-9 w-full rounded border border-border bg-background px-2.5 text-[11px]"
                    data-testid="select-structural-instrument"
                    value={instrument}
                    onChange={(event) =>
                      setInstrument(event.target.value as Instrument)
                    }
                  >
                    {INSTRUMENTS.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="min-w-[150px] flex-1 sm:max-w-[190px]">
                  <p className="eyebrow">Sample period</p>
                  <select
                    className="focus-ring mt-1 block h-9 w-full rounded border border-border bg-background px-2.5 text-[10.5px]"
                    data-testid="select-structural-sample-period"
                    value={samplePeriod}
                    onChange={(event) =>
                      setSamplePeriod(
                        event.target.value as
                          'development' | 'future_validation',
                      )
                    }
                  >
                    <option value="development">
                      Development · fixed dates
                    </option>
                    <option
                      value="future_validation"
                      disabled={!validationReady || existingValidationRun}
                    >
                      Future validation ·{' '}
                      {!validationReady
                        ? 'locked'
                        : existingValidationRun
                          ? 'already used'
                          : 'one run'}
                    </option>
                  </select>
                </div>
                <button
                  type="button"
                  className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded border border-[hsl(var(--sc-lime)/.4)] bg-[hsl(var(--sc-lime)/.12)] px-3.5 text-[10.5px] font-semibold text-[hsl(var(--sc-lime))] transition-colors hover:bg-[hsl(var(--sc-lime)/.18)] disabled:cursor-not-allowed disabled:opacity-45"
                  data-testid="button-run-structural-challenger"
                  onClick={startRun}
                  disabled={createRun.isPending || validationUnavailable}
                >
                  {createRun.isPending ? (
                    <>
                      <Clock3
                        className="h-3.5 w-3.5 animate-pulse"
                        aria-hidden
                      />{' '}
                      Running replay
                    </>
                  ) : samplePeriod === 'future_validation' &&
                    existingValidationRun ? (
                    <>
                      <LockKeyhole className="h-3.5 w-3.5" aria-hidden /> Final
                      run saved
                    </>
                  ) : (
                    <>
                      <BarChart3 className="h-3.5 w-3.5" aria-hidden /> Run
                      deterministic replay
                    </>
                  )}
                </button>
              </div>
              {samplePeriod === 'future_validation' &&
                existingValidationRun && (
                  <p
                    className="mt-2 text-[10px] text-warn"
                    data-testid="notice-instrument-locked"
                  >
                    The reserved validation sample has already been used for{' '}
                    {instrument}.
                  </p>
                )}
              {createRun.isError && (
                <div className="mt-3">
                  <ErrorNote
                    error={createRun.error}
                    title={`${samplePeriod === 'development' ? 'Development' : 'Validation'} replay failed`}
                    onRetry={startRun}
                  />
                </div>
              )}
              {createRun.isPending && (
                <div
                  className="mt-3 grid gap-2 sm:grid-cols-3"
                  aria-busy="true"
                  data-testid="loading-structural-run"
                >
                  <Skeleton className="h-8 bg-muted" />
                  <Skeleton className="h-8 bg-muted" />
                  <Skeleton className="h-8 bg-muted" />
                </div>
              )}
            </div>
            <div
              className="rounded border border-warn/30 bg-warn/[0.035] p-4"
              data-testid="section-future-validation-lock"
            >
              <p className="eyebrow text-warn">
                Future validation · {validationReady ? 'available' : 'locked'}
              </p>
              <p className="mt-1.5 text-[11px] font-medium">
                {validationReady
                  ? 'The reserved holdout is ready for one final run per instrument.'
                  : 'No future sample can be run yet.'}
              </p>
              <p className="mt-1 text-[10px] leading-relaxed text-muted-foreground">
                Validation remains pending until its window exists. No data is
                generated or substituted while the window is locked.
              </p>
            </div>
          </section>

          {isNoRuns ? (
            <section
              className="sc-grid rounded border border-dashed border-border/80 bg-card/45 px-5 py-10 text-center"
              data-testid="empty-structural-runs"
            >
              <div className="mx-auto grid h-10 w-10 place-items-center rounded border border-[hsl(var(--sc-lime)/.35)] bg-[hsl(var(--sc-lime)/.08)]">
                <BarChart3
                  className="h-4 w-4 text-[hsl(var(--sc-lime))]"
                  aria-hidden
                />
              </div>
              <p className="mt-3 text-[12px] font-semibold">
                No saved challenger runs
              </p>
              <p className="mx-auto mt-1 max-w-md text-[10.5px] leading-relaxed text-muted-foreground">
                Start one fixed development replay for an instrument. Results
                will appear here with their market, side, entry, hold and cost
                slices.
              </p>
            </section>
          ) : null}

          {activeRunId &&
            (detailQuery.isLoading || (detailQuery.isFetching && !result)) && (
              <div
                className="space-y-3"
                aria-busy="true"
                data-testid="loading-structural-detail"
              >
                <Skeleton className="h-32 bg-muted" />
                <Skeleton className="h-64 bg-muted" />
              </div>
            )}
          {detailQuery.isError && (
            <ErrorNote
              error={detailQuery.error}
              title="Saved challenger result could not be opened"
              onRetry={() => detailQuery.refetch()}
            />
          )}
          {result && (
            <ResultPanel
              key={result.id}
              result={result}
              runs={runs}
              onSelectRun={setSelectedId}
            />
          )}
          {!activeRunId && !isNoRuns && !listQuery.isError && (
            <div
              className="rounded border border-border/70 bg-card/60 px-4 py-8 text-center text-[10.5px] text-muted-foreground"
              data-testid="empty-structural-result"
            >
              No active run is selected.
            </div>
          )}
        </>
      )}
    </div>
  );
}
