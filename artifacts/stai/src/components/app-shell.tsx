import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'wouter';
import { Activity, LogOut, Menu, X } from 'lucide-react';
import type { AuthUser } from '@workspace/replit-auth-web';
import {
  MODULES,
  SYSTEM_STATUS_PATH,
  CURRENT_PHASE,
  getPhase,
} from '@/lib/modules';
import { cn } from '@/lib/utils';
import { BrandMark, PaperLabel } from '@/components/desk';

function displayName(user: AuthUser): string {
  const full = [user.firstName, user.lastName].filter(Boolean).join(' ');
  return full || user.username || user.id;
}

function initials(user: AuthUser): string {
  const n = displayName(user);
  const parts = n.split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || 'S';
}

function NavItem({
  href,
  testId,
  active,
  children,
  onNavigate,
}: {
  href: string;
  testId: string;
  active: boolean;
  children: ReactNode;
  onNavigate: () => void;
}) {
  return (
    <Link
      href={href}
      data-testid={testId}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'focus-ring group relative flex items-center gap-2.5 rounded-[4px] px-2.5 py-[7px] text-[13px] transition-colors',
        active
          ? 'bg-card text-foreground'
          : 'text-muted-foreground hover:bg-card/60 hover:text-foreground',
      )}
    >
      <span
        aria-hidden
        className={cn(
          'absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-full',
          active ? 'bg-teal' : 'bg-transparent',
        )}
      />
      {children}
    </Link>
  );
}

export function AppShell({
  user,
  onLogout,
  children,
}: {
  user: AuthUser;
  onLogout: () => void;
  children: ReactNode;
}) {
  const [location] = useLocation();
  // The phone navigation remembers the page it was opened on, so it closes by itself as
  // soon as the page changes, including with the browser's back button.
  const [openedOn, setOpenedOn] = useState<string | null>(null);
  const open = openedOn === location;
  const phase = getPhase(CURRENT_PHASE);

  const close = () => setOpenedOn(null);

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center gap-2.5 border-b border-sidebar-border px-4">
        <BrandMark size={24} />
        <span className="text-[15px] font-semibold tracking-[0.2em]">STAI</span>
        <PaperLabel className="ml-auto" />
      </div>

      <nav aria-label="Main" className="flex-1 overflow-y-auto px-2.5 py-4">
        <p className="eyebrow px-2.5 pb-2">Live</p>
        <NavItem
          href={SYSTEM_STATUS_PATH}
          testId="nav-system-status"
          active={location === SYSTEM_STATUS_PATH}
          onNavigate={close}
        >
          <Activity className="h-3.5 w-3.5 text-teal" aria-hidden />
          <span className="flex-1">System Status</span>
          <span className="h-1.5 w-1.5 rounded-full bg-teal" aria-hidden />
        </NavItem>

        <p className="eyebrow mt-5 px-2.5 pb-2">Modules</p>
        <ul className="space-y-px">
          {MODULES.map((m) => (
            <li key={m.id}>
              <NavItem
                href={m.path}
                testId={`nav-${m.id}`}
                active={location === m.path}
                onNavigate={close}
              >
                <span className="num w-5 text-[11px] text-muted-foreground/70">
                  {String(m.number).padStart(2, '0')}
                </span>
                <span className="flex-1 truncate">{m.name}</span>
                <span
                  className="num text-[10px] text-muted-foreground/60"
                  title={`Delivered in Phase ${m.phase}`}
                >
                  P{m.phase}
                </span>
              </NavItem>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <p className="eyebrow px-1 pb-2">
          Phase {phase.number} / {phase.name}
        </p>
        <div className="flex items-center gap-2.5 rounded-[4px] px-1 py-1">
          <span className="grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded-[4px] border border-border bg-card text-[11px] font-semibold text-teal">
            {user.profileImageUrl ? (
              <img
                src={user.profileImageUrl}
                alt=""
                className="h-full w-full object-cover"
              />
            ) : (
              initials(user)
            )}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-[10.5px] text-muted-foreground">Signed in as</p>
            <p
              data-testid="text-current-user"
              className="truncate text-[13px] font-medium"
            >
              {displayName(user)}
            </p>
          </div>
          <button
            type="button"
            data-testid="button-logout"
            onClick={onLogout}
            className="focus-ring inline-flex items-center gap-1.5 rounded-[4px] border border-border px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:border-loss/50 hover:text-foreground"
          >
            <LogOut className="h-3.5 w-3.5" aria-hidden />
            Log out
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div data-testid="app-shell" className="min-h-[100dvh] bg-background">
      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex h-12 items-center gap-2.5 border-b border-border bg-background/95 px-3 backdrop-blur lg:hidden">
        <button
          type="button"
          aria-label={open ? 'Close navigation' : 'Open navigation'}
          aria-expanded={open}
          onClick={() => setOpenedOn(open ? null : location)}
          className="focus-ring -ml-1 grid h-9 w-9 place-items-center rounded text-muted-foreground hover:text-foreground"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
        <BrandMark size={20} />
        <span className="text-sm font-semibold tracking-[0.2em]">STAI</span>
        <PaperLabel className="ml-auto" />
      </header>

      {open && (
        <div
          className="fixed inset-0 z-40 bg-background/70 lg:hidden"
          onClick={close}
          aria-hidden
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-[272px] border-r border-sidebar-border bg-sidebar transition-transform duration-200 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {sidebar}
      </aside>

      <main className="lg:pl-[272px]">{children}</main>
    </div>
  );
}
