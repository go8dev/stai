import { useMemo } from 'react';
import { Clock, RefreshCw } from 'lucide-react';
import {
  useGetCommitteeRun,
  getGetCommitteeRunQueryKey,
  type RoleDefinition,
} from '@workspace/api-client-react';
import { cn } from '@/lib/utils';
import { ErrorNote, KV } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';
import { Cost, Dur, Stamp, Tag, isRunning, statusTone } from './primitives';
import { RoleGrid } from './role-grid';
import { RecommendationPanel } from './recommendation-panel';
import { CallsPanel, EvidencePanel } from './evidence-calls';

export function RunDetail({
  runId,
  roles,
}: {
  runId: string;
  roles: RoleDefinition[];
}) {
  const q = useGetCommitteeRun(runId, {
    query: {
      queryKey: getGetCommitteeRunQueryKey(runId),
      enabled: !!runId,
      refetchInterval: (query) =>
        query.state.data && isRunning(query.state.data.status) ? 5000 : false,
    },
  });
  const d = q.data;
  const known = useMemo(
    () => new Map((d?.evidence ?? []).map((e) => [e.id, e])),
    [d],
  );

  if (q.isLoading)
    return (
      <div className="space-y-3" aria-busy>
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-24 w-full bg-muted" />
        ))}
      </div>
    );
  if (!d)
    return q.isError ? (
      <ErrorNote
        error={q.error}
        title="Run could not be loaded"
        onRetry={() => q.refetch()}
      />
    ) : null;

  const running = isRunning(d.status);
  return (
    <div className="space-y-4" data-testid={`detail-run-${d.id}`}>
      {q.isError && (
        <ErrorNote
          error={q.error}
          title="Refresh failed. Showing previous run detail."
          onRetry={() => q.refetch()}
        />
      )}
      <section className="panel p-4">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-[15px] font-semibold">{d.symbol}</h2>
          <span className="text-[12px] text-muted-foreground">
            {d.marketType}
          </span>
          <Tag tone={statusTone(d.status)} testId="status-run">
            {d.status}
          </Tag>
          {running && (
            <span
              className="inline-flex items-center gap-1 text-[11.5px] text-teal"
              role="status"
            >
              <Clock className="h-3 w-3 animate-pulse" aria-hidden /> In
              progress, polling every 5 s
            </span>
          )}
          <button
            type="button"
            onClick={() => q.refetch()}
            disabled={q.isFetching}
            data-testid="button-refresh-run"
            className="focus-ring ml-auto inline-flex h-7 items-center gap-1.5 rounded border border-border px-2 text-[12px] hover:border-teal/60 disabled:opacity-60"
          >
            <RefreshCw
              className={cn(
                'h-3 w-3 text-teal',
                q.isFetching && 'animate-spin',
              )}
              aria-hidden
            />{' '}
            Refresh run
          </button>
        </div>
        {d.error && (
          <p
            className="mt-2 rounded border-l-2 border-loss/70 bg-loss/[0.07] px-2.5 py-1.5 text-[12px]"
            data-testid="text-run-error"
          >
            {d.error}
          </p>
        )}
        <dl className="mt-3 grid gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
          <KV label="Started">
            <Stamp value={d.startedAt} />
          </KV>
          <KV label="Finished">
            <Stamp value={d.finishedAt} />
          </KV>
          <KV label="Duration">
            <Dur ms={d.durationMs} />
          </KV>
          <KV label="Model">{d.model}</KV>
          <KV label="Tokens in / out">
            {d.inputTokens.toLocaleString('en-US')} /{' '}
            {d.outputTokens.toLocaleString('en-US')}
          </KV>
          <KV label="Cost USD">
            <Cost v={d.costUsd} />
          </KV>
          <KV label="Cost basis">{d.costBasis}</KV>
          <KV label="Snapshot">
            <span title={d.snapshotId}>{d.snapshotId}</span>
          </KV>
          <KV label="Findings">
            {d.findings.length} of {roles.length}
          </KV>
        </dl>
      </section>
      <div className="grid gap-4 2xl:grid-cols-[1.3fr_1fr]">
        <RoleGrid roles={roles} findings={d.findings} known={known} hasRun />
        <RecommendationPanel rec={d.recommendation} d={d} known={known} />
      </div>
      <CallsPanel calls={d.calls} />
      <EvidencePanel items={d.evidence} />
    </div>
  );
}
