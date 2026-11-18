import { type ReactNode } from 'react';
import { formatManilaDateTime, formatUtcDateTime } from '@/lib/format';
import { fmtFixed } from '@/lib/display-number';
import { cn } from '@/lib/utils';
import { NotAvailable } from '@/components/desk';
import type { Evidence } from '@workspace/api-client-react';

export const RUNNING = new Set(['running']);
export const isRunning = (s: string) => RUNNING.has(s.toLowerCase());

export function Stamp({ value }: { value: string | null | undefined }) {
  if (!value) return <NotAvailable />;
  return (
    <time dateTime={value} title={`${formatUtcDateTime(value)} UTC`}>
      {formatManilaDateTime(value)}{' '}
      <span className="text-muted-foreground">MNL</span>
    </time>
  );
}

export function Cost({ v }: { v: number | string | null }) {
  if (v === null || v === undefined)
    return <NotAvailable>unknown</NotAvailable>;
  const s = fmtFixed(v, 4);
  return s === null ? <NotAvailable>unknown</NotAvailable> : <>${s}</>;
}

export function Dur({ ms }: { ms: number | null }) {
  if (ms === null || ms === undefined) return <NotAvailable />;
  return (
    <>{(ms / 1000).toLocaleString('en-US', { maximumFractionDigits: 1 })} s</>
  );
}

export function tok(n: number | null) {
  return n === null || n === undefined ? (
    <NotAvailable>unknown</NotAvailable>
  ) : (
    n.toLocaleString('en-US')
  );
}

export function statusTone(s: string) {
  const l = s.toLowerCase();
  if (isRunning(l)) return 'border-teal/40 bg-teal/10 text-teal';
  if (
    ['completed', 'complete', 'ok', 'succeeded', 'success', 'fresh'].includes(l)
  )
    return 'border-profit/40 bg-profit/10 text-profit';
  if (['failed', 'error', 'unavailable'].includes(l))
    return 'border-loss/40 bg-loss/10 text-loss';
  return 'border-warn/40 bg-warn/10 text-warn';
}

export function Tag({
  children,
  tone,
  testId,
}: {
  children: ReactNode;
  tone: string;
  testId?: string;
}) {
  return (
    <span
      data-testid={testId}
      className={cn(
        'inline-flex items-center rounded-[3px] border px-1.5 py-0.5 font-mono text-[10.5px] uppercase tracking-[0.1em]',
        tone,
      )}
    >
      {children}
    </span>
  );
}

export function safeHttps(v: unknown): string | null {
  if (typeof v !== 'string') return null;
  try {
    const u = new URL(v);
    return u.protocol === 'https:' ? u.href : null;
  } catch {
    return null;
  }
}

export function asText(v: unknown): string {
  if (v === null || v === undefined) return '';
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean')
    return String(v);
  try {
    return JSON.stringify(v);
  } catch {
    return '';
  }
}

export function TextList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: string;
}) {
  return (
    <div>
      <p className={cn('eyebrow', tone)}>
        {title} ({items.length})
      </p>
      {items.length === 0 ? (
        <p className="mt-1 text-[12px] italic text-muted-foreground/70">
          None stated.
        </p>
      ) : (
        <ul className="mt-1 space-y-1 text-[12.5px] leading-relaxed">
          {items.map((t, i) => (
            <li key={i} className="border-l border-border pl-2">
              {t}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function EvidenceRefs({
  ids,
  known,
}: {
  ids: string[];
  known: Map<string, Evidence>;
}) {
  return (
    <div className="flex flex-wrap gap-1">
      {ids.map((id) => {
        const e = known.get(id);
        return (
          <a
            key={id}
            href={`#evidence-${encodeURIComponent(id)}`}
            title={
              e ? `${e.kind} / ${e.status}` : 'Not found in this run snapshot'
            }
            className={cn(
              'focus-ring num rounded-[3px] border px-1.5 py-0.5 text-[10.5px] hover:border-teal/60',
              e
                ? e.status === 'fresh'
                  ? 'border-border'
                  : 'border-warn/50 text-warn'
                : 'border-loss/50 text-loss',
            )}
          >
            {id}
          </a>
        );
      })}
    </div>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div
      className="flex items-center gap-2"
      title="Subjective role confidence, not a calibrated probability"
    >
      <div className="h-1 w-16 overflow-hidden rounded bg-muted" aria-hidden>
        <div
          className="h-full origin-left bg-chart-5"
          style={{ transform: `scaleX(${v / 100})` }}
        />
      </div>
      <span className="num text-[11.5px] text-muted-foreground">
        {v}/100 subj.
      </span>
    </div>
  );
}
