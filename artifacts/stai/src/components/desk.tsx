import type { ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import type { CheckStatus } from '@workspace/api-client-react';
import { cn } from '@/lib/utils';
import { readApiError } from '@/lib/api-errors';

export function PaperLabel({ className }: { className?: string }) {
  return (
    <span
      data-testid="paper-label"
      title="Paper trading only. No real money moves."
      className={cn(
        'inline-flex items-center gap-1.5 rounded-[3px] border border-warn/50 bg-warn/10 px-1.5 py-0.5 font-mono text-[10.5px] font-semibold tracking-[0.18em] text-warn',
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-warn" aria-hidden />
      PAPER
    </span>
  );
}

export function BrandMark({ size = 22 }: { size?: number }) {
  return (
    <img
      src={`${import.meta.env.BASE_URL}favicon.svg`}
      width={size}
      height={size}
      alt=""
      aria-hidden
      className="shrink-0"
    />
  );
}

const STATUS_STYLE: Record<
  CheckStatus,
  { label: string; dot: string; text: string; ring: string }
> = {
  ok: {
    label: 'OK',
    dot: 'bg-profit',
    text: 'text-profit',
    ring: 'border-profit/35 bg-profit/10',
  },
  degraded: {
    label: 'Degraded',
    dot: 'bg-warn',
    text: 'text-warn',
    ring: 'border-warn/40 bg-warn/10',
  },
  down: {
    label: 'Down',
    dot: 'bg-loss',
    text: 'text-loss',
    ring: 'border-loss/40 bg-loss/10',
  },
};

export function StatusPill({
  status,
  testId,
  large,
}: {
  status: CheckStatus;
  testId?: string;
  large?: boolean;
}) {
  const s = STATUS_STYLE[status];
  return (
    <span
      data-testid={testId}
      data-status={status}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-[3px] border font-mono font-medium uppercase tracking-[0.12em]',
        large ? 'px-2.5 py-1 text-xs' : 'px-1.5 py-0.5 text-[10.5px]',
        s.ring,
        s.text,
      )}
    >
      <span
        className={cn('rounded-full', large ? 'h-2 w-2' : 'h-1.5 w-1.5', s.dot)}
        aria-hidden
      />
      {s.label}
    </span>
  );
}

export function NotAvailable({
  children = 'not available',
}: {
  children?: ReactNode;
}) {
  return (
    <span className="font-mono text-xs italic text-muted-foreground/70">
      {children}
    </span>
  );
}

export function KV({
  label,
  children,
  testId,
}: {
  label: string;
  children: ReactNode;
  testId?: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-border/60 py-1.5 last:border-b-0">
      <dt className="shrink-0 text-xs text-muted-foreground">{label}</dt>
      <dd
        data-testid={testId}
        className="num min-w-0 truncate text-right text-[12.5px] text-foreground"
      >
        {children}
      </dd>
    </div>
  );
}

export function ErrorNote({
  error,
  title,
  onRetry,
}: {
  error: unknown;
  title: string;
  onRetry?: () => void;
}) {
  const e = readApiError(error);
  return (
    <div
      role="alert"
      className="rounded-md border border-loss/40 bg-loss/[0.07] p-3"
    >
      <div className="flex items-start gap-2.5">
        <AlertTriangle
          className="mt-0.5 h-4 w-4 shrink-0 text-loss"
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="mt-0.5 text-[13px] text-muted-foreground">
            {e.message}
          </p>
          <dl className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs">
            {e.status !== null && (
              <div className="flex gap-1.5">
                <dt className="text-muted-foreground">HTTP</dt>
                <dd className="num">{e.status}</dd>
              </div>
            )}
            <div className="flex min-w-0 gap-1.5">
              <dt className="text-muted-foreground">Correlation ID</dt>
              <dd
                className="num select-all break-all"
                data-testid="text-error-correlation-id"
              >
                {e.correlationId ?? <NotAvailable />}
              </dd>
            </div>
          </dl>
        </div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="focus-ring shrink-0 rounded border border-border px-2.5 py-1 text-xs text-foreground transition-colors hover:border-teal/60 hover:text-teal"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
