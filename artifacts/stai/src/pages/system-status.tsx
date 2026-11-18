import type { ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, RefreshCw, ShieldCheck, ShieldX } from 'lucide-react';
import {
  useGetSystemStatus,
  useListAuditEvents,
  useVerifyAuditTrail,
  getGetSystemStatusQueryKey,
  getListAuditEventsQueryKey,
  type AuditVerification,
  type CheckStatus,
  type SystemStatus,
} from '@workspace/api-client-react';
import {
  formatManilaDateTime,
  formatUtcDateTime,
  formatManilaTime,
  formatUtcTime,
} from '@/lib/format';
import { cn } from '@/lib/utils';
import { ErrorNote, KV, NotAvailable, StatusPill } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';

const EVENTS_PARAMS = { limit: 12 };

const EVENT_LABEL: Record<string, string> = {
  'auth.signin': 'Signed in',
  'auth.signin_refused': 'Sign-in refused',
  'auth.signout': 'Signed out',
};

function eventLabel(eventType: string): string {
  return EVENT_LABEL[eventType] ?? eventType;
}

function actorLabel(event: { actorType: string; actorId?: string | null }) {
  return event.actorId
    ? `${event.actorType}:${event.actorId}`
    : event.actorType;
}

/** The start of a record's hash: enough to compare by eye. The full value is the tooltip. */
function shortHash(hash: string): string {
  return hash.slice(0, 8);
}

const BREAK_LABEL: Record<string, string> = {
  sequence_gap: 'Sequence gap',
  prev_hash_mismatch: 'Previous-hash mismatch',
  hash_mismatch: 'Hash mismatch',
};

function uptime(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  const hms = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`;
  return d > 0 ? `${d}d ${hms}` : hms;
}

function ms(value: number | null) {
  return value === null ? (
    <NotAvailable />
  ) : (
    `${value.toLocaleString('en-US', { maximumFractionDigits: 1 })} ms`
  );
}

function Stamp({ value }: { value: string | null }) {
  if (!value) return <NotAvailable />;
  return (
    <span title={`${formatUtcDateTime(value)} UTC`}>
      {formatManilaDateTime(value)}{' '}
      <span className="text-muted-foreground">MNL</span>
    </span>
  );
}

function Panel({
  title,
  status,
  testId,
  children,
  className,
}: {
  title: string;
  status?: CheckStatus;
  testId?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn('panel flex flex-col', className)}
      data-testid={testId}
      data-status={status}
    >
      <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-2.5">
        <h2 className="text-[13px] font-medium">{title}</h2>
        {status && <StatusPill status={status} />}
      </header>
      <div className="flex-1 px-4 py-2">{children}</div>
    </section>
  );
}

function Detail({ text }: { text: string | null }) {
  if (!text) return null;
  return (
    <p className="mb-1 mt-2 rounded border-l-2 border-warn/70 bg-warn/[0.06] px-2.5 py-1.5 text-[12.5px] text-foreground/90">
      {text}
    </p>
  );
}

function Clock({
  zone,
  primary,
  secondary,
}: {
  zone: string;
  primary: string;
  secondary: string;
}) {
  return (
    <div className="min-w-0">
      <p className="eyebrow">{zone}</p>
      <p className="num mt-0.5 text-xl font-medium tracking-tight sm:text-2xl">
        {primary}
      </p>
      <p className="num text-[11.5px] text-muted-foreground">{secondary}</p>
    </div>
  );
}

function StatusBody({ s }: { s: SystemStatus }) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Panel
          title="Backend"
          status={s.backend.status}
          testId="status-backend"
        >
          <dl>
            <KV label="Environment">{s.backend.environment}</KV>
            <KV label="Uptime">{uptime(s.backend.uptimeSeconds)}</KV>
            <KV label="Python">{s.backend.pythonVersion}</KV>
          </dl>
        </Panel>

        <Panel
          title="Database"
          status={s.database.status}
          testId="status-database"
        >
          <dl>
            <KV label="Latency">{ms(s.database.latencyMs)}</KV>
            <KV label="Server">
              {s.database.serverVersion ?? <NotAvailable />}
            </KV>
            <KV label="Schema">
              <span
                className={
                  s.database.schemaReady ? 'text-foreground' : 'text-warn'
                }
              >
                {s.database.schemaReady ? 'ready' : 'not ready'}
              </span>
            </KV>
            <KV label="Migration">
              {s.database.migrationRevision ?? <NotAvailable />}
            </KV>
          </dl>
          {s.database.missingTables.length > 0 && (
            <div className="mt-2">
              <p className="eyebrow">Missing tables</p>
              <p className="num mt-1 break-all text-[12px] text-warn">
                {s.database.missingTables.join(', ')}
              </p>
            </div>
          )}
          <Detail text={s.database.detail} />
        </Panel>

        <Panel
          title="Market data"
          status={s.marketData.status}
          testId="status-market-data"
        >
          <dl>
            <KV label="Provider">{s.marketData.provider}</KV>
            <KV label="Latency">{ms(s.marketData.latencyMs)}</KV>
            <KV label="Clock skew">{ms(s.marketData.clockSkewMs)}</KV>
            <KV label="Exchange time">
              {s.marketData.exchangeTime ? (
                formatManilaTime(s.marketData.exchangeTime)
              ) : (
                <NotAvailable />
              )}
            </KV>
            <KV label="Checked">{formatManilaTime(s.marketData.checkedAt)}</KV>
          </dl>
          <p
            className="num mt-1.5 truncate text-[11px] text-muted-foreground"
            title={s.marketData.endpoint}
          >
            {s.marketData.endpoint}
          </p>
          <Detail text={s.marketData.detail} />
        </Panel>

        <Panel
          title="Audit trail"
          status={s.audit.status}
          testId="status-audit"
        >
          <dl>
            <KV label="Events">{s.audit.eventCount.toLocaleString('en-US')}</KV>
            <KV label="Last event">
              {s.audit.lastEventType ?? <NotAvailable />}
            </KV>
            <KV label="Last at">
              {s.audit.lastEventAt ? (
                formatManilaTime(s.audit.lastEventAt)
              ) : (
                <NotAvailable />
              )}
            </KV>
          </dl>
          <Detail text={s.audit.detail} />
        </Panel>
      </div>
    </>
  );
}

function VerificationResult({ v }: { v: AuditVerification }) {
  return (
    <div
      data-testid="result-audit-verification"
      data-ok={v.ok ? 'true' : 'false'}
      role={v.ok ? 'status' : 'alert'}
      className={cn(
        'rise mt-3 rounded-md border p-3',
        v.ok
          ? 'border-profit/35 bg-profit/[0.06]'
          : 'border-loss/50 bg-loss/[0.08]',
      )}
    >
      <div className="flex items-center gap-2">
        {v.ok ? (
          <ShieldCheck className="h-4 w-4 text-profit" aria-hidden />
        ) : (
          <ShieldX className="h-4 w-4 text-loss" aria-hidden />
        )}
        <p className="text-sm font-medium">
          {v.ok ? 'Chain intact' : 'Chain broken'}
        </p>
      </div>
      {v.firstBreak && (
        <div className="mt-2.5 rounded border border-loss/40 bg-background/60 p-2.5">
          <p className="eyebrow text-loss">First break</p>
          <dl className="mt-1">
            <KV label="At sequence">#{v.firstBreak.seq}</KV>
            <KV label="Reason">
              {BREAK_LABEL[v.firstBreak.reason] ?? v.firstBreak.reason}
            </KV>
          </dl>
          <p className="mt-1.5 text-[12.5px] text-foreground/90">
            {v.firstBreak.detail}
          </p>
        </div>
      )}
      <dl className="mt-2">
        <KV label="Events checked">
          {v.eventsChecked.toLocaleString('en-US')}
        </KV>
        <KV label="Range">
          {v.firstSeq !== null && v.lastSeq !== null ? (
            `#${v.firstSeq} to #${v.lastSeq}`
          ) : (
            <NotAvailable />
          )}
        </KV>
        <KV label="Head hash">
          {v.headHash ? (
            <span title={v.headHash}>{v.headHash.slice(0, 16)}</span>
          ) : (
            <NotAvailable />
          )}
        </KV>
        <KV label="Duration">
          {v.durationMs.toLocaleString('en-US', { maximumFractionDigits: 1 })}{' '}
          ms
        </KV>
        <KV label="Verified">
          <Stamp value={v.verifiedAt} />
        </KV>
      </dl>
    </div>
  );
}

function AuditSection() {
  const qc = useQueryClient();
  const events = useListAuditEvents(EVENTS_PARAMS, {
    query: {
      refetchInterval: 30000,
      queryKey: getListAuditEventsQueryKey(EVENTS_PARAMS),
    },
  });
  const verify = useVerifyAuditTrail({
    mutation: {
      onSuccess: () => {
        qc.invalidateQueries({ queryKey: getGetSystemStatusQueryKey() });
        qc.invalidateQueries({
          queryKey: getListAuditEventsQueryKey(EVENTS_PARAMS),
        });
      },
    },
  });

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_340px]">
      {/* The events are laid out by the width of this panel, not of the screen. */}
      <section className="panel @container min-w-0">
        <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-2.5">
          <h2 className="text-[13px] font-medium">Recent audit events</h2>
          {events.data && (
            <span className="num text-[11.5px] text-muted-foreground">
              {events.data.events.length} of{' '}
              {events.data.total.toLocaleString('en-US')}
            </span>
          )}
        </header>
        {events.isLoading ? (
          <div className="space-y-2 p-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-6 w-full bg-muted" />
            ))}
          </div>
        ) : events.isError ? (
          <div className="p-4">
            <ErrorNote
              error={events.error}
              title="Audit events could not be loaded"
              onRetry={() => events.refetch()}
            />
          </div>
        ) : events.data && events.data.events.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-[13px]">No audit events recorded yet.</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Sign-ins and sign-outs appear here as they happen.
            </p>
          </div>
        ) : (
          <>
            {/* Narrow panel (phones): one block per event, nothing to scroll sideways. */}
            <ul className="divide-y divide-border/50 @[560px]:hidden">
              {events.data?.events.map((e) => (
                <li
                  key={e.seq}
                  data-testid={`card-audit-event-${e.seq}`}
                  className="px-4 py-2.5"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                    <span
                      className={cn(
                        'text-[13px]',
                        e.eventType === 'auth.signin_refused' && 'text-warn',
                      )}
                    >
                      {eventLabel(e.eventType)}
                    </span>
                    <span
                      className="num min-w-0 truncate text-xs text-muted-foreground"
                      title={e.actorId ?? undefined}
                    >
                      {actorLabel(e)}
                    </span>
                  </div>
                  <div className="mt-0.5 flex flex-wrap items-baseline justify-between gap-x-3">
                    <span className="num text-xs">
                      <Stamp value={e.occurredAt} />
                    </span>
                    <span
                      className="num text-[11.5px] text-muted-foreground"
                      title={e.hash}
                    >
                      #{e.seq} / {shortHash(e.hash)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>

            {/* Wider panel: a table. */}
            <div className="hidden overflow-x-auto @[560px]:block">
              <table className="w-full text-left text-[12.5px]">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="eyebrow py-2 pl-4 pr-2 font-normal">Seq</th>
                    <th className="eyebrow px-2 py-2 font-normal">
                      Time (Manila)
                    </th>
                    <th className="eyebrow px-2 py-2 font-normal">Event</th>
                    <th className="eyebrow px-2 py-2 font-normal">Actor</th>
                    <th className="eyebrow py-2 pl-2 pr-4 font-normal">Hash</th>
                  </tr>
                </thead>
                <tbody>
                  {events.data?.events.map((e) => (
                    <tr
                      key={e.seq}
                      data-testid={`row-audit-event-${e.seq}`}
                      className="border-b border-border/50 last:border-b-0 hover:bg-background/40"
                    >
                      <td className="num py-2 pl-4 pr-2 text-muted-foreground">
                        #{e.seq}
                      </td>
                      <td
                        className="num whitespace-nowrap px-2 py-2"
                        title={`${formatUtcDateTime(e.occurredAt)} UTC`}
                      >
                        {formatManilaDateTime(e.occurredAt)}
                      </td>
                      <td className="whitespace-nowrap px-2 py-2">
                        <span
                          className={cn(
                            e.eventType === 'auth.signin_refused' &&
                              'text-warn',
                          )}
                          title={e.eventType}
                        >
                          {eventLabel(e.eventType)}
                        </span>
                        {/* The machine name of the event, when there is room for it. */}
                        <span className="num ml-2 hidden text-[11px] text-muted-foreground @[760px]:inline">
                          {e.eventType}
                        </span>
                      </td>
                      <td
                        className="num max-w-[160px] truncate px-2 py-2 text-muted-foreground"
                        title={e.actorId ?? undefined}
                      >
                        {actorLabel(e)}
                      </td>
                      <td
                        className="num py-2 pl-2 pr-4 text-muted-foreground"
                        title={e.hash}
                      >
                        {shortHash(e.hash)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      <section className="panel h-fit">
        <header className="border-b border-border px-4 py-2.5">
          <h2 className="text-[13px] font-medium">Integrity check</h2>
        </header>
        <div className="p-4">
          <p className="text-[12.5px] leading-relaxed text-muted-foreground">
            Recomputes the hash chain over every recorded event and reports the
            first break, if any.
          </p>
          <p className="mt-2 text-[11.5px] leading-relaxed text-muted-foreground">
            Database-only verification cannot detect deletion of the newest
            events or a privileged rewrite of the whole chain.
          </p>
          <button
            type="button"
            data-testid="button-verify-audit"
            onClick={() => verify.mutate()}
            disabled={verify.isPending}
            className="focus-ring mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-md border border-teal/50 bg-teal/10 text-[13px] font-medium text-teal transition-colors hover:bg-teal/15 disabled:opacity-60"
          >
            {verify.isPending ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
            )}
            {verify.isPending ? 'Verifying chain' : 'Verify audit trail'}
          </button>
          {verify.isError && (
            <div className="mt-3">
              <ErrorNote
                error={verify.error}
                title="Verification could not run"
              />
            </div>
          )}
          {verify.data && !verify.isPending && (
            <VerificationResult v={verify.data} />
          )}
        </div>
      </section>
    </div>
  );
}

function LoadingGrid() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" aria-busy>
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="panel p-4">
          <Skeleton className="h-4 w-24 bg-muted" />
          <div className="mt-4 space-y-2.5">
            <Skeleton className="h-3 w-full bg-muted" />
            <Skeleton className="h-3 w-5/6 bg-muted" />
            <Skeleton className="h-3 w-2/3 bg-muted" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function SystemStatusPage() {
  const status = useGetSystemStatus({
    query: { refetchInterval: 30000, queryKey: getGetSystemStatusQueryKey() },
  });
  const s = status.data;

  return (
    <div
      data-testid="page-system-status"
      className="mx-auto max-w-[1440px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Live / Phase 1</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            System Status
          </h1>
        </div>
        <div className="flex items-center gap-3">
          {s && (
            <p className="num text-right text-[11.5px] text-muted-foreground">
              Checked {formatManilaTime(s.checkedAt)} MNL
              <span className="block">
                {formatUtcTime(s.checkedAt)} UTC / every 30 s
              </span>
            </p>
          )}
          <button
            type="button"
            data-testid="button-refresh-status"
            onClick={() => status.refetch()}
            disabled={status.isFetching}
            className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-border bg-card px-3 text-[13px] transition-colors hover:border-teal/60 disabled:opacity-70"
          >
            <RefreshCw
              className={cn(
                'h-3.5 w-3.5 text-teal',
                status.isFetching && 'animate-spin',
              )}
              aria-hidden
            />
            {status.isFetching ? 'Refreshing' : 'Refresh'}
          </button>
        </div>
      </div>

      {status.isError && (
        <div className="mt-5">
          <ErrorNote
            error={status.error}
            title={
              s
                ? 'The latest check failed. Showing the previous result.'
                : 'System status could not be loaded'
            }
            onRetry={() => status.refetch()}
          />
        </div>
      )}

      {status.isLoading && (
        <div className="mt-5">
          <LoadingGrid />
        </div>
      )}

      {s && (
        <div key={status.dataUpdatedAt} className="landed mt-5 space-y-4">
          <section className="panel grid gap-5 p-4 sm:grid-cols-2 lg:grid-cols-[auto_1fr_1fr_1fr] lg:items-center lg:gap-8">
            <div
              data-testid="status-overall"
              data-status={s.overall}
              className="min-w-0"
            >
              <p className="eyebrow">Overall</p>
              <div className="mt-1.5">
                <StatusPill status={s.overall} large />
              </div>
            </div>
            <Clock
              zone="Manila"
              primary={formatManilaTime(s.time.utc)}
              secondary={formatManilaDateTime(s.time.utc)}
            />
            <Clock
              zone="UTC"
              primary={formatUtcTime(s.time.utc)}
              secondary={formatUtcDateTime(s.time.utc)}
            />
            <div className="min-w-0">
              <p className="eyebrow">Build</p>
              <p className="num mt-0.5 truncate text-base font-medium">
                {s.build.version}
              </p>
              <p className="num truncate text-[11.5px] text-muted-foreground">
                {s.build.commit
                  ? s.build.commit.slice(0, 12)
                  : 'commit not available'}{' '}
                / started {formatManilaDateTime(s.build.startedAt)}
              </p>
            </div>
          </section>
          <StatusBody s={s} />
        </div>
      )}

      <div className="mt-4">
        <AuditSection />
      </div>
    </div>
  );
}
