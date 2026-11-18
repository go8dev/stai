import type { BacktestSegment } from '@workspace/api-client-react';
import { cn } from '@/lib/utils';

export function segmentLabel(segment: BacktestSegment) {
  const market = segment.marketType === 'spot' ? 'Spot' : 'Futures';
  const side = segment.side === 'long' ? 'Long' : 'Short';
  const period =
    segment.period === 'out_of_sample' ? 'Out-of-sample' : 'Development';
  return `${market} · ${side} · ${period}`;
}

type Props = {
  segments: BacktestSegment[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  formatMoney: (value: number | string | null | undefined) => string;
  formatPercent: (value: number | string | null | undefined) => string;
};

export function BacktestSegmentSummary({
  segments,
  selectedIndex,
  onSelect,
  formatMoney,
  formatPercent,
}: Props) {
  if (!segments.length) return null;
  const total = segments.reduce(
    (sum, item) => sum + item.metrics.tradeCount,
    0,
  );
  return (
    <section
      className="panel overflow-hidden"
      data-testid="section-segment-summary"
    >
      <header className="border-b border-border/60 px-4 py-3">
        <h2 className="text-[13px] font-semibold">All segment results</h2>
        <p className="mt-1 text-xs" data-testid="text-all-segment-trades">
          <span className="num font-semibold">{total.toLocaleString()}</span>{' '}
          simulated closed trades across {segments.length} segments.
        </p>
        <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
          Each row is an independent simulation, not a combined portfolio.
          Returns, equity and drawdown are not added together. Select a segment
          to update the metric cards, chart and underlying trades.
        </p>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-[11.5px]">
          <caption className="sr-only">
            Compare independent backtest segments and choose the result to
            inspect.
          </caption>
          <thead className="border-b border-border/60 bg-background/20">
            <tr className="text-muted-foreground">
              {[
                'Market · side · period',
                'Trades',
                'Wins / losses / flat',
                'Win rate',
                'Net P&L',
                'Max drawdown',
              ].map((label, index) => (
                <th
                  key={label}
                  scope="col"
                  className={cn(
                    'eyebrow px-3 py-2 font-normal',
                    index !== 0 && 'text-right',
                  )}
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {segments.map((segment, index) => {
              const selected = index === selectedIndex;
              const { metrics } = segment;
              const key = `${segment.marketType}-${segment.side}-${segment.period}`;
              return (
                <tr
                  key={key}
                  className={cn(
                    'border-b border-border/40 last:border-0',
                    selected && 'bg-teal/[0.07]',
                  )}
                  data-testid={`summary-segment-${key}`}
                  data-selected={selected}
                >
                  <th scope="row" className="px-3 py-2 font-normal">
                    <button
                      type="button"
                      onClick={() => onSelect(index)}
                      aria-pressed={selected}
                      className={cn(
                        'focus-ring rounded py-1 text-left hover:text-teal',
                        selected && 'font-medium text-teal',
                      )}
                      data-testid={`button-summary-segment-${key}`}
                    >
                      {segmentLabel(segment)}
                      {selected && (
                        <span className="ml-2 text-[10px]">Selected</span>
                      )}
                    </button>
                  </th>
                  <td className="num px-3 py-2 text-right">
                    {metrics.tradeCount.toLocaleString()}
                  </td>
                  <td className="num px-3 py-2 text-right">
                    {metrics.wins} / {metrics.losses} / {metrics.breakeven}
                  </td>
                  <td className="num px-3 py-2 text-right">
                    {formatPercent(metrics.winRatePct)}
                  </td>
                  <td
                    className={cn(
                      'num px-3 py-2 text-right',
                      Number(metrics.cumulativePnlUsdt) > 0
                        ? 'text-profit'
                        : Number(metrics.cumulativePnlUsdt) < 0
                          ? 'text-loss'
                          : 'text-muted-foreground',
                    )}
                  >
                    {formatMoney(metrics.cumulativePnlUsdt)}
                  </td>
                  <td className="num px-3 py-2 text-right">
                    <div>{formatMoney(metrics.maxDrawdownUsdt)}</div>
                    <div className="text-[10px] text-muted-foreground">
                      {formatPercent(metrics.maxDrawdownPct)}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {total === 0 && (
        <p className="border-t border-border/50 px-4 py-3 text-xs text-muted-foreground">
          No completed trades in any segment of this saved run. Win rates are
          unavailable, not zero.
        </p>
      )}
    </section>
  );
}
