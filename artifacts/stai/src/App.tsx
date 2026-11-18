import { type ReactNode } from 'react';
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';
import {
  Redirect,
  Route,
  Switch,
  useLocation,
  Router as WouterRouter,
} from 'wouter';
import { useAuth } from '@workspace/replit-auth-web';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AppShell } from '@/components/app-shell';
import NotFound from '@/pages/not-found';
import SystemStatusPage from '@/pages/system-status';
import MarketScannerPage from '@/pages/market-scanner';
import ProposalsPage from '@/pages/proposals';
import PortfolioPage from '@/pages/portfolio';
import AiCommitteePage from '@/pages/ai-committee';
import { NotBuiltPage } from '@/pages/not-built';
import { LoadingScreen, SignInScreen } from '@/pages/sign-in';
import { MODULES, SYSTEM_STATUS_PATH } from '@/lib/modules';
import { sessionExpiredUrl } from '@/lib/signin-notices';
import { getStatus } from '@/lib/api-errors';

let redirecting = false;
function handleAuthError(error: unknown) {
  if (getStatus(error) === 401 && !redirecting) {
    redirecting = true;
    window.location.assign(sessionExpiredUrl(import.meta.env.BASE_URL));
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: handleAuthError }),
  mutationCache: new MutationCache({ onError: handleAuthError }),
  defaultOptions: {
    queries: {
      retry: (count, error) => {
        const s = getStatus(error);
        if (s === 401 || s === 403) return false;
        return count < 2;
      },
      refetchOnWindowFocus: false,
    },
    mutations: { retry: false },
  },
});

function Router() {
  return (
    <RoutedErrorBoundary>
      <Switch>
        <Route path="/">
          <Redirect to={SYSTEM_STATUS_PATH} replace />
        </Route>
        <Route path={SYSTEM_STATUS_PATH} component={SystemStatusPage} />
        <Route path="/market-scanner" component={MarketScannerPage} />
        <Route path="/proposals" component={ProposalsPage} />
        <Route path="/portfolio" component={PortfolioPage} />
        <Route path="/ai-committee" component={AiCommitteePage} />
        {MODULES.map((m) => (
          <Route key={m.id} path={m.path}>
            <NotBuiltPage module={m} />
          </Route>
        ))}
        <Route component={NotFound} />
      </Switch>
    </RoutedErrorBoundary>
  );
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

function Gate() {
  const { user, isLoading, isAuthenticated, login, logout } = useAuth();
  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated || !user) return <SignInScreen onLogin={login} />;
  return (
    <AppShell user={user} onLogout={logout}>
      <Router />
    </AppShell>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
          <Gate />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
