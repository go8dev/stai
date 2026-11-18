import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import {
  useGetCommitteeOverview,
  getGetCommitteeOverviewQueryKey,
} from '@workspace/api-client-react';
import { formatManilaTime } from '@/lib/format';
import { cn } from '@/lib/utils';
import { ErrorNote, PaperLabel } from '@/components/desk';
import { Skeleton } from '@/components/ui/skeleton';
import { GateBanner, RunList } from '@/components/committee/run-list';
import { RunDetail } from '@/components/committee/run-detail';
import { RoleGrid } from '@/components/committee/role-grid';

export default function AiCommitteePage() {
  const q = useGetCommitteeOverview({
    query: {
      queryKey: getGetCommitteeOverviewQueryKey(),
      refetchInterval: 30000,
    },
  });
  const o = q.data;
  const [picked, setSelected] = useState<string | null>(null);
  const selected =
    o && picked && o.runs.some((r) => r.id === picked)
      ? picked
      : (o?.runs[0]?.id ?? null);

  return (
    <div
      data-testid="page-ai-committee"
      className="mx-auto max-w-[1440px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Live / Phase 3 / Module 02</p>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-semibold tracking-tight">
            AI Committee <PaperLabel />
          </h1>
          <p className="mt-1 max-w-2xl text-[12.5px] text-muted-foreground">
            Ten roles review recorded evidence and produce advisory research.
            Nothing here approves, proposes or places a trade.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {o && (
            <p className="num text-right text-[11.5px] text-muted-foreground">
              Checked{' '}
              {formatManilaTime(new Date(q.dataUpdatedAt).toISOString())} MNL
              <span className="block">every 30 s</span>
            </p>
          )}
          <button
            type="button"
            data-testid="button-refresh-committee"
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
              o
                ? 'The latest refresh failed. Showing previous data.'
                : 'Committee could not be loaded'
            }
            onRetry={() => q.refetch()}
          />
        </div>
      )}
      {q.isLoading && (
        <div className="mt-5 grid gap-4 lg:grid-cols-[300px_1fr]" aria-busy>
          <Skeleton className="h-64 bg-muted" />
          <div className="space-y-2">
            {Array.from({ length: 10 }, (_, i) => (
              <Skeleton key={i} className="h-10 bg-muted" />
            ))}
          </div>
        </div>
      )}
      {o && (
        <div className="mt-5 space-y-4">
          <GateBanner o={o} />
          <div className="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)]">
            <RunList runs={o.runs} selected={selected} onSelect={setSelected} />
            {selected ? (
              <RunDetail key={selected} runId={selected} roles={o.roles} />
            ) : (
              <RoleGrid
                roles={o.roles}
                findings={null}
                known={new Map()}
                hasRun={false}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
