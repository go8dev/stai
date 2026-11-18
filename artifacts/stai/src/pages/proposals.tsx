import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Check,
  Clock3,
  RefreshCw,
  ShieldCheck,
  X,
  type LucideIcon,
} from 'lucide-react';
import {
  getGetMarketScannerQueryKey,
  getGetProposalCenterQueryKey,
  useApproveTradeProposal,
  useGetProposalCenter,
  useRejectTradeProposal,
  type CandidateView,
  type ProposalView,
} from '@workspace/api-client-react';
import { formatManilaDateTime } from '@/lib/format';
import { cn } from '@/lib/utils';
import { ErrorNote, PaperLabel } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';

function display(value: unknown): string | null {
  if (value === null || value === undefined || value === '') return null;
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  )
    return String(value);
  if (Array.isArray(value))
    return value
      .map((item) => display(item))
      .filter(Boolean)
      .join(' · ');
  if (typeof value === 'object') {
    try {
      const encoded = JSON.stringify(value);
      return encoded && encoded !== '{}' ? encoded.slice(0, 1200) : null;
    } catch {
      return null;
    }
  }
  return null;
}

function safeTime(value: string | null | undefined) {
  if (!value) return 'Not available';
  const time = new Date(value);
  return Number.isNaN(time.getTime())
    ? value
    : `${formatManilaDateTime(value)} MNL`;
}

function money(value: number | string | null | undefined, digits = 2) {
  if (value === null || value === undefined || value === '') return '—';
  const n = Number(value);
  return Number.isFinite(n)
    ? n.toLocaleString('en-US', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      })
    : String(value);
}

function DetailValue({ label, value }: { label: string; value: unknown }) {
  const text = display(value);
  if (!text) return null;
  return (
    <div className="border-b border-border/50 py-2 last:border-0">
      <dt className="eyebrow">{label}</dt>
      <dd className="mt-1 whitespace-pre-wrap break-words text-[12.5px] leading-relaxed text-foreground/90">
        {text}
      </dd>
    </div>
  );
}

function CandidateCard({ candidate }: { candidate: CandidateView }) {
  const details = candidate.details ?? {};
  const low = details.entryZoneLow ?? details.entry_zone_low;
  const high = details.entryZoneHigh ?? details.entry_zone_high;
  return (
    <article
      className="panel p-4"
      data-testid={`card-candidate-${candidate.id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{candidate.symbol}</h3>
            <span className="rounded border border-teal/35 bg-teal/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-teal">
              {candidate.marketType}
            </span>
            <span
              className={cn(
                'inline-flex items-center gap-1 text-xs',
                candidate.side === 'long' ? 'text-profit' : 'text-loss',
              )}
            >
              {candidate.side === 'long' ? (
                <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
              ) : (
                <ArrowDownRight className="h-3.5 w-3.5" aria-hidden />
              )}
              {candidate.side}
            </span>
          </div>
          <p className="mt-1 font-mono text-[10.5px] text-muted-foreground">
            Candidate {candidate.id} · {candidate.strategyVersion}
          </p>
        </div>
        <div className="text-right">
          <p
            className="num text-xl font-semibold text-teal"
            data-testid={`text-candidate-score-${candidate.id}`}
          >
            {money(candidate.score, 1)}
          </p>
          <p className="eyebrow">screen score / 100</p>
        </div>
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <p className="text-xs text-muted-foreground">
          <span className="text-foreground/80">Status</span> ·{' '}
          {candidate.status}
        </p>
        <p className="text-xs text-muted-foreground">
          <span className="text-foreground/80">Expires</span> ·{' '}
          {safeTime(candidate.expiresAt)}
        </p>
      </div>
      <dl className="mt-3 grid gap-x-6 sm:grid-cols-2">
        <DetailValue label="Score evidence" value={details.scoreEvidence} />
        <DetailValue
          label="Entry zone"
          value={
            low || high
              ? `${display(low) ?? 'n/a'} – ${display(high) ?? 'n/a'}`
              : null
          }
        />
        <DetailValue
          label="Risk policy"
          value={details.riskPolicy ?? details.risk_policy}
        />
        <DetailValue
          label="Screening notice"
          value={details.screeningNotice ?? details.screening_notice}
        />
      </dl>
      <p className="mt-3 border-t border-border/50 pt-3 text-[11.5px] leading-relaxed text-muted-foreground">
        A deterministic screening candidate is evidence only. It is not an AI
        review, proposal, or trade instruction.
      </p>
    </article>
  );
}

function Term({
  label,
  value,
  testId,
}: {
  label: string;
  value: string;
  testId?: string;
}) {
  return (
    <div className="min-w-0 border-b border-border/50 py-2 last:border-0">
      <dt className="eyebrow">{label}</dt>
      <dd
        className="num mt-1 truncate text-[13px] font-medium"
        data-testid={testId}
      >
        {value}
      </dd>
    </div>
  );
}

function ProposalCard({
  proposal,
  reason,
  onReasonChange,
  onApprove,
  onReject,
  busy,
}: {
  proposal: ProposalView;
  reason: string;
  onReasonChange: (value: string) => void;
  onApprove: () => void;
  onReject: () => void;
  busy: boolean;
}) {
  const pending = proposal.status === 'pending';
  const details = proposal.details ?? {};
  const DirectionIcon: LucideIcon =
    proposal.side === 'long' ? ArrowUpRight : ArrowDownRight;
  return (
    <article
      className="panel overflow-hidden"
      data-testid={`card-proposal-${proposal.id}`}
    >
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border/60 px-4 py-3 sm:px-5">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold tracking-tight">
              {proposal.instrument}
            </h3>
            <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {proposal.marketType}
            </span>
            <span
              className={cn(
                'inline-flex items-center gap-1 text-xs font-medium',
                proposal.side === 'long' ? 'text-profit' : 'text-loss',
              )}
            >
              <DirectionIcon className="h-3.5 w-3.5" aria-hidden />
              {proposal.side}
            </span>
          </div>
          <p className="mt-1 font-mono text-[10.5px] text-muted-foreground">
            Proposal {proposal.id} · Candidate {proposal.candidateId} · Run{' '}
            {proposal.committeeRunId}
          </p>
        </div>
        <span
          className={cn(
            'rounded-[3px] border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.12em]',
            pending
              ? 'border-warn/50 bg-warn/10 text-warn'
              : proposal.status === 'approved'
                ? 'border-profit/40 bg-profit/10 text-profit'
                : 'border-border text-muted-foreground',
          )}
          data-testid={`status-proposal-${proposal.id}`}
        >
          {proposal.status}
        </span>
      </header>
      <div className="grid gap-x-6 px-4 py-3 sm:grid-cols-2 sm:px-5 lg:grid-cols-4">
        <Term
          label="Entry price"
          value={money(proposal.entryPrice, 6)}
          testId={`text-entry-${proposal.id}`}
        />
        <Term
          label="Stop price"
          value={money(proposal.stopPrice, 6)}
          testId={`text-stop-${proposal.id}`}
        />
        <Term
          label="Target price"
          value={money(proposal.targetPrice, 6)}
          testId={`text-target-${proposal.id}`}
        />
        <Term
          label="Notional"
          value={`${money(proposal.notionalUsdt)} USDT`}
          testId={`text-notional-${proposal.id}`}
        />
        <Term label="Leverage" value={`${money(proposal.leverage, 2)}×`} />
        <Term
          label="Planned loss"
          value={`${money(proposal.plannedLossUsdt)} USDT`}
        />
        <Term
          label="Estimated cost"
          value={`${money(proposal.estimatedCostUsdt)} USDT`}
        />
        <Term label="Reward / risk" value={money(proposal.rewardRisk, 2)} />
      </div>
      <div className="grid gap-4 border-t border-border/60 bg-background/30 px-4 py-3 sm:grid-cols-2 sm:px-5">
        <div className="flex gap-2 text-[11.5px] text-muted-foreground">
          <Clock3
            className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal"
            aria-hidden
          />
          <p>
            Created {safeTime(proposal.createdAt)}
            <br />
            Expires {safeTime(proposal.expiresAt)}
          </p>
        </div>
        <dl>
          <DetailValue
            label="Research thesis"
            value={
              details.thesis ??
              details.investmentThesis ??
              details.investment_thesis
            }
          />
          <DetailValue
            label="Committee confidence"
            value={
              details.confidence === null || details.confidence === undefined
                ? null
                : `${display(details.confidence)}/100`
            }
          />
          <DetailValue label="Supporting evidence" value={details.supporting} />
          <DetailValue label="Opposing evidence" value={details.opposing} />
          <DetailValue label="Uncertainties" value={details.uncertainties} />
          <DetailValue
            label="Captured evidence IDs"
            value={details.evidenceIds}
          />
          <DetailValue
            label="Risk assessment"
            value={details.riskAssessment ?? details.risk_assessment}
          />
          <DetailValue
            label="Decision reason"
            value={proposal.decisionReason}
          />
          {proposal.permitId && (
            <DetailValue label="Paper permit" value={proposal.permitId} />
          )}
        </dl>
      </div>
      {pending && (
        <div className="border-t border-border/60 px-4 py-4 sm:px-5">
          <label htmlFor={`reason-${proposal.id}`} className="eyebrow block">
            Owner decision reason
          </label>
          <textarea
            id={`reason-${proposal.id}`}
            data-testid={`input-decision-reason-${proposal.id}`}
            value={reason}
            onChange={(event) => onReasonChange(event.target.value)}
            maxLength={500}
            rows={2}
            className="focus-ring mt-1.5 w-full resize-y rounded border border-input bg-background px-3 py-2 text-[12.5px] leading-relaxed"
            placeholder="Record the basis for this decision"
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <p className="max-w-xl text-[11.5px] leading-relaxed text-muted-foreground">
              Approval creates a paper permit for these exact terms only. The
              entry engine remains fail-closed; no orders are placed.
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                data-testid={`button-reject-${proposal.id}`}
                disabled={busy || !reason.trim()}
                onClick={onReject}
                className="focus-ring inline-flex h-9 items-center gap-1.5 rounded border border-loss/40 px-3 text-xs text-loss transition-colors hover:bg-loss/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
                Reject
              </button>
              <button
                type="button"
                data-testid={`button-approve-${proposal.id}`}
                disabled={busy || !reason.trim()}
                onClick={onApprove}
                className="focus-ring inline-flex h-9 items-center gap-1.5 rounded border border-teal/50 bg-teal/10 px-3 text-xs font-medium text-teal transition-colors hover:bg-teal/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Check className="h-3.5 w-3.5" aria-hidden />
                Approve paper terms
              </button>
            </div>
          </div>
        </div>
      )}
    </article>
  );
}

export default function ProposalsPage() {
  const queryClient = useQueryClient();
  const q = useGetProposalCenter({
    query: { queryKey: getGetProposalCenterQueryKey(), refetchInterval: 30000 },
  });
  const approve = useApproveTradeProposal();
  const reject = useRejectTradeProposal();
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [tab, setTab] = useState<'proposals' | 'candidates'>('proposals');
  const overview = q.data;
  const refreshLinkedData = () => {
    void queryClient.invalidateQueries({
      queryKey: getGetProposalCenterQueryKey(),
    });
    void queryClient.invalidateQueries({
      queryKey: getGetMarketScannerQueryKey(),
    });
  };
  const reasonFor = (proposal: ProposalView) =>
    reasons[proposal.id] ?? 'Reviewed against the exact paper terms.';
  const approveProposal = (proposal: ProposalView) => {
    approve.reset();
    reject.reset();
    approve.mutate(
      { proposalId: proposal.id, data: { reason: reasonFor(proposal).trim() } },
      { onSuccess: refreshLinkedData },
    );
  };
  const rejectProposal = (proposal: ProposalView) => {
    approve.reset();
    reject.reset();
    reject.mutate(
      { proposalId: proposal.id, data: { reason: reasonFor(proposal).trim() } },
      { onSuccess: refreshLinkedData },
    );
  };
  const pendingCount =
    overview?.proposals.filter((p) => p.status === 'pending').length ?? 0;

  return (
    <div
      data-testid="page-proposals"
      className="mx-auto max-w-[1440px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Owner review / Phase 4 / Module 04</p>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-semibold tracking-tight">
            Proposal Center <PaperLabel />
          </h1>
          <p className="mt-1 max-w-2xl text-[12.5px] text-muted-foreground">
            Inspect persisted research proposals and exact risk terms. Screening
            scores are evidence, not trade advice.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {overview && (
            <p className="num text-right text-[11.5px] text-muted-foreground">
              {pendingCount} pending owner decision
              <span className="block">refreshes every 30 s</span>
            </p>
          )}
          <button
            type="button"
            data-testid="button-refresh-proposals"
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

      <section className="mt-5 grid gap-3 lg:grid-cols-[1.4fr_1fr]">
        <div
          className="rounded-md border border-warn/40 bg-warn/[0.07] p-4"
          data-testid="notice-paid-review-gate"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle
              className="mt-0.5 h-4 w-4 shrink-0 text-warn"
              aria-hidden
            />
            <div>
              <p className="text-sm font-semibold">
                Paid committee review is disabled
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                No model call or manual AI run is available. Paid review stays
                gated until a supported model and daily run and spend caps are
                explicitly authorized.
              </p>
            </div>
          </div>
        </div>
        <div
          className="panel flex items-start gap-3 p-4"
          data-testid="notice-paper-only"
        >
          <ShieldCheck
            className="mt-0.5 h-4 w-4 shrink-0 text-teal"
            aria-hidden
          />
          <div>
            <p className="text-sm font-semibold">Approval is not execution</p>
            <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
              Owner approval grants only an exact-term paper permit. The trading
              entry engine remains fail-closed and places no orders.
            </p>
          </div>
        </div>
      </section>

      {overview && (
        <div
          className="mt-4 grid gap-2 sm:grid-cols-3"
          data-testid="proposal-gate-summary"
        >
          <div className="panel px-3 py-2">
            <p className="eyebrow">Gate status</p>
            <p className="mt-1 text-sm font-medium">{overview.gateStatus}</p>
          </div>
          <div className="panel px-3 py-2">
            <p className="eyebrow">Strategy threshold</p>
            <p className="num mt-1 text-sm font-medium">
              {overview.strategyThreshold} / 100
            </p>
          </div>
          <div className="panel px-3 py-2">
            <p className="eyebrow">Committee spend</p>
            <p className="mt-1 text-sm font-medium">
              Disabled · owner approval required
            </p>
          </div>
          {overview.gateMessage && (
            <p
              className="sm:col-span-3 text-[11.5px] leading-relaxed text-muted-foreground"
              data-testid="text-gate-message"
            >
              {overview.gateMessage}
            </p>
          )}
        </div>
      )}

      {q.isError && (
        <div className="mt-5">
          <ErrorNote
            error={q.error}
            title={
              overview
                ? 'The latest refresh failed. Showing persisted previous data.'
                : 'Proposal center could not be loaded'
            }
            onRetry={() => q.refetch()}
          />
        </div>
      )}
      {q.isLoading && (
        <div
          className="mt-5 space-y-3"
          aria-busy="true"
          data-testid="loading-proposals"
        >
          {[0, 1, 2].map((n) => (
            <Skeleton key={n} className="h-36 bg-muted" />
          ))}
        </div>
      )}

      {overview && (
        <>
          {(approve.isSuccess || reject.isSuccess) && (
            <p
              role="status"
              data-testid="status-decision-success"
              className={cn(
                'mt-4 rounded border px-3 py-2 text-xs',
                approve.data?.status === 'vetoed'
                  ? 'border-warn/40 bg-warn/[0.08] text-warn'
                  : 'border-profit/40 bg-profit/[0.08] text-profit',
              )}
            >
              {approve.data?.status === 'vetoed'
                ? 'The safety recheck vetoed these terms. No permit or order was created.'
                : 'Owner decision saved. Proposal and scanner data are refreshing.'}
            </p>
          )}
          {(approve.isError || reject.isError) && (
            <div
              role="alert"
              data-testid="status-decision-error"
              className="mt-4 rounded border border-loss/40 bg-loss/[0.08] px-3 py-2 text-xs text-loss"
            >
              Decision could not be saved. The proposal remains unchanged; retry
              after checking the current server state.
            </div>
          )}
          <div
            className="mt-5 flex gap-1 border-b border-border"
            role="tablist"
            aria-label="Proposal center views"
          >
            {(['proposals', 'candidates'] as const).map((item) => (
              <button
                key={item}
                type="button"
                role="tab"
                aria-selected={tab === item}
                data-testid={`tab-${item}`}
                onClick={() => setTab(item)}
                className={cn(
                  'focus-ring border-b-2 px-3 py-2 text-[12.5px] capitalize transition-colors',
                  tab === item
                    ? 'border-teal text-teal'
                    : 'border-transparent text-muted-foreground hover:text-foreground',
                )}
              >
                {item}{' '}
                <span className="num ml-1 text-[10px]">
                  {item === 'proposals'
                    ? overview.proposals.length
                    : overview.candidates.length}
                </span>
              </button>
            ))}
          </div>
          {tab === 'proposals' ? (
            <section
              className="mt-4 space-y-3"
              aria-label="Persisted proposals"
              data-testid="list-proposals"
            >
              {overview.proposals.length === 0 ? (
                <div
                  className="panel px-5 py-10 text-center"
                  data-testid="empty-proposals"
                >
                  <p className="text-sm font-medium">No persisted proposals</p>
                  <p className="mx-auto mt-1 max-w-lg text-xs leading-relaxed text-muted-foreground">
                    This view contains only proposals returned by the server.
                    Screening candidates do not become proposals automatically,
                    and none are fabricated here.
                  </p>
                </div>
              ) : (
                overview.proposals.map((proposal) => (
                  <ProposalCard
                    key={proposal.id}
                    proposal={proposal}
                    reason={reasonFor(proposal)}
                    onReasonChange={(value) =>
                      setReasons((previous) => ({
                        ...previous,
                        [proposal.id]: value,
                      }))
                    }
                    onApprove={() => approveProposal(proposal)}
                    onReject={() => rejectProposal(proposal)}
                    busy={approve.isPending || reject.isPending}
                  />
                ))
              )}
            </section>
          ) : (
            <section
              className="mt-4 space-y-3"
              aria-label="Qualified candidates"
              data-testid="list-candidates"
            >
              {overview.candidates.length === 0 ? (
                <div
                  className="panel px-5 py-10 text-center"
                  data-testid="empty-candidates"
                >
                  <p className="text-sm font-medium">
                    No qualified candidates in the current record
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Candidate records are supplied by the live screening
                    pipeline; this page never creates sample candidates.
                  </p>
                </div>
              ) : (
                overview.candidates.map((candidate) => (
                  <CandidateCard key={candidate.id} candidate={candidate} />
                ))
              )}
            </section>
          )}
          <p className="mt-4 text-[11px] leading-relaxed text-muted-foreground">
            Only actual pending proposal records can be decided. Decisions are
            recorded against the persisted terms and do not place an order.
          </p>
        </>
      )}
    </div>
  );
}
