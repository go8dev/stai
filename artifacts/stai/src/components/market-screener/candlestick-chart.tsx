import type { CandlePoint } from '@workspace/api-client-react';
import type { MtfZone } from '@workspace/api-client-react';
import { fmtPrice } from '@/lib/display-number';
import { formatManilaTime, formatUtcDateTime } from '@/lib/format';

export function CandlestickChart({
  candles,
  timeframe,
  symbol,
  zones = [],
  currentPrice = null,
  selectedZoneId = null,
  onSelectZone,
}: {
  candles: CandlePoint[];
  timeframe: string;
  symbol: string;
  zones?: MtfZone[];
  currentPrice?: number | string | null;
  selectedZoneId?: string | null;
  onSelectZone?: (id: string) => void;
}) {
  const completed = candles.filter((candle) => candle.complete).slice(-80);
  if (!completed.length) {
    return (
      <div className="flex h-[220px] items-center justify-center border-t border-border/60 text-xs text-muted-foreground">
        No completed {timeframe} candles returned for {symbol}.
      </div>
    );
  }

  const values = completed.flatMap((candle) => [
    Number(candle.high),
    Number(candle.low),
  ]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || Math.max(max * 0.001, 1);
  const width = 760;
  const height = 220;
  const plotBottom = 186;
  const plotTop = 12;
  const y = (price: number) =>
    plotTop + ((max - price) / span) * (plotBottom - plotTop);
  const step = width / completed.length;
  const bodyWidth = Math.max(2, Math.min(8, step * 0.58));
  const last = completed[completed.length - 1];

  return (
    <div className="w-full overflow-hidden border-t border-border/60">
      <div className="flex items-center justify-between px-3 py-2 text-[10px] text-muted-foreground">
        <span>
          {completed.length} completed candles · {timeframe}
        </span>
        <span
          className="num"
          title={`${fmtPrice(last.close)} · ${formatUtcDateTime(last.openedAt)} UTC`}
        >
          Last close {fmtPrice(last.close)}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${symbol} ${timeframe} candlestick chart from OKX`}
        className="block h-[220px] w-full"
        preserveAspectRatio="none"
      >
        {zones
          .filter(
            (zone) => Number(zone.upper) >= min && Number(zone.lower) <= max,
          )
          .map((zone) => {
            const upper = y(Number(zone.upper));
            const lower = y(Number(zone.lower));
            const color =
              zone.kind === 'support' ? 'hsl(164 55% 49%)' : 'hsl(5 58% 61%)';
            return (
              <g
                key={zone.id}
                onClick={() => onSelectZone?.(zone.id)}
                className="cursor-pointer"
              >
                <title>{`${zone.kind} · ${zone.sourceTimeframe.toUpperCase()} · ${fmtPrice(zone.lower)}–${fmtPrice(zone.upper)} · ${zone.state} · confirmed ${formatUtcDateTime(zone.confirmedAt)} UTC`}</title>
                <rect
                  data-testid={`chart-zone-${zone.id}`}
                  x="0"
                  y={Math.min(upper, lower)}
                  width={width}
                  height={Math.max(2, Math.abs(lower - upper))}
                  fill={color}
                  opacity={
                    selectedZoneId === zone.id
                      ? '.20'
                      : zone.sourceTimeframe === timeframe.toLowerCase()
                        ? '.14'
                        : '.06'
                  }
                  stroke={color}
                  strokeWidth={
                    selectedZoneId === zone.id
                      ? '1.5'
                      : zone.sourceTimeframe === timeframe.toLowerCase()
                        ? '1'
                        : '.5'
                  }
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectZone?.(zone.id);
                  }}
                />
                <text
                  x="4"
                  y={Math.min(upper, lower) + 10}
                  fill={color}
                  opacity={
                    zone.sourceTimeframe === timeframe.toLowerCase()
                      ? '1'
                      : '.65'
                  }
                  fontSize="8"
                  fontFamily="monospace"
                >
                  {zone.sourceTimeframe.toUpperCase()} {zone.kind.toUpperCase()}{' '}
                  {fmtPrice(zone.lower)}–{fmtPrice(zone.upper)}
                </text>
              </g>
            );
          })}
        {[0, 0.5, 1].map((ratio) => {
          const price = max - span * ratio;
          const yy = plotTop + (plotBottom - plotTop) * ratio;
          return (
            <g key={ratio}>
              <line
                x1="0"
                x2={width}
                y1={yy}
                y2={yy}
                stroke="hsl(217 30% 28% / .45)"
                strokeDasharray="3 5"
              />
              <text
                x={width - 4}
                y={yy - 3}
                textAnchor="end"
                fill="hsl(215 20% 65%)"
                fontSize="9"
                fontFamily="monospace"
              >
                {fmtPrice(price)}
              </text>
            </g>
          );
        })}
        {currentPrice != null &&
          Number(currentPrice) >= min &&
          Number(currentPrice) <= max && (
            <g>
              <line
                x1="0"
                x2={width}
                y1={y(Number(currentPrice))}
                y2={y(Number(currentPrice))}
                stroke="hsl(174 72% 43%)"
                strokeDasharray="4 3"
              />
              <text
                x="5"
                y={y(Number(currentPrice)) - 3}
                fill="hsl(174 72% 43%)"
                fontSize="8"
                fontFamily="monospace"
              >
                ticker {fmtPrice(currentPrice)}
              </text>
            </g>
          )}
        {completed.map((candle, index) => {
          const open = Number(candle.open);
          const close = Number(candle.close);
          const high = Number(candle.high);
          const low = Number(candle.low);
          const rising = close >= open;
          const color = rising ? 'hsl(164 55% 49%)' : 'hsl(5 58% 61%)';
          const x = step * index + step / 2;
          const bodyTop = Math.min(y(open), y(close));
          const bodyHeight = Math.max(1, Math.abs(y(open) - y(close)));
          return (
            <g key={candle.openedAt}>
              <title>{`${formatManilaTime(candle.openedAt)} MNL · ${formatUtcDateTime(candle.openedAt)} UTC · O ${fmtPrice(candle.open)} H ${fmtPrice(candle.high)} L ${fmtPrice(candle.low)} C ${fmtPrice(candle.close)}`}</title>
              <line
                x1={x}
                x2={x}
                y1={y(high)}
                y2={y(low)}
                stroke={color}
                strokeWidth="1"
              />
              <rect
                x={x - bodyWidth / 2}
                y={bodyTop}
                width={bodyWidth}
                height={bodyHeight}
                fill={color}
                opacity=".9"
              />
            </g>
          );
        })}
        <text x="4" y={height - 6} fill="hsl(215 20% 65%)" fontSize="9">
          {formatManilaTime(completed[0].openedAt)} MNL
        </text>
        <text
          x={width - 4}
          y={height - 6}
          textAnchor="end"
          fill="hsl(215 20% 65%)"
          fontSize="9"
        >
          {formatManilaTime(last.openedAt)} MNL
        </text>
      </svg>
    </div>
  );
}
