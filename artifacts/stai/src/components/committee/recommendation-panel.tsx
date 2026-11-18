import { AlertTriangle } from 'lucide-react';
import {
  type CommitteeRunDetail,
  type Evidence,
  type Recommendation,
} from '@workspace/api-client-react';
import { fmtFixed } from '@/lib/display-number';
import { KV, NotAvailable } from '@/components/desk';
import {
  ConfidenceBar,
  EvidenceRefs,
  Tag,
  TextList,
  isRunning,
} from './primitives';

export function RecommendationPanel({
  rec,
  d,
  known,
}: {
  rec: Recommendation | null;
  d: CommitteeRunDetail;
  known: Map<string, Evidence>;
}) {
  return (
    <section
      className="panel"
      aria-labelledby="h-rec"
      data-testid="panel-recommendation"
    >
      <header className="border-b border-border px-4 py-2.5">
        <h2 id="h-rec" className="text-[13px] font-medium">
          Research recommendation
        </h2>
        <p className="mt-0.5 text-[11.5px] text-muted-foreground">
          Advisory research only. Not a risk approval and not an actionable
          proposal.
        </p>
      </header>
      <div className="space-y-4 p-4">
        {d.evidenceStale && (
          <p
            className="flex items-start gap-2 rounded border-l-2 border-warn/70 bg-warn/[0.06] px-2.5 py-1.5 text-[12px]"
            data-testid="text-evidence-stale"
          >
            <AlertTriangle
              className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warn"
              aria-hidden
            />
            Evidence for this run is stale. Read it as a historical record, not
            current market conditions.
          </p>
        )}
        {!rec ? (
          <p
            className="text-[12.5px] text-muted-foreground"
            data-testid="text-no-recommendation"
          >
            {isRunning(d.status)
              ? 'The committee has not produced a recommendation yet.'
              : 'No recommendation was recorded for this run.'}
          </p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <Tag
                tone={
                  rec.action === 'abstain'
                    ? 'border-border text-muted-foreground'
                    : 'border-teal/40 text-teal'
                }
                testId="text-recommendation-action"
              >
                {rec.action.replace('_', ' ')}
              </Tag>
              <ConfidenceBar value={rec.confidence} />
            </div>
            <p
              className="whitespace-pre-wrap text-[13px] leading-relaxed"
              data-testid="text-thesis"
            >
              {rec.thesis}
            </p>
            <div className="grid gap-4 sm:grid-cols-3">
              <TextList
                title="Supporting"
                items={rec.supporting}
                tone="text-profit"
              />
              <TextList
                title="Opposing"
                items={rec.opposing}
                tone="text-loss"
              />
              <TextList
                title="Uncertainties"
                items={rec.uncertainties}
                tone="text-warn"
              />
            </div>
            <div>
              <p className="eyebrow mb-1">Research terms</p>
              {rec.terms ? (
                <dl className="rounded border border-dashed border-border px-3">
                  <KV label="Entry">
                    {fmtFixed(rec.terms.entry, 4) ?? <NotAvailable />}
                  </KV>
                  <KV label="Stop">
                    {fmtFixed(rec.terms.stop, 4) ?? <NotAvailable />}
                  </KV>
                  <KV label="Target">
                    {fmtFixed(rec.terms.target, 4) ?? <NotAvailable />}
                  </KV>
                  <KV label="Notional USDT">
                    {fmtFixed(rec.terms.notionalUsdt, 2) ?? <NotAvailable />}
                  </KV>
                  <KV label="Leverage">{rec.terms.leverage}x</KV>
                </dl>
              ) : (
                <NotAvailable>no terms</NotAvailable>
              )}
            </div>
            <div>
              <p className="eyebrow mb-1">Evidence cited</p>
              <EvidenceRefs ids={rec.evidenceIds} known={known} />
            </div>
          </>
        )}
        {d.memory.length > 0 && (
          <TextList
            title="Memory carried"
            items={d.memory}
            tone="text-muted-foreground"
          />
        )}
      </div>
    </section>
  );
}
