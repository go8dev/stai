import { Link } from 'wouter';
import { Activity } from 'lucide-react';
import {
  CURRENT_PHASE,
  PHASES,
  SYSTEM_STATUS_PATH,
  getPhase,
  type StaiModule,
} from '@/lib/modules';
import { cn } from '@/lib/utils';

export function NotBuiltPage({ module }: { module: StaiModule }) {
  const phase = getPhase(module.phase);
  return (
    <div
      data-testid={`page-not-built-${module.id}`}
      className="rise mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8"
    >
      <p className="eyebrow">
        Module {String(module.number).padStart(2, '0')} / {module.name}
      </p>
      <h1 className="mt-1.5 text-2xl font-semibold tracking-tight sm:text-[28px]">
        {module.title}
      </h1>
      <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
        {module.summary}
      </p>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_300px]">
        <section className="panel">
          <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
            <span className="rounded-[3px] border border-border bg-background px-1.5 py-0.5 font-mono text-[10.5px] uppercase tracking-[0.14em] text-muted-foreground">
              Not built yet
            </span>
            <p data-testid="text-module-phase" className="text-[13px]">
              Delivered in{' '}
              <span className="font-medium text-teal">
                Phase {phase.number}: {phase.name}
              </span>
            </p>
          </div>
          <div className="px-4 py-4">
            <p className="text-[13.5px] text-muted-foreground">
              This screen is not built yet. Nothing here is live, and no values
              are shown until the module exists.
            </p>
            <h2 className="eyebrow mt-5">What it will contain</h2>
            <ul className="mt-2 grid gap-x-6 sm:grid-cols-2">
              {module.willContain.map((item) => (
                <li
                  key={item}
                  className="flex items-center gap-2.5 border-b border-border/60 py-2 text-[13.5px]"
                >
                  <span
                    className="h-1 w-1 shrink-0 rounded-full bg-teal/70"
                    aria-hidden
                  />
                  {item}
                </li>
              ))}
            </ul>
            {module.note && (
              <p className="mt-4 rounded border-l-2 border-warn/70 bg-warn/[0.06] px-3 py-2 text-[13px] text-foreground/90">
                {module.note}
              </p>
            )}
          </div>
        </section>

        <aside className="panel h-fit">
          <h2 className="eyebrow border-b border-border px-4 py-3">
            Build sequence
          </h2>
          <ol className="px-2 py-2">
            {PHASES.map((p) => {
              const current = p.number === CURRENT_PHASE;
              const target = p.number === module.phase;
              return (
                <li
                  key={p.number}
                  className={cn(
                    'flex items-start gap-2.5 rounded px-2 py-1.5',
                    target && 'bg-teal/[0.07]',
                  )}
                >
                  <span
                    className={cn(
                      'num mt-px w-4 text-[11px]',
                      target ? 'text-teal' : 'text-muted-foreground/70',
                    )}
                  >
                    {p.number}
                  </span>
                  <span
                    className={cn(
                      'flex-1 text-[13px]',
                      target ? 'text-foreground' : 'text-muted-foreground',
                    )}
                  >
                    {p.name}
                  </span>
                  {current && (
                    <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-teal">
                      Now
                    </span>
                  )}
                  {target && !current && (
                    <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-foreground/80">
                      This module
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
          <div className="border-t border-border px-4 py-3">
            <Link
              href={SYSTEM_STATUS_PATH}
              className="focus-ring inline-flex items-center gap-1.5 text-[13px] text-teal hover:underline"
            >
              <Activity className="h-3.5 w-3.5" aria-hidden />
              Go to System Status
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
