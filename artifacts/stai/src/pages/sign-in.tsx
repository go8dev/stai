import { useMemo } from 'react';
import {
  ArrowUpRight,
  Info,
  LogIn,
  ShieldAlert,
  AlertTriangle,
} from 'lucide-react';
import { readSigninNotice, type SigninNotice } from '@/lib/signin-notices';
import { isEmbedded, standaloneUrl } from '@/lib/embedding';
import { cn } from '@/lib/utils';
import { PaperLabel } from '@/components/desk';

const TONE = {
  error: {
    box: 'border-loss/45 bg-loss/[0.07]',
    icon: 'text-loss',
    Icon: ShieldAlert,
  },
  warning: {
    box: 'border-warn/45 bg-warn/[0.07]',
    icon: 'text-warn',
    Icon: AlertTriangle,
  },
  info: { box: 'border-teal/40 bg-teal/[0.06]', icon: 'text-teal', Icon: Info },
} as const;

function Notice({ notice }: { notice: SigninNotice }) {
  const t = TONE[notice.tone];
  return (
    <div
      data-testid="signin-notice"
      data-reason={notice.reason}
      role={notice.tone === 'info' ? 'status' : 'alert'}
      className={cn('rounded-md border p-3.5 text-left', t.box)}
    >
      <div className="flex gap-2.5">
        <t.Icon className={cn('mt-0.5 h-4 w-4 shrink-0', t.icon)} aria-hidden />
        <div className="min-w-0">
          <p className="text-sm font-medium">{notice.title}</p>
          <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
            {notice.body}
          </p>
          {notice.reason === 'refused' && notice.accountId && (
            <div className="mt-2.5 rounded border border-border bg-background/60 px-2.5 py-1.5">
              <p className="eyebrow">Refused account ID</p>
              <p
                data-testid="text-refused-account-id"
                className="num mt-0.5 select-all break-all text-[13px]"
              >
                {notice.accountId}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function SignInScreen({ onLogin }: { onLogin: () => void }) {
  const notice = useMemo(() => readSigninNotice(window.location.search), []);
  const embedded = useMemo(() => isEmbedded(), []);
  const base = import.meta.env.BASE_URL;

  return (
    <div
      data-testid="signin-screen"
      className="desk-grid relative flex min-h-[100dvh] flex-col bg-background"
    >
      <header className="flex items-center justify-between px-5 py-4 sm:px-8">
        <span className="eyebrow">Private research desk</span>
        <PaperLabel />
      </header>

      <div className="flex flex-1 items-center justify-center px-5 py-8">
        <div className="rise w-full max-w-[380px] text-center">
          <div className="mx-auto w-fit bg-background p-2">
            <img
              src={`${base}brand/stai-logo-on-dark-320.webp`}
              srcSet={`${base}brand/stai-logo-on-dark-320.webp 1x, ${base}brand/stai-logo-on-dark-640.webp 2x`}
              width={176}
              height={175}
              alt="STAI, SmartTrader AI"
              className="block h-[176px] w-[176px]"
            />
          </div>

          <p className="mt-6 text-lg font-medium tracking-tight">
            Stay Ahead. Stay in Control.
          </p>
          <p className="mt-1 text-[13px] text-muted-foreground">
            A virtual fund on paper. Every trade waits for your approval.
          </p>

          {notice && (
            <div className="mt-6">
              <Notice notice={notice} />
            </div>
          )}

          <div className="mt-6">
            {embedded ? (
              <>
                <p className="mb-3 text-[13px] text-muted-foreground">
                  Sign-in needs its own browser tab, so open STAI outside this
                  page to log in.
                </p>
                <a
                  data-testid="link-open-new-tab"
                  href={standaloneUrl()}
                  target="_blank"
                  rel="noopener"
                  className="focus-ring inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-primary text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  Open STAI in a new tab
                  <ArrowUpRight className="h-4 w-4" aria-hidden />
                </a>
              </>
            ) : (
              <button
                type="button"
                data-testid="button-login"
                onClick={onLogin}
                className="focus-ring inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-primary text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
              >
                <LogIn className="h-4 w-4" aria-hidden />
                Log in
              </button>
            )}
          </div>

          <p className="mt-5 text-xs text-muted-foreground/80">
            Owner access only. No real money moves.
          </p>
        </div>
      </div>

      <footer className="px-5 py-4 text-center sm:px-8">
        <span className="eyebrow">Intelligence in Every Trade.</span>
      </footer>
    </div>
  );
}

export function LoadingScreen() {
  return (
    <div
      className="flex min-h-[100dvh] flex-col items-center justify-center gap-4 bg-background"
      role="status"
      aria-live="polite"
    >
      <img
        src={`${import.meta.env.BASE_URL}favicon.svg`}
        width={36}
        height={36}
        alt=""
        aria-hidden
        className="opacity-90"
      />
      <div className="h-px w-32 overflow-hidden bg-border">
        <div className="h-full w-1/3 animate-[shimmer_1.4s_ease-in-out_infinite] bg-teal/70" />
      </div>
      <span className="eyebrow">Checking session</span>
      <PaperLabel />
      <style>
        {
          '@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(300%)}}'
        }
      </style>
    </div>
  );
}
