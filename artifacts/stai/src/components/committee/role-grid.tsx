import { useState } from 'react';
import {
  type Evidence,
  type Finding,
  type RoleDefinition,
} from '@workspace/api-client-react';
import { NotAvailable } from '@/components/desk';
import { ConfidenceBar, EvidenceRefs, Tag, TextList } from './primitives';

export function RoleGrid({
  roles,
  findings,
  known,
  hasRun,
}: {
  roles: RoleDefinition[];
  findings: Finding[] | null;
  known: Map<string, Evidence>;
  hasRun: boolean;
}) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <section className="panel" aria-labelledby="h-roles">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-4 py-2.5">
        <h2 id="h-roles" className="text-[13px] font-medium">
          Committee roles
        </h2>
        <span className="text-[11.5px] text-muted-foreground">
          Confidence is each role's subjective rating, not a calibrated
          probability.
        </span>
      </header>
      <ul className="divide-y divide-border/60">
        {roles.map((r, i) => {
          const f = findings?.find((x) => x.role === r.id) ?? null;
          const isOpen = open === r.id && !!f;
          return (
            <li key={r.id} data-testid={`row-role-${r.id}`}>
              <button
                type="button"
                disabled={!f}
                aria-expanded={f ? isOpen : undefined}
                data-testid={`button-role-${r.id}`}
                onClick={() => setOpen(isOpen ? null : r.id)}
                className="focus-ring grid w-full grid-cols-[28px_1fr_auto] items-center gap-3 px-4 py-2.5 text-left hover:bg-background/40 disabled:cursor-default disabled:hover:bg-transparent"
              >
                <span className="num text-[11px] text-muted-foreground">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span className="min-w-0">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="text-[13px] font-medium">{r.name}</span>
                    <Tag tone="border-border text-muted-foreground">
                      {r.mode}
                    </Tag>
                  </span>
                  <span className="mt-0.5 block truncate text-[12px] text-muted-foreground">
                    {f
                      ? f.summary
                      : hasRun
                        ? 'No finding recorded for this role in the selected run.'
                        : 'No runs yet.'}
                  </span>
                </span>
                {f ? (
                  <ConfidenceBar value={f.confidence} />
                ) : (
                  <NotAvailable>no finding</NotAvailable>
                )}
              </button>
              {isOpen && f && (
                <div className="rise space-y-3 bg-background/40 px-4 pb-4 pl-[56px] pt-1">
                  <p className="whitespace-pre-wrap text-[13px] leading-relaxed">
                    {f.summary}
                  </p>
                  <div className="grid gap-4 md:grid-cols-3">
                    <TextList
                      title="Supporting"
                      items={f.supporting}
                      tone="text-profit"
                    />
                    <TextList
                      title="Opposing"
                      items={f.opposing}
                      tone="text-loss"
                    />
                    <TextList
                      title="Uncertainties"
                      items={f.uncertainties}
                      tone="text-warn"
                    />
                  </div>
                  <div>
                    <p className="eyebrow mb-1">Evidence cited</p>
                    <EvidenceRefs ids={f.evidenceIds} known={known} />
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
