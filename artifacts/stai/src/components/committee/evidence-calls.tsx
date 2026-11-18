import { ExternalLink } from 'lucide-react';
import { type CommitteeCall, type Evidence } from '@workspace/api-client-react';
import { KV, NotAvailable } from '@/components/desk';
import {
  Cost,
  Dur,
  Stamp,
  Tag,
  asText,
  safeHttps,
  statusTone,
  tok,
} from './primitives';

export function EvidencePanel({ items }: { items: Evidence[] }) {
  return (
    <section className="panel min-w-0" aria-labelledby="h-ev">
      <header className="border-b border-border px-4 py-2.5">
        <h2 id="h-ev" className="text-[13px] font-medium">
          Evidence snapshot ({items.length})
        </h2>
      </header>
      {items.length === 0 ? (
        <p className="p-4 text-[12.5px] text-muted-foreground">
          No evidence recorded.
        </p>
      ) : (
        <ul className="divide-y divide-border/60">
          {items.map((e) => {
            const entries = Object.entries(e.data ?? {});
            return (
              <li
                key={e.id}
                id={`evidence-${encodeURIComponent(e.id)}`}
                className="scroll-mt-20 px-4 py-3 target:bg-teal/[0.06]"
                data-testid={`row-evidence-${e.id}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="num text-[11.5px] text-muted-foreground">
                    {e.id}
                  </span>
                  <Tag tone={statusTone(e.status)}>{e.status}</Tag>
                  <span className="text-[12px]">{e.kind}</span>
                  <span className="ml-auto num text-[11.5px] text-muted-foreground">
                    <Stamp value={e.observedAt} />
                  </span>
                </div>
                <p className="mt-1 whitespace-pre-wrap text-[12.5px] leading-relaxed">
                  {e.summary}
                </p>
                <p className="mt-1 text-[11.5px] text-muted-foreground">
                  Source:{' '}
                  {safeHttps(e.source) ? (
                    <a
                      href={safeHttps(e.source)!}
                      target="_blank"
                      rel="noopener noreferrer nofollow"
                      className="focus-ring inline-flex items-center gap-1 text-teal underline-offset-2 hover:underline"
                    >
                      {e.source}{' '}
                      <ExternalLink className="h-3 w-3" aria-hidden />
                    </a>
                  ) : (
                    <span className="num">{e.source}</span>
                  )}
                </p>
                {entries.length > 0 && (
                  <details className="mt-1.5">
                    <summary className="focus-ring cursor-pointer text-[11.5px] text-muted-foreground hover:text-foreground">
                      Data ({entries.length} fields)
                    </summary>
                    <dl className="mt-1 grid gap-x-6 sm:grid-cols-2">
                      {entries.map(([k, v]) => (
                        <KV key={k} label={k}>
                          <span title={asText(v)}>
                            {asText(v) || <NotAvailable />}
                          </span>
                        </KV>
                      ))}
                    </dl>
                  </details>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

export function CallsPanel({ calls }: { calls: CommitteeCall[] }) {
  return (
    <section className="panel min-w-0" aria-labelledby="h-calls">
      <header className="border-b border-border px-4 py-2.5">
        <h2 id="h-calls" className="text-[13px] font-medium">
          Stages and model calls ({calls.length})
        </h2>
      </header>
      {calls.length === 0 ? (
        <p className="p-4 text-[12.5px] text-muted-foreground">
          No stage calls recorded.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead>
              <tr className="border-b border-border">
                {['Stage', 'Status', 'Model', 'In', 'Out', 'Cost', 'Time'].map(
                  (h) => (
                    <th key={h} className="eyebrow px-3 py-2 font-normal">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {calls.map((c, i) => (
                <tr
                  key={i}
                  className="border-b border-border/50"
                  data-testid={`row-call-${i}`}
                >
                  <td className="px-3 py-1.5">{c.stage}</td>
                  <td className="px-3 py-1.5">
                    <Tag tone={statusTone(c.status)}>{c.status}</Tag>
                  </td>
                  <td className="num px-3 py-1.5 text-muted-foreground">
                    {c.model}
                  </td>
                  <td className="num px-3 py-1.5">{tok(c.inputTokens)}</td>
                  <td className="num px-3 py-1.5">{tok(c.outputTokens)}</td>
                  <td className="num px-3 py-1.5">
                    <Cost v={c.costUsd} />
                  </td>
                  <td className="num px-3 py-1.5">
                    <Dur ms={c.durationMs} />
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
