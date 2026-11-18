import { useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  FlaskConical,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react';
import {
  getGetStrategyBacktestQueryKey,
  getGetStrategyLabOverviewQueryKey,
  getListStrategyBacktestReviewsQueryKey,
  getListStrategyBacktestsQueryKey,
  useListStrategyBacktestReviews,
  useCreateStrategyBacktest,
  useCreateStrategyBacktestReview,
  useGetStrategyBacktest,
  useGetStrategyLabOverview,
  useListStrategyBacktests,
  type BacktestInput,
  type BacktestListItem,
  type BacktestEntryOrder,
  type BacktestResult,
  type BacktestSegment,
  type BacktestTrade,
  type HistoricalReviewResponse,
  type StrategyConfiguration,
} from '@workspace/api-client-react';
import { cn } from '@/lib/utils';
import { ErrorNote, KV, NotAvailable, PaperLabel } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';
import {
  BacktestSegmentSummary,
  segmentLabel,
} from '@/components/backtest-segment-summary';
import { StructuralChallenger } from '@/pages/structural-challenger';

const CHART_COLORS = {
  blue: '#51c8b5',
  purple: '#d3a967',
  green: '#70bd8a',
  red: '#dd8178',
  pink: '#cb8ca8',
};
const PAIR_OPTIONS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'] as const;
type Pair = (typeof PAIR_OPTIONS)[number];

function numberOf(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null;
  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

function numeric(value: number | string | null | undefined, digits = 2) {
  const n = numberOf(value);
  return n === null
    ? '—'
    : n.toLocaleString('en-US', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
}

function money(value: number | string | null | undefined, digits = 2) {
  const n = numberOf(value);
  if (n === null) return '—';
  return `${n < 0 ? '−' : ''}${Math.abs(n).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })} USDT`;
}

function percent(value: number | string | null | undefined, digits = 2) {
  const n = numberOf(value);
  if (n === null) return '—';
  return `${n > 0 ? '+' : ''}${n.toFixed(digits)}%`;
}

function dateTime(value: string | null | undefined) {
  if (!value) return 'Not available';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
    timeZoneName: 'short',
  });
}

function dateOnly(value: string | null | undefined) {
  if (!value) return 'Not available';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

function signTone(value: number | string | null | undefined) {
  const n = numberOf(value);
  return n === null
    ? 'text-muted-foreground'
    : n > 0
      ? 'text-profit'
      : n < 0
        ? 'text-loss'
        : 'text-foreground';
}

function SideLabel({ side }: { side: string }) {
  const bullish = side === 'long';
  const Icon = bullish ? ArrowUpRight : ArrowDownRight;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 capitalize',
        bullish ? 'text-profit' : 'text-loss',
      )}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {side}
    </span>
  );
}

function RunRow({
  run,
  active,
  onSelect,
}: {
  run: BacktestListItem;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      data-testid={`button-select-run-${run.id}`}
      onClick={onSelect}
      aria-current={active ? 'true' : undefined}
      className={cn(
        'focus-ring group grid w-full grid-cols-[1fr_auto] gap-x-3 border-b border-border/50 px-3 py-3 text-left transition-colors last:border-0 hover:bg-background/60',
        active && 'bg-teal/[0.07]',
      )}
    >
      <span className="flex min-w-0 items-center gap-2">
        <span
          className={cn(
            'h-1.5 w-1.5 shrink-0 rounded-full',
            active ? 'bg-teal' : 'bg-muted-foreground/40',
          )}
        />
        <span className="num truncate text-[12.5px] font-medium">
          {run.symbol}
        </span>
        <span className="rounded-sm border border-border px-1 py-0.5 font-mono text-[9px] text-muted-foreground">
          {run.requestedDays}d
        </span>
      </span>
      <span className="num text-[10px] text-muted-foreground">
        {dateOnly(run.createdAt)}
      </span>
      <span className="col-span-2 mt-1.5 pl-3.5 text-[10.5px] text-muted-foreground">
        {run.tradeCount} closed trades · all segments{' '}
        <span className="px-1 text-border">/</span> {run.strategyVersion}
      </span>
    </button>
  );
}

function ConfigItem({
  label,
  value,
  testId,
}: {
  label: string;
  value: string;
  testId?: string;
}) {
  return (
    <div className="min-w-0 border-b border-border/50 py-2 last:border-0">
      <dt className="eyebrow">{label}</dt>
      <dd
        className="mt-1 break-words text-[12px] leading-relaxed text-foreground/90"
        data-testid={testId}
      >
        {value || <NotAvailable />}
      </dd>
    </div>
  );
}

function Configuration({ strategy }: { strategy: StrategyConfiguration }) {
  return (
    <section
      className="panel overflow-hidden"
      data-testid="section-approved-strategy"
    >
      <header className="flex items-center justify-between border-b border-border/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-teal" aria-hidden />
          <h2 className="text-[13px] font-semibold">Strategy definition</h2>
        </div>
        <span
          className="num rounded border border-teal/30 bg-teal/[0.07] px-1.5 py-1 text-[10px] text-teal"
          data-testid="text-strategy-version"
        >
          {strategy.strategyVersion}
        </span>
      </header>
      {strategy.strategyVersion === 'btc-regime-pullback-v1' && (
        <p
          className="border-b border-warn/30 bg-warn/[0.06] px-4 py-3 text-[12px] leading-relaxed text-warn"
          data-testid="notice-scanner-rule-conflict"
        >
          Scanner parity mode: the current 1h trend and pullback gates conflict.
          No entry can satisfy both. Zero trades cannot establish a win/loss
          rate or validate the stops and targets. These rules are preserved
          exactly as requested.
        </p>
      )}
      {strategy.entryRules && strategy.entryRules.length > 0 && (
        <ul
          className="space-y-1 border-b border-border px-4 py-3 text-xs text-muted-foreground"
          data-testid="approved-entry-rules"
        >
          {strategy.entryRules.map((rule) => (
            <li key={rule}>{rule}</li>
          ))}
          <li>
            Research only. Existing EMA-derived exits remain inherited and
            unvalidated.
          </li>
        </ul>
      )}
      <div className="grid gap-x-6 px-4 py-2 sm:grid-cols-2 xl:grid-cols-4">
        <ConfigItem
          label="Trend / regime"
          value={`${strategy.trendTimeframe} timeframe · BTC regime`}
          testId="text-trend-regime"
        />
        <ConfigItem
          label="Setup confirmation"
          value={`${strategy.confirmationTimeframe} closed candles`}
          testId="text-confirmation-timeframe"
        />
        <ConfigItem
          label="Future AI threshold"
          value={
            strategy.scoreGateEnabled === false
              ? `${strategy.scoreThreshold}/100 selected · NOT applied; revised weights pending`
              : `${strategy.scoreThreshold} / 100 (legacy rule gate)`
          }
          testId="text-score-threshold"
        />
        <ConfigItem
          label="Spot coverage"
          value={`Long only · ${strategy.spotSides.join(', ') || 'none'}`}
          testId="text-spot-coverage"
        />
        <ConfigItem
          label="Futures coverage"
          value={strategy.futuresSides.join(' / ') || 'Not available'}
          testId="text-futures-coverage"
        />
        <ConfigItem
          label="Take profit"
          value={strategy.takeProfitLevel}
          testId="text-take-profit-rule"
        />
        <ConfigItem
          label="Stop rule"
          value={strategy.stopRule}
          testId="text-stop-rule"
        />
        <ConfigItem
          label="Entry order"
          value={`${strategy.entryLimitRule} · expires after ${strategy.entryExpiryBars} candles`}
          testId="text-entry-limit-rule"
        />
        <ConfigItem
          label="Maximum hold"
          value={`${strategy.maxHoldMinutes} minutes · ${Math.floor(strategy.maxHoldMinutes / 15)} × 15m bars`}
          testId="text-max-hold"
        />
        <ConfigItem
          label="Sample split"
          value={strategy.sampleSplit}
          testId="text-sample-split"
        />
        <ConfigItem
          label="Sizing"
          value={`${numeric(strategy.notionalUsdt, 0)} USDT notional · ${numeric(strategy.leverage, 0)}×`}
          testId="text-sizing-assumptions"
        />
        <ConfigItem
          label="Lookahead control"
          value={strategy.noLookaheadRule}
          testId="text-no-lookahead-rule"
        />
        <ConfigItem
          label="Execution assumptions"
          value={strategy.executionAssumptions.join(' · ')}
          testId="text-execution-assumptions"
        />
      </div>
      <div className="grid gap-3 border-t border-border/50 bg-background/25 px-4 py-3 sm:grid-cols-2">
        <p
          className="text-[11px] leading-relaxed text-muted-foreground"
          data-testid="text-cost-coverage-note"
        >
          Entry and target use maker-fee defaults; stop and time exits use
          taker-fee defaults. They are not your account-specific OKX tier.
          Historical futures funding is included where returned.
        </p>
        <p
          className="text-[11px] leading-relaxed text-muted-foreground"
          data-testid="text-strategy-interpretation"
        >
          This is a fixed research definition. Only the instrument and lookback
          window are adjustable. No separate spread or slippage charge is used.
        </p>
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
  note,
  tone,
  testId,
}: {
  label: string;
  value: string;
  note?: string;
  tone?: string;
  testId: string;
}) {
  return (
    <div className="min-w-0 border-l border-border/60 pl-3 first:border-0 first:pl-0 sm:pl-4">
      <p className="eyebrow">{label}</p>
      <p
        className={cn(
          'num mt-1 text-[17px] font-medium tracking-tight sm:text-[19px]',
          tone,
        )}
        data-testid={testId}
      >
        {value}
      </p>
      {note && (
        <p className="mt-1 truncate text-[10.5px] text-muted-foreground">
          {note}
        </p>
      )}
    </div>
  );
}

function SegmentSwitch({
  segments,
  value,
  onChange,
}: {
  segments: BacktestSegment[];
  value: number;
  onChange: (index: number) => void;
}) {
  return (
    <div
      className="flex gap-1 overflow-x-auto p-1"
      role="tablist"
      aria-label="Backtest segments"
      data-testid="list-segment-tabs"
    >
      {segments.map((segment, index) => {
        const selected = value === index;
        return (
          <button
            type="button"
            role="tab"
            aria-selected={selected}
            key={`${segment.marketType}-${segment.side}-${segment.period}`}
            data-testid={`tab-segment-${segment.marketType}-${segment.side}-${segment.period}`}
            onClick={() => onChange(index)}
            className={cn(
              'focus-ring shrink-0 rounded px-2.5 py-1.5 text-[10.5px] transition-colors',
              selected
                ? 'bg-card text-teal shadow-sm'
                : 'text-muted-foreground hover:bg-card/60 hover:text-foreground',
            )}
          >
            <span className="capitalize">
              {segment.marketType} · {segment.side}
            </span>
            <span className="ml-1.5 border-l border-border pl-1.5 capitalize">
              {segment.period.replaceAll('_', ' ')}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function EquityChart({ segment }: { segment: BacktestSegment }) {
  const points = useMemo(
    () =>
      segment.equityCurve
        .map((point) => ({
          ...point,
          equity: numberOf(point.equityUsdt),
          pnl: numberOf(point.cumulativePnlUsdt),
        }))
        .filter((point) => point.equity !== null),
    [segment.equityCurve],
  );
  const tick = '#9aa8ad';
  if (!points.length) {
    return (
      <div
        className="grid h-[220px] place-items-center rounded border border-dashed border-border text-center"
        data-testid="empty-equity-curve"
      >
        <div>
          <BarChart3
            className="mx-auto h-5 w-5 text-muted-foreground/60"
            aria-hidden
          />
          <p className="mt-2 text-xs text-muted-foreground">
            No equity points in this segment
          </p>
        </div>
      </div>
    );
  }
  return (
    <div className="h-[230px] w-full" data-testid="chart-equity-curve">
      <ResponsiveContainer width="100%" height="100%" debounce={0}>
        <AreaChart
          data={points}
          margin={{ top: 8, right: 5, left: -18, bottom: 0 }}
        >
          <defs>
            <linearGradient id="equityTint" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor={CHART_COLORS.blue}
                stopOpacity={0.24}
              />
              <stop
                offset="100%"
                stopColor={CHART_COLORS.blue}
                stopOpacity={0.01}
              />
            </linearGradient>
          </defs>
          <CartesianGrid
            stroke="rgba(160,180,185,0.12)"
            strokeDasharray="3 5"
            vertical={false}
          />
          <XAxis
            dataKey="at"
            tickFormatter={(value: string) => {
              const d = new Date(value);
              return Number.isNaN(d.getTime())
                ? value
                : d.toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: 'short',
                    timeZone: 'UTC',
                  });
            }}
            tick={{ fill: tick, fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            minTickGap={28}
          />
          <YAxis
            tickFormatter={(value: number) => `${value.toFixed(0)}`}
            tick={{ fill: tick, fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            domain={['auto', 'auto']}
          />
          <Tooltip
            isAnimationActive={false}
            cursor={{ stroke: 'rgba(160,180,185,0.4)', strokeDasharray: '3 3' }}
            contentStyle={{
              background: '#172327',
              border: '1px solid #35464a',
              borderRadius: 4,
              color: '#e2e9e9',
              fontSize: 11,
            }}
            labelFormatter={(label) => dateTime(String(label))}
            formatter={(value: number | string) => [
              `${numeric(value)} USDT`,
              'Equity',
            ]}
          />
          <Area
            type="linear"
            dataKey="equity"
            name="Equity"
            stroke={CHART_COLORS.blue}
            strokeWidth={2}
            fill="url(#equityTint)"
            dot={false}
            activeDot={{
              r: 4,
              fill: CHART_COLORS.blue,
              stroke: '#172327',
              strokeWidth: 2,
            }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function TradeTable({ trades }: { trades: BacktestTrade[] }) {
  if (!trades.length) {
    return (
      <div className="px-4 py-8 text-center" data-testid="empty-trades">
        <p className="text-[13px] font-medium">
          No closed trades in this segment
        </p>
        <p className="mt-1 text-[11.5px] text-muted-foreground">
          Unclosed positions are excluded from the reported performance.
        </p>
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table
        className="w-full min-w-[1120px] text-left text-[11.5px]"
        data-testid="table-underlying-trades"
      >
        <thead>
          <tr className="border-b border-border/60">
            {[
              'Signal / fill time',
              'Side',
              'Limit order',
              'Filled entry',
              'Stop / target',
              'Actual exit',
              'Exit reason',
              'Gross P&L',
              'Fee detail',
              'Funding',
              'Other costs',
              'Net P&L',
            ].map((label) => (
              <th
                className="eyebrow whitespace-nowrap px-2.5 py-2 font-normal first:pl-4 last:pr-4"
                key={label}
              >
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, index) => (
            <tr
              key={`${trade.enteredAt}-${index}`}
              data-testid={`row-backtest-trade-${index}`}
              className="border-b border-border/40 hover:bg-background/30"
            >
              <td className="num whitespace-nowrap px-2.5 py-2 first:pl-4">
                <span title={dateTime(trade.signalAt)}>
                  {dateTime(trade.enteredAt)}
                </span>
                <span className="block text-[10px] text-muted-foreground">
                  {trade.holdingMinutes} min
                </span>
              </td>
              <td className="px-2.5 py-2">
                <SideLabel side={trade.side} />
              </td>
              <td className="num whitespace-nowrap px-2.5 py-2">
                {numeric(trade.entryOrderPrice ?? trade.entryPrice, 4)}
                <span className="block text-[10px] text-muted-foreground">
                  limit · {trade.entryFeeType}
                </span>
              </td>
              <td className="num whitespace-nowrap px-2.5 py-2">
                {numeric(trade.entryPrice, 4)}
                <span className="block text-[10px] text-muted-foreground">
                  {trade.entryOrderType === 'legacy_next_open'
                    ? 'legacy open'
                    : 'simulated fill'}
                </span>
              </td>
              <td className="num whitespace-nowrap px-2.5 py-2">
                <span className="text-loss">{numeric(trade.stopPrice, 4)}</span>
                <span className="text-muted-foreground"> / </span>
                <span className="text-profit">
                  {numeric(trade.targetPrice, 4)}
                </span>
              </td>
              <td className="num whitespace-nowrap px-2.5 py-2">
                {numeric(trade.exitPrice, 4)}
                <span className="block text-[10px] text-muted-foreground">
                  {trade.exitFeeType} · {dateTime(trade.exitedAt)}
                </span>
              </td>
              <td className="px-2.5 py-2 capitalize">
                {trade.exitReason.replaceAll('_', ' ')}
              </td>
              <td
                className={cn(
                  'num whitespace-nowrap px-2.5 py-2',
                  signTone(trade.grossPnlUsdt),
                )}
              >
                {money(trade.grossPnlUsdt)}
              </td>
              <td className="num whitespace-nowrap px-2.5 py-2 text-muted-foreground">
                {trade.entryOrderType === 'legacy_next_open'
                  ? money(trade.feeUsdt)
                  : `${money(trade.makerFeeUsdt)} maker · ${money(trade.takerFeeUsdt)} taker`}
              </td>
              <td
                className={cn(
                  'num whitespace-nowrap px-2.5 py-2',
                  signTone(trade.fundingUsdt),
                )}
              >
                {money(trade.fundingUsdt)}
              </td>
              <td className="num whitespace-nowrap px-2.5 py-2 text-muted-foreground">
                {money(
                  numberOf(trade.spreadCostUsdt) === null ||
                    numberOf(trade.slippageCostUsdt) === null
                    ? null
                    : Number(trade.spreadCostUsdt) +
                        Number(trade.slippageCostUsdt),
                )}
              </td>
              <td
                className={cn(
                  'num whitespace-nowrap px-2.5 py-2 pr-4 font-medium',
                  signTone(trade.netPnlUsdt),
                )}
              >
                {money(trade.netPnlUsdt)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EntryOrderTable({ orders }: { orders: BacktestEntryOrder[] }) {
  if (!orders.length) return null;
  const notFilled = orders.filter((order) => order.status !== 'filled');
  if (!notFilled.length) return null;
  return (
    <div
      className="border-t border-border/50"
      data-testid="section-entry-orders"
    >
      <header className="flex items-center justify-between px-4 py-2.5">
        <div>
          <h3 className="text-[11.5px] font-medium">
            Unfilled or cancelled limit orders
          </h3>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            These are not counted as trades or included in win rate.
          </p>
        </div>
        <span className="num text-[10px] text-muted-foreground">
          {notFilled.length} orders
        </span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px] text-left text-[10.5px]">
          <thead>
            <tr className="border-y border-border/40">
              {[
                'Signal time',
                'Side',
                'Limit price',
                'Expires',
                'Status',
                'Reason',
              ].map((label) => (
                <th
                  className="eyebrow whitespace-nowrap px-3 py-2 first:pl-4"
                  key={label}
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {notFilled.map((order, index) => (
              <tr
                className="border-b border-border/30"
                data-testid={`row-entry-order-${index}`}
                key={`${order.signalAt}-${index}`}
              >
                <td className="num whitespace-nowrap px-3 py-2 first:pl-4">
                  {dateTime(order.signalAt)}
                </td>
                <td className="px-3 py-2">
                  <SideLabel side={order.side} />
                </td>
                <td className="num px-3 py-2">
                  {numeric(order.limitPrice, 4)}
                </td>
                <td className="num whitespace-nowrap px-3 py-2">
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
    </div>
  );
}

function HistoricalReviewCard({
  review,
}: {
  review: HistoricalReviewResponse;
}) {
  return (
    <article
      className="rounded border border-teal/30 bg-teal/[0.04] p-3"
      data-testid="card-historical-ai-review"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[11px] font-medium">Advisory review</p>
        <p className="num text-[9.5px] text-muted-foreground">
          {review.model} · {review.inputTokens + review.outputTokens} tokens ·{' '}
          {money(review.costUsd, 4)}
        </p>
      </div>
      <p className="mt-2 text-[11.5px] leading-relaxed">
        {review.answer.summary}
      </p>
      {[
        ['Observations', review.answer.observations],
        ['Risks', review.answer.risks],
        ['Limitations', review.answer.limitations],
      ].map(([title, items]) =>
        Array.isArray(items) && items.length ? (
          <div className="mt-2" key={String(title)}>
            <p className="eyebrow">{String(title)}</p>
            <ul className="mt-1 list-inside list-disc space-y-1 text-[10.5px] text-muted-foreground">
              {items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null,
      )}
      <p className="mt-2 break-words font-mono text-[9px] text-muted-foreground">
        Evidence: {review.answer.evidenceIds.join(', ') || 'none cited'} · run
        fingerprint {review.dataSha256}
      </p>
      <p className="mt-2 border-t border-border/50 pt-2 text-[9.5px] text-muted-foreground">
        Historical commentary only. Not a trade recommendation, approval, or
        execution instruction.
      </p>
    </article>
  );
}

function Coverage({ result }: { result: BacktestResult }) {
  const incomplete = result.candleCoverage.some(
    (item) => numberOf(item.coveragePct) !== 100 || item.missingCandles > 0,
  );
  const fundingPartial =
    result.fundingCoverage.status === 'partial' ||
    result.fundingCoverage.status === 'unavailable';
  return (
    <section
      className="panel overflow-hidden"
      data-testid="section-data-coverage"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
        <h2 className="text-[13px] font-semibold">Historical data coverage</h2>
        <span
          className={cn(
            'rounded border px-2 py-1 font-mono text-[9.5px] uppercase tracking-wider',
            incomplete || fundingPartial
              ? 'border-warn/40 bg-warn/[0.07] text-warn'
              : 'border-profit/30 bg-profit/[0.06] text-profit',
          )}
          data-testid="status-coverage"
        >
          {incomplete || fundingPartial
            ? 'Partial coverage'
            : 'Coverage recorded'}
        </span>
      </header>
      {result.candleCoverage.length ? (
        <div className="divide-y divide-border/40">
          {result.candleCoverage.map((coverage, index) => {
            const pct = numberOf(coverage.coveragePct);
            return (
              <div
                className="grid gap-2 px-4 py-2.5 sm:grid-cols-[1fr_auto] sm:items-center"
                key={`${coverage.symbol}-${coverage.marketType}-${index}`}
                data-testid={`coverage-candle-${coverage.marketType}-${index}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="num text-[11px] font-medium">
                    {coverage.symbol}
                  </span>
                  <span className="font-mono text-[9px] uppercase text-muted-foreground">
                    {coverage.marketType}
                  </span>
                  <span className="text-[10.5px] text-muted-foreground">
                    {coverage.actualClosedCandles.toLocaleString()} /{' '}
                    {coverage.expectedCandles.toLocaleString()} closed candles
                  </span>
                </div>
                <div className="flex items-center gap-2 sm:justify-end">
                  <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
                    <div
                      className={cn(
                        'h-full rounded-full',
                        pct === 100 ? 'bg-profit' : 'bg-warn',
                      )}
                      style={{
                        width: `${Math.max(0, Math.min(pct ?? 0, 100))}%`,
                      }}
                    />
                  </div>
                  <span
                    className="num w-12 text-right text-[10.5px]"
                    data-testid={`text-coverage-pct-${index}`}
                  >
                    {pct === null ? '—' : `${pct.toFixed(1)}%`}
                  </span>
                </div>
                {coverage.gapRanges.length > 0 && (
                  <p
                    className="sm:col-span-2 text-[10px] leading-relaxed text-warn"
                    data-testid={`text-coverage-gaps-${index}`}
                  >
                    Missing intervals: {coverage.gapRanges.join(' · ')}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <p
          className="px-4 py-3 text-xs text-muted-foreground"
          data-testid="empty-candle-coverage"
        >
          Candle coverage was not returned for this run.
        </p>
      )}
      <div className="grid gap-2 border-t border-border/50 bg-background/25 px-4 py-3 sm:grid-cols-[auto_1fr] sm:items-start">
        <span className="eyebrow mt-0.5">Funding records</span>
        <div
          className="text-[11px] leading-relaxed"
          data-testid="text-funding-coverage"
        >
          <span
            className={cn(
              'font-medium capitalize',
              fundingPartial ? 'text-warn' : 'text-foreground',
            )}
          >
            {result.fundingCoverage.status.replaceAll('_', ' ')}
          </span>
          <span className="text-muted-foreground">
            {' '}
            · {result.fundingCoverage.records.toLocaleString()} records ·{' '}
            {result.fundingCoverage.note || 'No coverage note supplied.'}
          </span>
        </div>
      </div>
    </section>
  );
}

function ResultView({
  result,
  onChooseAnother,
  latestRunId,
  reviewEnabled,
  reviewNotice,
}: {
  result: BacktestResult;
  onChooseAnother: (id: string) => void;
  latestRunId: string;
  reviewEnabled: boolean;
  reviewNotice: string;
}) {
  const queryClient = useQueryClient();
  const initialIndex = Math.max(
    0,
    result.segments.findIndex((item) => item.period === 'out_of_sample'),
  );
  const [segmentIndex, setSegmentIndex] = useState(initialIndex);
  const [reviewQuestion, setReviewQuestion] = useState('');
  const reviewRun = useCreateStrategyBacktestReview();
  const reviewsQuery = useListStrategyBacktestReviews(result.id, {
    query: {
      queryKey: getListStrategyBacktestReviewsQueryKey(result.id),
      enabled: Boolean(result.id),
    },
  });
  const segment = result.segments[segmentIndex];
  const metrics = segment?.metrics;
  const totalTrades = result.segments.reduce(
    (sum, item) => sum + item.metrics.tradeCount,
    0,
  );
  const orderAwareRun = result.engineVersion === 'okx-limit-order-candle-v3';
  const savedReviews = [...(reviewsQuery.data ?? [])];
  if (
    reviewRun.data &&
    !savedReviews.some((review) => review.id === reviewRun.data?.id)
  ) {
    savedReviews.unshift(reviewRun.data);
  }
  const statusIncomplete =
    result.candleCoverage.some((c) => c.missingCandles > 0) ||
    result.fundingCoverage.status === 'partial' ||
    result.fundingCoverage.status === 'unavailable';
  return (
    <div className="space-y-4" data-testid="section-backtest-result">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className="num text-[18px] font-semibold tracking-tight"
              data-testid="text-result-symbol"
            >
              {result.symbol}
            </span>
            <span className="rounded border border-teal/30 bg-teal/[0.06] px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-teal">
              Hypothetical historical analysis
            </span>
            {statusIncomplete && (
              <span
                className="rounded border border-warn/40 bg-warn/[0.07] px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-warn"
                data-testid="status-partial-history"
              >
                Partial history
              </span>
            )}
          </div>
          <p
            className="num mt-1 text-[10.5px] text-muted-foreground"
            data-testid="text-result-period"
          >
            Requested {dateOnly(result.requestedStart)} —{' '}
            {dateOnly(result.requestedEnd)} · {result.requestedDays} days · run{' '}
            {result.id}
          </p>
        </div>
        <button
          type="button"
          data-testid="button-view-latest-run"
          onClick={() => onChooseAnother(latestRunId || result.id)}
          className="focus-ring inline-flex h-8 items-center gap-1.5 rounded border border-border px-2.5 text-[11px] text-muted-foreground hover:text-foreground"
        >
          Latest saved run <ChevronRight className="h-3.5 w-3.5" aria-hidden />
        </button>
      </div>

      {segment && (
        <section
          className="rounded border border-teal/30 bg-teal/5 px-4 py-3"
          aria-live="polite"
          data-testid="section-selected-segment"
        >
          <p className="eyebrow">Selected segment — not the whole run</p>
          <h2
            className="mt-1 text-sm font-semibold"
            data-testid="text-selected-segment"
          >
            {segmentLabel(segment)}
          </h2>
          <p className="num mt-1 text-[11px] text-muted-foreground">
            {dateTime(segment.periodStart)} — {dateTime(segment.periodEnd)}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            The metric cards, chart and underlying trades show this segment
            only.
          </p>
          {metrics?.tradeCount === 0 && (
            <p
              className="mt-2 text-xs"
              data-testid="text-selected-segment-empty"
            >
              No completed trades in this segment.
              {totalTrades > 0
                ? ` This run has ${totalTrades.toLocaleString()} simulated closed trades across the other segments. Select a row in All segment results to inspect them.`
                : ' No completed trades in the other segments either.'}
            </p>
          )}
        </section>
      )}

      <div className="grid gap-3 md:grid-cols-[1fr_1.3fr]">
        <section className="panel p-4" data-testid="card-selected-period">
          <p className="eyebrow">Chronological holdout</p>
          <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-center gap-2">
            <div>
              <p className="text-[11px] text-muted-foreground">
                Development ends
              </p>
              <p
                className="num mt-1 text-[12px] font-medium"
                data-testid="text-development-end"
              >
                {dateTime(result.developmentEnd)}
              </p>
            </div>
            <ChevronRight className="h-4 w-4 text-teal" aria-hidden />
            <div>
              <p className="text-[11px] text-muted-foreground">
                Out-of-sample starts
              </p>
              <p
                className="num mt-1 text-[12px] font-medium"
                data-testid="text-oos-start"
              >
                {dateTime(result.outOfSampleStart)}
              </p>
            </div>
          </div>
          <p className="mt-3 border-t border-border/50 pt-2 text-[10.5px] leading-relaxed text-muted-foreground">
            The out-of-sample window follows development in time. It is a
            historical holdout, not a forecast.
          </p>
        </section>
        <section
          className="panel grid grid-cols-2 gap-y-4 p-4 sm:grid-cols-4"
          data-testid="grid-segment-metrics"
        >
          <Metric
            label="Net cumulative P&L"
            value={money(metrics?.cumulativePnlUsdt)}
            tone={signTone(metrics?.cumulativePnlUsdt)}
            testId="text-metric-cumulative-pnl"
          />
          <Metric
            label="Return on starting equity"
            value={percent(metrics?.cumulativeReturnPct)}
            tone={signTone(metrics?.cumulativeReturnPct)}
            testId="text-metric-return"
          />
          <Metric
            label="Max drawdown"
            value={money(metrics?.maxDrawdownUsdt)}
            tone="text-loss"
            note={percent(metrics?.maxDrawdownPct)}
            testId="text-metric-drawdown"
          />
          <Metric
            label="Trades / win rate"
            value={`${metrics?.tradeCount ?? 0} / ${percent(metrics?.winRatePct)}`}
            testId="text-metric-trades"
          />
          <Metric
            label="Expectancy"
            value={money(metrics?.expectancyUsdt)}
            tone={signTone(metrics?.expectancyUsdt)}
            testId="text-metric-expectancy"
          />
          <Metric
            label="Profit factor"
            value={numeric(metrics?.profitFactor)}
            note={metrics?.profitFactorNote ?? undefined}
            testId="text-metric-profit-factor"
          />
          <Metric
            label="Ending equity"
            value={money(metrics?.endingEquityUsdt)}
            testId="text-metric-ending-equity"
          />
          <Metric
            label="Wins / losses / flat"
            value={`${metrics?.wins ?? 0} / ${metrics?.losses ?? 0} / ${metrics?.breakeven ?? 0}`}
            testId="text-metric-win-loss"
          />
        </section>
      </div>

      <BacktestSegmentSummary
        segments={result.segments}
        selectedIndex={segmentIndex}
        onSelect={setSegmentIndex}
        formatMoney={money}
        formatPercent={percent}
      />

      {result.segments.length ? (
        <section
          className="panel overflow-hidden"
          data-testid="section-segment-performance"
        >
          <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-3 py-2">
            <div className="flex items-center gap-2 px-1">
              <BarChart3 className="h-3.5 w-3.5 text-teal" aria-hidden />
              <h2 className="text-[12.5px] font-semibold">
                Cumulative performance
              </h2>
            </div>
            <SegmentSwitch
              segments={result.segments}
              value={segmentIndex}
              onChange={setSegmentIndex}
            />
          </header>
          {segment ? (
            <div className="grid gap-3 p-3 lg:grid-cols-[minmax(0,1.35fr)_minmax(220px,.65fr)]">
              <div className="min-w-0">
                <div className="mb-1 flex items-center justify-between gap-2 px-1">
                  <p className="text-[10.5px] capitalize text-muted-foreground">
                    {segment.marketType} {segment.side} ·{' '}
                    {segment.period.replace('_', ' ')}
                  </p>
                  <p className="num text-[10px] text-muted-foreground">
                    {dateOnly(segment.periodStart)} —{' '}
                    {dateOnly(segment.periodEnd)}
                  </p>
                </div>
                <EquityChart segment={segment} />
              </div>
              <div className="rounded border border-border/50 bg-background/25 px-3 py-2">
                <p className="eyebrow">Segment breakdown</p>
                <dl className="mt-1">
                  <KV label="Market / side">
                    {segment.marketType} · {segment.side}
                  </KV>
                  <KV label="Period">{segment.period.replace('_', ' ')}</KV>
                  <KV label="Closed trades">
                    {segment.metrics.tradeCount.toLocaleString()}
                  </KV>
                  <KV label="Wins / losses / flat">
                    {segment.metrics.wins} / {segment.metrics.losses} /{' '}
                    {segment.metrics.breakeven}
                  </KV>
                  <KV label="Net win rate">
                    {percent(segment.metrics.winRatePct)}
                  </KV>
                  <KV label="Net expectancy">
                    {money(segment.metrics.expectancyUsdt)}
                  </KV>
                  <KV label="Fees">
                    <span className="text-muted-foreground">
                      {money(segment.metrics.totalFeesUsdt)}
                    </span>
                  </KV>
                  <KV label="Maker / taker fees">
                    {orderAwareRun
                      ? `${money(segment.metrics.totalMakerFeesUsdt)} / ${money(segment.metrics.totalTakerFeesUsdt)}`
                      : 'Not separated in this saved run'}
                  </KV>
                  <KV label="Funding">
                    <span
                      className={signTone(segment.metrics.totalFundingUsdt)}
                    >
                      {money(segment.metrics.totalFundingUsdt)}
                    </span>
                  </KV>
                  <KV label="Legacy spread / slippage">
                    <span className="text-muted-foreground">
                      {money(segment.metrics.totalSpreadCostUsdt)} /{' '}
                      {money(segment.metrics.totalSlippageCostUsdt)}
                    </span>
                  </KV>
                  <KV label="Unfilled limit orders">
                    {orderAwareRun
                      ? segment.metrics.unfilledEntryOrders.toLocaleString()
                      : 'Not tracked in this saved run'}
                  </KV>
                  <KV label="Unclosed excluded">
                    {segment.metrics.excludedUnclosedTrades.toLocaleString()}
                  </KV>
                  {Object.entries(segment.entryDiagnostics ?? {}).map(
                    ([reason, count]) => (
                      <KV key={reason} label={reason.replaceAll('_', ' ')}>
                        {count}
                      </KV>
                    ),
                  )}
                </dl>
              </div>
            </div>
          ) : (
            <p
              className="px-4 py-8 text-center text-xs text-muted-foreground"
              data-testid="empty-result-segments"
            >
              No market segments were returned for this run.
            </p>
          )}
        </section>
      ) : (
        <section
          className="panel px-4 py-8 text-center"
          data-testid="empty-result-segments"
        >
          <p className="text-sm font-medium">No segment results returned</p>
          <p className="mt-1 text-xs text-muted-foreground">
            The saved run contains no market or period breakdown.
          </p>
        </section>
      )}

      <Coverage result={result} />

      <section
        className="panel overflow-hidden"
        data-testid="section-historical-ai-review"
      >
        <header className="border-b border-border/60 px-4 py-3">
          <h2 className="text-[13px] font-semibold">
            Ask AI about this saved run
          </h2>
          <p className="mt-1 text-[10.5px] leading-relaxed text-muted-foreground">
            Reviews the immutable data snapshot and a bounded sample of trades
            and candles. Advisory only; it cannot recommend or place a live
            order.
          </p>
        </header>
        <div className="space-y-3 p-4">
          {!reviewEnabled && (
            <p
              className="rounded border border-warn/30 bg-warn/[0.05] px-3 py-2 text-[10.5px] leading-relaxed text-muted-foreground"
              data-testid="notice-historical-ai-review-disabled"
            >
              {reviewNotice}
            </p>
          )}
          <label className="block">
            <span className="eyebrow">Your question</span>
            <textarea
              value={reviewQuestion}
              onChange={(event) => setReviewQuestion(event.target.value)}
              maxLength={500}
              rows={3}
              placeholder="For example: What were the most common reasons entries did not fill?"
              data-testid="input-historical-review-question"
              className="focus-ring mt-1.5 w-full rounded border border-input bg-background px-3 py-2 text-[12px] leading-relaxed"
            />
          </label>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-[10px] text-muted-foreground">
              No AI call occurs until you submit. Each review uses configured
              per-run and daily cost caps.
            </p>
            <button
              type="button"
              disabled={
                !reviewEnabled || reviewRun.isPending || !reviewQuestion.trim()
              }
              onClick={() =>
                reviewRun.mutate(
                  {
                    runId: result.id,
                    data: { question: reviewQuestion.trim() },
                  },
                  {
                    onSuccess: () => {
                      setReviewQuestion('');
                      void queryClient.invalidateQueries({
                        queryKey: getListStrategyBacktestReviewsQueryKey(
                          result.id,
                        ),
                      });
                    },
                  },
                )
              }
              data-testid="button-ask-historical-review"
              className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded border border-teal/50 bg-teal/10 px-3 text-[11px] font-semibold text-teal disabled:cursor-not-allowed disabled:opacity-50"
            >
              {reviewRun.isPending ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <CircleHelp className="h-3.5 w-3.5" aria-hidden />
              )}
              {reviewRun.isPending ? 'Reviewing saved evidence' : 'Ask AI'}
            </button>
          </div>
          {reviewRun.isError && (
            <p
              role="alert"
              className="rounded border border-loss/30 bg-loss/[0.05] px-3 py-2 text-[10.5px] text-loss"
              data-testid="error-historical-ai-review"
            >
              The review was not completed. Check the saved-run access and
              review budget before trying again; failed provider calls are not
              retried automatically.
            </p>
          )}
          {reviewsQuery.isError && (
            <p className="text-[10px] text-muted-foreground" role="status">
              Saved review history could not be loaded. A new review will still
              be stored against this backtest.
            </p>
          )}
          {savedReviews.slice(0, 5).map((review) => (
            <HistoricalReviewCard key={review.id} review={review} />
          ))}
        </div>
      </section>

      <section
        className="panel overflow-hidden"
        data-testid="section-underlying-trades"
      >
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
          <div>
            <h2 className="text-[13px] font-semibold">Underlying trades</h2>
            <p className="mt-0.5 text-[10.5px] text-muted-foreground">
              Selected market, side, and chronological period. Target and stop
              are shown beside the simulated order fills.
            </p>
          </div>
          <span
            className="num rounded border border-border px-2 py-1 text-[10px] text-muted-foreground"
            data-testid="text-trade-count"
          >
            {segment?.trades.length ?? 0} records
          </span>
        </header>
        {segment ? (
          <>
            <TradeTable trades={segment.trades} />
            <EntryOrderTable orders={segment.entryOrders} />
          </>
        ) : (
          <div className="px-4 py-7 text-center text-xs text-muted-foreground">
            Trade detail is not available for this result.
          </div>
        )}
      </section>

      <section
        className="rounded border border-border/60 bg-background/30 px-4 py-3"
        data-testid="section-result-provenance"
      >
        <div className="flex items-start gap-2.5">
          <CircleHelp
            className="mt-0.5 h-4 w-4 shrink-0 text-teal"
            aria-hidden
          />
          <div className="min-w-0">
            <p className="text-[11.5px] font-medium">
              Hypothetical historical analysis — not a forecast, signal, or
              profitability guarantee.
            </p>
            <p
              className="mt-1 break-all font-mono text-[9.5px] leading-relaxed text-muted-foreground"
              data-testid="text-result-data-hash"
            >
              Data SHA-256 · {result.dataSha256}
            </p>
            {result.notes.length > 0 && (
              <ul
                className="mt-2 list-inside list-disc space-y-1 text-[10.5px] text-muted-foreground"
                data-testid="list-result-notes"
              >
                {result.notes.map((note, index) => (
                  <li key={`${index}-${note}`}>{note}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function EmaStrategyLabPage() {
  const queryClient = useQueryClient();
  const overviewQuery = useGetStrategyLabOverview({
    query: { queryKey: getGetStrategyLabOverviewQueryKey() },
  });
  const listQuery = useListStrategyBacktests({
    query: { queryKey: getListStrategyBacktestsQueryKey() },
  });
  const createRun = useCreateStrategyBacktest();
  const [symbol, setSymbol] = useState<Pair>('BTCUSDT');
  const [days, setDays] = useState(14);
  const [selectedId, setSelectedId] = useState('');
  const strategy = overviewQuery.data?.strategy;
  const recentRuns = listQuery.data ?? overviewQuery.data?.recentRuns ?? [];
  const activeRunId = selectedId || recentRuns[0]?.id || '';
  const detailQuery = useGetStrategyBacktest(activeRunId, {
    query: {
      queryKey: getGetStrategyBacktestQueryKey(activeRunId),
      enabled: Boolean(activeRunId),
    },
  });
  const result =
    detailQuery.data ??
    (createRun.data?.id === activeRunId ? createRun.data : undefined);
  const isNoSavedRuns =
    !listQuery.isLoading &&
    !listQuery.isFetching &&
    !listQuery.isError &&
    recentRuns.length === 0;

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const input: BacktestInput = {
      symbol,
      days,
    };
    createRun.reset();
    createRun.mutate(
      { data: input },
      {
        onSuccess: (saved) => {
          setSelectedId(saved.id);
          void queryClient.invalidateQueries({
            queryKey: getGetStrategyLabOverviewQueryKey(),
          });
          void queryClient.invalidateQueries({
            queryKey: getListStrategyBacktestsQueryKey(),
          });
        },
      },
    );
  };

  const chooseRun = (id: string) => {
    setSelectedId(id);
    if (id) createRun.reset();
  };

  const loading = overviewQuery.isLoading || listQuery.isLoading;
  const failed =
    overviewQuery.isError &&
    !overviewQuery.data &&
    listQuery.isError &&
    !listQuery.data;

  return (
    <div
      data-testid="page-strategy-lab"
      className="mx-auto max-w-[1500px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7"
    >
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Research / Strategy Laboratory / Module 08</p>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-semibold tracking-tight">
            Strategy Laboratory <PaperLabel />
          </h1>
          <p className="mt-1 max-w-2xl text-[12.5px] leading-relaxed text-muted-foreground">
            Historical behavior, measured carefully. Public OKX evidence only;
            no automated execution.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            data-testid="button-refresh-strategy-lab"
            onClick={() => {
              void overviewQuery.refetch();
              void listQuery.refetch();
              if (activeRunId) void detailQuery.refetch();
            }}
            disabled={
              overviewQuery.isFetching ||
              listQuery.isFetching ||
              detailQuery.isFetching
            }
            className="focus-ring inline-flex h-9 items-center gap-2 rounded border border-border bg-card px-3 text-[12px] transition-colors hover:border-teal/50 disabled:opacity-60"
          >
            <RefreshCw
              className={cn(
                'h-3.5 w-3.5 text-teal',
                (overviewQuery.isFetching || listQuery.isFetching) &&
                  'animate-spin',
              )}
              aria-hidden
            />
            Refresh records
          </button>
        </div>
      </header>

      <section className="mt-5 grid gap-3 lg:grid-cols-[1.2fr_.8fr]">
        <div
          className="rounded border border-warn/35 bg-warn/[0.055] px-4 py-3.5"
          data-testid="notice-historical-only"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle
              className="mt-0.5 h-4 w-4 shrink-0 text-warn"
              aria-hidden
            />
            <div>
              <p className="text-[12.5px] font-semibold">
                Historical analysis only
              </p>
              <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                Results are hypothetical historical analysis, not a forecast,
                trading signal, or profitability guarantee. This laboratory
                cannot propose, approve, permit, or place trades.
              </p>
            </div>
          </div>
        </div>
        <div
          className="panel flex items-center justify-between gap-3 px-4 py-3"
          data-testid="notice-ai-review-disabled"
        >
          <div className="flex items-start gap-2.5">
            <FlaskConical
              className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground"
              aria-hidden
            />
            <div>
              <p className="text-[12px] font-semibold">Historical AI review</p>
              <p className="mt-0.5 text-[10.5px] text-muted-foreground">
                {overviewQuery.data?.status.historicalAiReviewEnabled
                  ? 'Manually requested · bounded by the server budget'
                  : 'Disabled · no provider calls are made'}
              </p>
              {overviewQuery.data?.status.notice && (
                <p
                  className="mt-1 max-w-md text-[10px] leading-relaxed text-muted-foreground"
                  data-testid="text-lab-status-notice"
                >
                  {overviewQuery.data.status.notice}
                </p>
              )}
            </div>
          </div>
          <span
            data-testid="status-historical-ai-review"
            className="rounded border border-border bg-muted/60 px-2.5 py-1.5 text-[10px] text-muted-foreground"
          >
            {overviewQuery.data?.status.historicalAiReviewEnabled
              ? 'Ready'
              : 'Locked'}
          </span>
        </div>
      </section>

      {overviewQuery.data?.status && (
        <section
          className="mt-3 grid gap-2 sm:grid-cols-3"
          data-testid="status-lab-gates"
        >
          <div className="panel flex items-center justify-between gap-2 px-3 py-2">
            <span className="eyebrow">Historical review</span>
            <span
              className="text-[10.5px] font-medium text-muted-foreground"
              data-testid="status-paid-review"
            >
              {overviewQuery.data.status.historicalAiReviewEnabled
                ? 'Enabled with budget'
                : 'Disabled'}
            </span>
          </div>
          <div className="panel flex items-center justify-between gap-2 px-3 py-2">
            <span className="eyebrow">Trading path</span>
            <span
              className="text-[10.5px] font-medium text-muted-foreground"
              data-testid="status-trading-path"
            >
              {overviewQuery.data.status.tradingEnabled
                ? 'Server reports enabled'
                : 'Disabled · research only'}
            </span>
          </div>
          <div className="panel flex items-center justify-between gap-2 px-3 py-2">
            <span className="eyebrow">Proposal creation</span>
            <span
              className="text-[10.5px] font-medium text-muted-foreground"
              data-testid="status-proposal-creation"
            >
              {overviewQuery.data.status.proposalCreationEnabled
                ? 'Server reports enabled'
                : 'Disabled'}
            </span>
          </div>
        </section>
      )}

      {overviewQuery.isError && (
        <div className="mt-4">
          <ErrorNote
            error={overviewQuery.error}
            title="Strategy definition could not be loaded"
            onRetry={() => overviewQuery.refetch()}
          />
        </div>
      )}

      {loading && (
        <div
          className="mt-4 grid gap-4"
          aria-busy="true"
          data-testid="loading-strategy-lab"
        >
          <Skeleton className="h-40 bg-muted" />
          <div className="grid gap-4 lg:grid-cols-[330px_1fr]">
            <Skeleton className="h-72 bg-muted" />
            <Skeleton className="h-72 bg-muted" />
          </div>
        </div>
      )}

      {!loading && failed && (
        <div
          className="panel mt-4 px-5 py-8 text-center"
          data-testid="error-strategy-lab"
        >
          <AlertTriangle className="mx-auto h-5 w-5 text-loss" aria-hidden />
          <p className="mt-2 text-sm font-medium">
            Research records are unavailable
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            The saved strategy and backtests could not be retrieved. No
            placeholder results are shown.
          </p>
          <button
            type="button"
            data-testid="button-retry-strategy-lab"
            onClick={() => {
              void overviewQuery.refetch();
              void listQuery.refetch();
            }}
            className="focus-ring mt-4 rounded border border-border px-3 py-1.5 text-xs hover:border-teal/50"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && strategy && (
        <>
          <div className="mt-4">
            <Configuration strategy={strategy} />
            {result &&
              result.strategy.strategyVersion !== strategy.strategyVersion && (
                <Configuration strategy={result.strategy} />
              )}
          </div>

          <div className="mt-4 grid items-start gap-4 xl:grid-cols-[318px_minmax(0,1fr)]">
            <aside className="space-y-4">
              <section
                className="panel overflow-hidden"
                data-testid="section-run-configuration"
              >
                <header className="flex items-center justify-between border-b border-border/60 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <SlidersHorizontal
                      className="h-3.5 w-3.5 text-teal"
                      aria-hidden
                    />
                    <h2 className="text-[13px] font-semibold">
                      Run parameters
                    </h2>
                  </div>
                  <span className="eyebrow">Historical</span>
                </header>
                <form
                  onSubmit={submit}
                  className="space-y-3.5 p-4"
                  data-testid="form-backtest"
                >
                  <label className="block">
                    <span className="eyebrow">Instrument</span>
                    <select
                      value={symbol}
                      onChange={(event) =>
                        setSymbol(event.target.value as Pair)
                      }
                      data-testid="select-backtest-symbol"
                      className="focus-ring mt-1.5 h-9 w-full rounded border border-input bg-background px-2.5 text-[12px]"
                    >
                      {PAIR_OPTIONS.map((pair) => (
                        <option value={pair} key={pair}>
                          {pair}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block">
                    <span className="flex items-center justify-between">
                      <span className="eyebrow">Lookback window</span>
                      <span
                        className="num text-[10px] text-muted-foreground"
                        data-testid="text-days-value"
                      >
                        {days} days
                      </span>
                    </span>
                    <input
                      type="range"
                      min={7}
                      max={30}
                      step={1}
                      value={days}
                      onChange={(event) => setDays(Number(event.target.value))}
                      data-testid="input-backtest-days"
                      aria-label="Lookback window in days"
                      className="mt-2 h-1.5 w-full cursor-pointer accent-[hsl(var(--accent-teal))]"
                    />
                    <span className="mt-1 flex justify-between font-mono text-[9px] text-muted-foreground">
                      <span>7 days</span>
                      <span>30 days</span>
                    </span>
                  </label>
                  <p
                    className="text-[10.5px] leading-relaxed text-muted-foreground"
                    data-testid="text-cost-assumption-hint"
                  >
                    Entries rest at the pullback limit for up to four 15m
                    candles. Maker/taker fee defaults and available futures
                    funding are included; no separate spread or slippage charge.
                  </p>
                  <button
                    type="submit"
                    disabled={createRun.isPending || !strategy}
                    data-testid="button-run-backtest"
                    className="focus-ring inline-flex h-10 w-full items-center justify-center gap-2 rounded border border-teal/60 bg-teal/10 text-[12px] font-semibold text-teal transition-colors hover:bg-teal/15 disabled:cursor-not-allowed disabled:opacity-55"
                  >
                    {createRun.isPending ? (
                      <RefreshCw
                        className="h-3.5 w-3.5 animate-spin"
                        aria-hidden
                      />
                    ) : (
                      <FlaskConical className="h-3.5 w-3.5" aria-hidden />
                    )}
                    {createRun.isPending
                      ? 'Running historical test'
                      : 'Run backtest'}
                  </button>
                </form>
                {createRun.isPending && (
                  <div
                    className="space-y-2 border-t border-border/50 px-4 py-3"
                    role="status"
                    data-testid="status-backtest-running"
                  >
                    <p className="text-[11px] text-muted-foreground">
                      Loading public historical records and calculating
                      closed-candle results…
                    </p>
                    <Skeleton className="h-2 w-full bg-muted" />
                    <Skeleton className="h-2 w-3/4 bg-muted" />
                  </div>
                )}
                {createRun.isError && (
                  <div
                    className="border-t border-loss/30 bg-loss/[0.04] px-4 py-3"
                    role="alert"
                    data-testid="error-backtest-run"
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle
                        className="mt-0.5 h-3.5 w-3.5 shrink-0 text-loss"
                        aria-hidden
                      />
                      <div>
                        <p className="text-[11.5px] font-medium text-loss">
                          Backtest failed
                        </p>
                        <p className="mt-1 text-[10.5px] leading-relaxed text-muted-foreground">
                          No new run was saved. Existing results remain
                          unchanged; retry after reviewing the data service
                          status.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                {createRun.isSuccess && (
                  <p
                    role="status"
                    data-testid="status-backtest-saved"
                    className="flex items-center gap-2 border-t border-profit/30 bg-profit/[0.05] px-4 py-2.5 text-[10.5px] text-profit"
                  >
                    <Check className="h-3.5 w-3.5" aria-hidden /> Saved result
                    loaded below.
                  </p>
                )}
              </section>

              <section
                className="panel overflow-hidden"
                data-testid="section-saved-runs"
              >
                <header className="flex items-center justify-between border-b border-border/60 px-4 py-3">
                  <div>
                    <h2 className="text-[13px] font-semibold">
                      Saved backtests
                    </h2>
                    <p className="mt-0.5 text-[10px] text-muted-foreground">
                      Persisted historical runs
                    </p>
                  </div>
                  <span
                    className="num rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground"
                    data-testid="text-saved-run-count"
                  >
                    {recentRuns.length}
                  </span>
                </header>
                {listQuery.isError && (
                  <div className="px-3 py-3" data-testid="error-saved-runs">
                    <ErrorNote
                      error={listQuery.error}
                      title="Saved run list could not be loaded"
                      onRetry={() => listQuery.refetch()}
                    />
                  </div>
                )}
                {listQuery.isLoading || listQuery.isFetching ? (
                  <div
                    className="space-y-2 p-3"
                    aria-busy="true"
                    data-testid="loading-saved-runs"
                  >
                    {[0, 1, 2].map((item) => (
                      <Skeleton className="h-12 bg-muted" key={item} />
                    ))}
                  </div>
                ) : recentRuns.length === 0 ? (
                  <div
                    className="px-4 py-7 text-center"
                    data-testid="empty-saved-runs"
                  >
                    <Clock3
                      className="mx-auto h-5 w-5 text-muted-foreground/60"
                      aria-hidden
                    />
                    <p className="mt-2 text-[12px] font-medium">
                      No saved runs yet
                    </p>
                    <p className="mt-1 text-[10.5px] leading-relaxed text-muted-foreground">
                      Run a backtest to persist a reproducible result. No sample
                      results are invented.
                    </p>
                  </div>
                ) : (
                  <div
                    className="max-h-[340px] overflow-y-auto"
                    data-testid="list-saved-runs"
                  >
                    {recentRuns.map((run) => (
                      <RunRow
                        key={run.id}
                        run={run}
                        active={run.id === activeRunId}
                        onSelect={() => chooseRun(run.id)}
                      />
                    ))}
                  </div>
                )}
              </section>
            </aside>

            <main className="min-w-0 space-y-4">
              {detailQuery.isError && (
                <div
                  className="panel px-4 py-4"
                  data-testid="error-selected-backtest"
                >
                  <ErrorNote
                    error={detailQuery.error}
                    title="Saved result could not be opened"
                    onRetry={() => detailQuery.refetch()}
                  />
                </div>
              )}
              {activeRunId &&
                (detailQuery.isLoading ||
                  (detailQuery.isFetching && !result)) && (
                  <div
                    className="space-y-3"
                    aria-busy="true"
                    data-testid="loading-backtest-result"
                  >
                    <Skeleton className="h-32 bg-muted" />
                    <Skeleton className="h-64 bg-muted" />
                    <Skeleton className="h-44 bg-muted" />
                  </div>
                )}
              {result && (
                <ResultView
                  key={result.id}
                  result={result}
                  onChooseAnother={chooseRun}
                  latestRunId={recentRuns[0]?.id ?? result.id}
                  reviewEnabled={
                    overviewQuery.data?.status.historicalAiReviewEnabled ??
                    false
                  }
                  reviewNotice={
                    overviewQuery.data?.status.notice ??
                    'Historical AI review is not configured.'
                  }
                />
              )}
              {!activeRunId && isNoSavedRuns && (
                <div
                  className="panel desk-grid px-5 py-12 text-center"
                  data-testid="empty-backtest-workspace"
                >
                  <div className="mx-auto grid h-11 w-11 place-items-center rounded border border-teal/30 bg-teal/[0.06]">
                    <BarChart3 className="h-5 w-5 text-teal" aria-hidden />
                  </div>
                  <p className="mt-3 text-sm font-semibold">
                    A clean historical sample starts here
                  </p>
                  <p className="mx-auto mt-1 max-w-md text-[11.5px] leading-relaxed text-muted-foreground">
                    Choose a supported instrument and bounded lookback, then
                    inspect limit fills and compare development with
                    chronological out-of-sample behavior.
                  </p>
                </div>
              )}
              {!activeRunId && !isNoSavedRuns && listQuery.isError && (
                <div
                  className="panel px-4 py-8 text-center text-xs text-muted-foreground"
                  data-testid="empty-backtest-result"
                >
                  The saved-run list could not be confirmed. Refresh records
                  before treating this workspace as empty.
                </div>
              )}
              {activeRunId &&
                !result &&
                !detailQuery.isLoading &&
                !detailQuery.isFetching &&
                !detailQuery.isError && (
                  <div
                    className="panel px-4 py-8 text-center"
                    data-testid="empty-backtest-result"
                  >
                    <p className="text-sm font-medium">Result not available</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      The selected run is not present in the response. Refresh
                      the saved records and try again.
                    </p>
                  </div>
                )}
            </main>
          </div>
          <footer
            className="mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-border/50 pt-3 text-[10px] text-muted-foreground"
            data-testid="footer-lab-disclaimer"
          >
            <span>STAI research cockpit · Public OKX evidence</span>
            <span>Historical analysis only · No order path</span>
          </footer>
        </>
      )}

      {!loading && !strategy && !failed && !overviewQuery.isError && (
        <div
          className="panel mt-4 px-4 py-8 text-center"
          data-testid="empty-strategy-definition"
        >
          <p className="text-sm font-medium">Strategy definition unavailable</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Backtests are disabled until the server supplies the current
            reviewed configuration.
          </p>
        </div>
      )}
    </div>
  );
}

export default function StrategyLabPage() {
  const [activeView, setActiveView] = useState<'baseline' | 'challenger'>(
    'baseline',
  );

  return (
    <>
      <nav
        className="mx-auto flex max-w-[1500px] gap-1 px-4 pt-4 sm:px-6 lg:px-8"
        aria-label="Strategy research views"
        data-testid="nav-strategy-lab-views"
      >
        <button
          type="button"
          className={cn(
            'focus-ring rounded border border-border/70 px-3 py-2 text-[11px] transition-colors',
            activeView === 'baseline'
              ? 'bg-card text-foreground'
              : 'text-muted-foreground hover:text-foreground',
          )}
          aria-pressed={activeView === 'baseline'}
          data-testid="button-view-ema-baseline"
          onClick={() => setActiveView('baseline')}
        >
          EMA baseline
        </button>
        <button
          type="button"
          className={cn(
            'focus-ring rounded border border-border/70 px-3 py-2 text-[11px] transition-colors',
            activeView === 'challenger'
              ? 'bg-card text-foreground'
              : 'text-muted-foreground hover:text-foreground',
          )}
          aria-pressed={activeView === 'challenger'}
          data-testid="button-view-structural-challenger"
          onClick={() => setActiveView('challenger')}
        >
          Structural pullback challenger
        </button>
      </nav>
      {activeView === 'challenger' ? (
        <StructuralChallenger />
      ) : (
        <EmaStrategyLabPage />
      )}
    </>
  );
}
