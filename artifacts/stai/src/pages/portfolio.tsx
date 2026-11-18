import { Fragment, useState } from 'react';
import {
  CheckCircle2,
  Lock,
  RefreshCw,
  ShieldCheck,
  ShieldX,
} from 'lucide-react';
import {
  useGetPortfolioSummary,
  useListPortfolioLedger,
  useVerifyPortfolioLedger,
  getGetPortfolioSummaryQueryKey,
  getListPortfolioLedgerQueryKey,
  getVerifyPortfolioLedgerQueryKey,
  type LedgerVerification,
  type PortfolioSummary,
} from '@workspace/api-client-react';
import {
  formatManilaDateTime,
  formatManilaTime,
  formatUtcDateTime,
} from '@/lib/format';
import { fmtFixed, fmtSigned, signTone } from '@/lib/display-number';
import { cn } from '@/lib/utils';
import { ErrorNote, KV, NotAvailable, PaperLabel } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';

const LEDGER_PARAMS = { limit: 50 };

function Stamp({ value }: { value: string | null }) {
  if (!value) return <NotAvailable />;
  return (
    <span title={`${formatUtcDateTime(value)} UTC`}>
      {formatManilaDateTime(value)}{' '}
      <span className="text-muted-foreground">MNL</span>
    </span>
  );
}

function money(v: number | string, ccy: string) {
  const s = fmtFixed(v, 2);
  return s === null ? (
    <NotAvailable />
  ) : (
    <>
      {s} <span className="text-muted-foreground">{ccy}</span>
    </>
  );
}

function asText(v: unknown): string {
  if (v === null || v === undefined) return '';
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean')
    return String(v);
  try {
    return JSON.stringify(v);
  } catch {
    return '';
  }
}

function DictList({
  items,
  empty,
  testId,
}: {
  items: Record<string, unknown>[];
  empty: string;
  testId: string;
}) {
  if (!Array.isArray(items) || items.length === 0)
    return (
      <p
        className="py-4 text-[12.5px] text-muted-foreground"
        data-testid={`${testId}-empty`}
      >
        {empty}
      </p>
    );
  return (
    <ul className="divide-y divide-border/50" data-testid={testId}>
      {items.map((it, i) => (
        <li key={i} className="py-2">
          <dl>
            {Object.entries(it ?? {}).map(([k, v]) => (
              <KV key={k} label={k}>
                {k.endsWith('At') &&
                typeof v === 'string' &&
                Number.isFinite(Date.parse(v)) ? (
                  <Stamp value={v} />
                ) : (
                  asText(v) || <NotAvailable />
                )}
              </KV>
            ))}
          </dl>
        </li>
      ))}
    </ul>
  );
}

function Summary({ s }: { s: PortfolioSummary }) {
  return (
    <div className="space-y-4">
      <section className="panel grid gap-5 p-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="eyebrow">Paper equity</p>
          <p
            className="num mt-1 text-3xl font-medium tracking-tight"
            data-testid="text-equity"
          >
            {fmtFixed(s.equity, 2) ?? 'n/a'}{' '}
            <span className="text-base text-muted-foreground">
              {s.currency}
            </span>
          </p>
          <p className="num text-[11.5px] text-muted-foreground">
            from {fmtFixed(s.initialBalance, 2)} initial / fund #{s.fundId}
          </p>
        </div>
        <div>
          <p className="eyebrow">Realized P&amp;L</p>
          <p
            className={cn('num mt-1 text-xl', signTone(s.realizedPnl))}
            data-testid="text-realized"
          >
            {fmtSigned(s.realizedPnl) ?? 'n/a'}
          </p>
          <p className="eyebrow mt-2">Unrealized P&amp;L</p>
          <p
            className={cn('num mt-1 text-xl', signTone(s.unrealizedPnl))}
            data-testid="text-unrealized"
          >
            {fmtSigned(s.unrealizedPnl) ?? 'n/a'}
          </p>
        </div>
        <div>
          <dl>
            <KV label="Fees paid" testId="text-fees">
              {money(s.fees, s.currency)}
            </KV>
            <KV label="Funding" testId="text-funding">
              {money(s.funding, s.currency)}
            </KV>
            <KV label="Ledger events">
              {s.ledgerEvents.toLocaleString('en-US')}
            </KV>
            <KV label="Updated">
              <Stamp value={s.updatedAt} />
            </KV>
          </dl>
        </div>
        <div className="flex flex-col justify-between gap-2 rounded-md border border-dashed border-border p-3">
          <div className="flex items-center gap-2">
            {s.ledgerVerified ? (
              <ShieldCheck className="h-4 w-4 text-profit" aria-hidden />
            ) : (
              <ShieldX className="h-4 w-4 text-warn" aria-hidden />
            )}
            <span className="text-[13px]" data-testid="status-ledger-verified">
              {s.ledgerVerified
                ? 'Ledger chain verified'
                : 'Ledger not verified'}
            </span>
          </div>
          <p className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <Lock className="h-3.5 w-3.5" aria-hidden /> Entries disabled
            pending owner approval workflow.
          </p>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        {s.allocations.map((a) => (
          <section
            key={a.marketType}
            className="panel p-4"
            data-testid={`card-allocation-${a.marketType}`}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-[13px] font-medium">
                {a.marketType === 'spot'
                  ? 'Spot allocation'
                  : 'Futures allocation'}
              </h2>
              <span className="eyebrow">{a.marketType}</span>
            </div>
            <p className="num mt-2 text-2xl">
              {fmtFixed(a.balance, 2) ?? 'n/a'}{' '}
              <span className="text-sm text-muted-foreground">
                {s.currency}
              </span>
            </p>
            <p className="num text-[11.5px] text-muted-foreground">
              initial {fmtFixed(a.initialBalance, 2)} {s.currency}
            </p>
            <dl className="mt-3 grid grid-cols-3 gap-3 text-[11.5px]">
              <div>
                <dt className="text-muted-foreground">Available</dt>
                <dd className="num">{fmtFixed(a.availableBalance, 2)}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Collateral</dt>
                <dd className="num">{fmtFixed(a.collateral, 2)}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Exposure</dt>
                <dd className="num">{fmtFixed(a.exposure, 2)}</dd>
              </div>
            </dl>
          </section>
        ))}
        {s.allocations.length === 0 && (
          <p className="panel p-4 text-[12.5px] text-muted-foreground">
            No allocations recorded.
          </p>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="panel px-4 py-3">
          <h2 className="text-[13px] font-medium">Open positions</h2>
          <DictList
            items={s.positions}
            empty="No open paper positions. Nothing has been traded."
            testId="list-positions"
          />
        </section>
        <section className="panel px-4 py-3">
          <h2 className="text-[13px] font-medium">Bots</h2>
          <DictList
            items={s.bots}
            empty="No bots configured. Bots run only after owner approval."
            testId="list-bots"
          />
        </section>
      </div>
    </div>
  );
}

function VerifyResult({ v }: { v: LedgerVerification }) {
  return (
    <div
      role={v.ok ? 'status' : 'alert'}
      data-testid="result-ledger-verification"
      data-ok={v.ok ? 'true' : 'false'}
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
      {v.reason && (
        <p className="mt-2 text-[12.5px]">
          {v.reason}
          {v.firstBreakSeq !== null && ` (at #${v.firstBreakSeq})`}
        </p>
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

function LedgerSection() {
  const ledger = useListPortfolioLedger(LEDGER_PARAMS, {
    query: {
      queryKey: getListPortfolioLedgerQueryKey(LEDGER_PARAMS),
      refetchInterval: 30000,
    },
  });
  const verify = useVerifyPortfolioLedger({
    query: { queryKey: getVerifyPortfolioLedgerQueryKey(), enabled: false },
  });
  const [openSeq, setOpenSeq] = useState<number | null>(null);

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_340px]">
      <section className="panel min-w-0">
        <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-2.5">
          <h2 className="text-[13px] font-medium">Ledger</h2>
          {ledger.data && (
            <span className="num text-[11.5px] text-muted-foreground">
              {ledger.data.events.length} of{' '}
              {ledger.data.total.toLocaleString('en-US')}
            </span>
          )}
        </header>
        {ledger.isLoading ? (
          <div className="space-y-2 p-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-6 w-full bg-muted" />
            ))}
          </div>
        ) : ledger.isError ? (
          <div className="p-4">
            <ErrorNote
              error={ledger.error}
              title="Ledger could not be loaded"
              onRetry={() => ledger.refetch()}
            />
          </div>
        ) : ledger.data && ledger.data.events.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-[13px]">The ledger is empty.</p>
            <p className="mt-1 text-xs text-muted-foreground">
              The funding deposit and every simulated fill will be recorded
              here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[12.5px]">
              <thead>
                <tr className="border-b border-border">
                  <th className="eyebrow py-2 pl-4 pr-2 font-normal">Seq</th>
                  <th className="eyebrow px-2 py-2 font-normal">
                    Time (Manila)
                  </th>
                  <th className="eyebrow px-2 py-2 font-normal">Event</th>
                  <th className="eyebrow px-2 py-2 font-normal">Market</th>
                  <th className="eyebrow px-2 py-2 text-right font-normal">
                    Amount
                  </th>
                  <th className="eyebrow hidden px-2 py-2 font-normal md:table-cell">
                    Reference
                  </th>
                  <th className="eyebrow py-2 pl-2 pr-4 font-normal">Hash</th>
                </tr>
              </thead>
              <tbody>
                {ledger.data?.events.map((e) => {
                  const open = openSeq === e.seq;
                  const details = Object.entries(e.details ?? {});
                  return (
                    <Fragment key={e.seq}>
                      <tr
                        data-testid={`row-ledger-${e.seq}`}
                        onClick={() => setOpenSeq(open ? null : e.seq)}
                        className={cn(
                          'cursor-pointer border-b border-border/50 hover:bg-background/40',
                          open && 'bg-background/40',
                        )}
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
                        <td className="num whitespace-nowrap px-2 py-2">
                          {e.eventType}
                        </td>
                        <td className="px-2 py-2 text-muted-foreground">
                          {e.marketType}
                        </td>
                        <td
                          className={cn(
                            'num whitespace-nowrap px-2 py-2 text-right',
                            signTone(e.amount),
                          )}
                        >
                          {fmtSigned(e.amount) ?? 'n/a'}
                        </td>
                        <td
                          className="num hidden max-w-[180px] truncate px-2 py-2 text-muted-foreground md:table-cell"
                          title={e.reference ?? undefined}
                        >
                          {e.reference ?? '-'}
                        </td>
                        <td
                          className="num py-2 pl-2 pr-4 text-muted-foreground"
                          title={e.hash}
                        >
                          {e.hash.slice(0, 8)}
                        </td>
                      </tr>
                      {open && (
                        <tr
                          key={`${e.seq}-d`}
                          className="border-b border-border/50 bg-background/40"
                        >
                          <td colSpan={7} className="px-4 py-3">
                            <dl className="rise grid gap-x-6 sm:grid-cols-2">
                              <KV label="Full hash">
                                <span className="break-all">{e.hash}</span>
                              </KV>
                              <KV label="Reference">
                                {e.reference ?? <NotAvailable />}
                              </KV>
                              {details.map(([k, v]) => (
                                <KV key={k} label={k}>
                                  {asText(v) || <NotAvailable />}
                                </KV>
                              ))}
                            </dl>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel h-fit">
        <header className="border-b border-border px-4 py-2.5">
          <h2 className="text-[13px] font-medium">Ledger integrity</h2>
        </header>
        <div className="p-4">
          <p className="text-[12.5px] leading-relaxed text-muted-foreground">
            Recomputes the ledger hash chain and reports the first break, if
            any.
          </p>
          <button
            type="button"
            data-testid="button-verify-ledger"
            onClick={() => verify.refetch()}
            disabled={verify.isFetching}
            className="focus-ring mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-md border border-teal/50 bg-teal/10 text-[13px] font-medium text-teal transition-colors hover:bg-teal/15 disabled:opacity-60"
          >
            {verify.isFetching ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
            )}
            {verify.isFetching ? 'Verifying chain' : 'Verify Ledger'}
          </button>
          {verify.isError && (
            <div className="mt-3">
              <ErrorNote
                error={verify.error}
                title="Verification could not run"
              />
            </div>
          )}
          {verify.data && !verify.isFetching && (
            <VerifyResult v={verify.data} />
          )}
          <p
            className="mt-3 rounded border-l-2 border-warn/70 bg-warn/[0.06] px-2.5 py-1.5 text-[11.5px] leading-relaxed"
            data-testid="text-ledger-limitation"
          >
            Database-only check. It detects edits that break the chain, but
            cannot detect a privileged rewrite of the full chain or deletion of
            the newest entries.
          </p>
        </div>
      </section>
    </div>
  );
}

export default function PortfolioPage() {
  const q = useGetPortfolioSummary({
    query: {
      queryKey: getGetPortfolioSummaryQueryKey(),
      refetchInterval: 30000,
    },
  });
  const s = q.data;
  return (
    <div
      data-testid="page-portfolio"
      className="mx-auto max-w-[1440px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Live / Phase 2 / Module 05</p>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-semibold tracking-tight">
            Portfolio <PaperLabel />
          </h1>
          <p className="mt-1 max-w-xl text-[12.5px] text-muted-foreground">
            A virtual fund. No exchange account, no real money. Figures are read
            from the server ledger as recorded.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {s && (
            <p className="num text-right text-[11.5px] text-muted-foreground">
              Updated {formatManilaTime(s.updatedAt)} MNL
              <span className="block">every 30 s</span>
            </p>
          )}
          <button
            type="button"
            data-testid="button-refresh-portfolio"
            onClick={() => q.refetch()}
            disabled={q.isFetching}
            className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-border bg-card px-3 text-[13px] transition-colors hover:border-teal/60 disabled:opacity-70"
          >
            <RefreshCw
              className={cn(
                'h-3.5 w-3.5 text-teal',
                q.isFetching && 'animate-spin',
              )}
              aria-hidden
            />
            {q.isFetching ? 'Refreshing' : 'Refresh'}
          </button>
        </div>
      </div>
      {q.isError && (
        <div className="mt-5">
          <ErrorNote
            error={q.error}
            title={
              s
                ? 'The latest refresh failed. Showing the previous summary.'
                : 'Portfolio could not be loaded'
            }
            onRetry={() => q.refetch()}
          />
        </div>
      )}
      {q.isLoading && (
        <div
          className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4"
          aria-busy
        >
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="panel space-y-2.5 p-4">
              <Skeleton className="h-4 w-24 bg-muted" />
              <Skeleton className="h-7 w-2/3 bg-muted" />
              <Skeleton className="h-3 w-full bg-muted" />
            </div>
          ))}
        </div>
      )}
      {s && (
        <div key={q.dataUpdatedAt} className="landed mt-5">
          <Summary s={s} />
        </div>
      )}
      <div className="mt-4">
        <LedgerSection />
      </div>
    </div>
  );
}
