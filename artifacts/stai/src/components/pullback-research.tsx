import type { EntryResearch } from '@workspace/api-client-react';
import { formatManilaDateTime } from '@/lib/format';

const labels: Record<string, string> = {
  waiting: 'Waiting',
  pullback_detected: 'Pullback detected',
  confirmed: 'Confirmed entry candidate',
  invalidated: 'Invalidated',
  expired: 'Expired',
  insufficient_data: 'Insufficient data',
};

export function researchSummary(research: EntryResearch | null | undefined) {
  if (!research) return 'Insufficient data';
  return Object.entries(research.sides ?? {})
    .map(
      ([side, evidence]) =>
        `${side}: ${labels[evidence.stage ?? 'insufficient_data'] ?? evidence.stage}`,
    )
    .join(' · ');
}

export function PullbackResearch({
  research,
}: {
  research: EntryResearch | null | undefined;
}) {
  if (!research)
    return <p>Entry research unavailable. No candidate is authorized.</p>;
  return (
    <section
      className="min-w-0 max-w-[calc(100vw-4.25rem)] break-words rounded border border-teal/30 bg-teal/5 p-3 sm:max-w-none lg:col-span-3"
      data-testid="pullback-research"
    >
      <h3 className="text-sm font-medium">
        Pullback entry research · {research.strategyVersion}
      </h3>
      <p className="mt-1 text-xs text-muted-foreground">{research.note}</p>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {Object.entries(research.sides ?? {}).map(([side, evidence]) => (
          <div
            key={side}
            className="min-w-0 rounded border border-border p-3"
            data-testid={`entry-stage-${side}`}
          >
            <p className="text-xs font-semibold uppercase">
              {side} ·{' '}
              {labels[evidence.stage ?? 'insufficient_data'] ?? evidence.stage}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {evidence.reason}
            </p>
            <dl className="mt-2 space-y-1 text-xs">
              <div>
                Pullback closed:{' '}
                {evidence.pullbackAt
                  ? formatManilaDateTime(evidence.pullbackAt)
                  : '—'}
              </div>
              <div>
                Confirmation closed:{' '}
                {evidence.confirmationAt
                  ? formatManilaDateTime(evidence.confirmationAt)
                  : '—'}
              </div>
              <div>
                Confirmation window: {evidence.barsWaited}/4 subsequent candles
              </div>
              {Object.entries(evidence.checks ?? {}).map(([rule, passed]) => (
                <div key={rule}>
                  {passed ? 'Pass' : 'Not met'} · {rule}
                </div>
              ))}
            </dl>
            {evidence.setupId && (
              <p className="mt-2 break-all font-mono text-[10px] text-muted-foreground">
                Setup {evidence.setupId}
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
