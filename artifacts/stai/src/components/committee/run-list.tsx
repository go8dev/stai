import { Lock } from 'lucide-react';
import {
  type CommitteeOverview,
  type CommitteeRunSummary,
} from '@workspace/api-client-react';
import { formatManilaDateTime, formatUtcDateTime } from '@/lib/format';
import { cn } from '@/lib/utils';
import { KV } from '@/components/desk';
import { Tag, statusTone } from './primitives';

export function RunList({
  runs,
  selected,
  onSelect,
}: {
  runs: CommitteeRunSummary[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="panel h-fit" aria-labelledby="h-runs">
      <header className="border-b border-border px-4 py-2.5">
        <h2 id="h-runs" className="text-[13px] font-medium">
          Run history ({runs.length})
        </h2>
      </header>
      {runs.length === 0 ? (
        <div className="px-4 py-6" data-testid="text-no-runs">
          <p className="text-[13px]">No committee runs recorded.</p>
          <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
            Runs appear here once paid automation or manual runs are enabled
            under approved limits.
          </p>
        </div>
      ) : (
        <ul
          className="max-h-[560px] divide-y divide-border/60 overflow-y-auto"
          role="listbox"
          aria-label="Committee runs"
        >
          {runs.map((r) => {
            const on = r.id === selected;
            return (
              <li key={r.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={on}
                  data-testid={`button-run-${r.id}`}
                  onClick={() => onSelect(r.id)}
                  className={cn(
                    'focus-ring w-full px-4 py-2.5 text-left hover:bg-background/40',
                    on &&
                      'bg-background/60 shadow-[inset_2px_0_0_hsl(var(--accent-teal))]',
                  )}
                >
                  <span className="flex items-center gap-2">
                    <span className="text-[13px] font-medium">{r.symbol}</span>
                    <span className="text-[11px] text-muted-foreground">
                      {r.marketType}
                    </span>
                    <span className="ml-auto">
                      <Tag tone={statusTone(r.status)}>{r.status}</Tag>
                    </span>
                  </span>
                  <span className="num mt-1 flex justify-between gap-2 text-[11px] text-muted-foreground">
                    <span title={`${formatUtcDateTime(r.startedAt)} UTC`}>
                      {formatManilaDateTime(r.startedAt)} MNL
                    </span>
                    <span>
                      {r.action ?? 'no action'} / {r.findingCount} f
                    </span>
                  </span>
                  {r.error && (
                    <span
                      className="mt-1 block truncate text-[11px] text-loss"
                      title={r.error}
                    >
                      {r.error}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

export function GateBanner({ o }: { o: CommitteeOverview }) {
  return (
    <section
      className="panel grid gap-4 p-4 md:grid-cols-[1fr_1fr_1.4fr]"
      data-testid="panel-gate"
    >
      <div className="flex items-start gap-2.5">
        <Lock className="mt-0.5 h-4 w-4 shrink-0 text-warn" aria-hidden />
        <div className="text-[12.5px]">
          <p className="font-medium">Runs disabled</p>
          <p className="text-muted-foreground">
            Paid automation {o.paidAutomationEnabled ? 'on' : 'off'}. Manual
            paid runs {o.manualPaidRunsEnabled ? 'on' : 'off'}. Entry gate{' '}
            {o.entryGate ?? 'closed'}.
          </p>
        </div>
      </div>
      <dl>
        <KV label="Benchmark" testId="text-benchmark-state">
          {o.benchmarkState}
        </KV>
        <KV label="Limits" testId="text-limits-status">
          {o.limitsStatus}
        </KV>
      </dl>
      <div>
        <p className="eyebrow">Next step</p>
        <p
          className="mt-1 text-[12.5px] leading-relaxed"
          data-testid="text-next-step"
        >
          {o.nextStep}
        </p>
      </div>
    </section>
  );
}
