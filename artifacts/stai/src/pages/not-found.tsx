import { Link, useLocation } from 'wouter';
import { SYSTEM_STATUS_PATH } from '@/lib/modules';

export default function NotFound() {
  const [location] = useLocation();
  return (
    <div
      data-testid="page-not-found"
      className="rise mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8"
    >
      <p className="eyebrow">Error 404</p>
      <h1 className="mt-1.5 text-2xl font-semibold tracking-tight">
        No screen at this address
      </h1>
      <p className="mt-2 text-[14px] text-muted-foreground">
        STAI has no screen at{' '}
        <span className="num break-all text-foreground">{location}</span>. Use
        the navigation, or go back to the live checks.
      </p>
      <Link
        href={SYSTEM_STATUS_PATH}
        className="focus-ring mt-6 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground hover:opacity-90"
      >
        Go to System Status
      </Link>
    </div>
  );
}
