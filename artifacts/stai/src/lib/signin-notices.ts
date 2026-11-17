/**
 * Messages for the sign-in screen.
 *
 * When a sign-in does not end with a session, the server sends the browser back to the
 * app with `?signin=<reason>` (and `&account=<id>` for a refused account). The app also
 * uses `?signin=expired` when the server answers 401 to a signed-in screen, and the server
 * uses `?signin=signout-failed` when a log out could not be recorded.
 */

export type SigninReason =
  | 'refused'
  | 'failed'
  | 'cancelled'
  | 'cookies'
  | 'not-configured'
  | 'rate-limited'
  | 'unavailable'
  | 'expired'
  | 'signout-failed';

export type SigninNoticeTone = 'error' | 'warning' | 'info';

export interface SigninNotice {
  reason: SigninReason;
  tone: SigninNoticeTone;
  title: string;
  body: string;
  /** ID of the account that was refused. Only set for `refused`. */
  accountId: string | null;
}

const NOTICES: Record<
  SigninReason,
  Omit<SigninNotice, 'reason' | 'accountId'>
> = {
  refused: {
    tone: 'error',
    title: 'This account does not have access',
    body: 'STAI is open to its owner only. The account you signed in with is not the owner account, so no session was created.',
  },
  failed: {
    tone: 'error',
    title: 'Sign-in could not be completed',
    body: 'Something went wrong while signing you in. No session was created. Try again.',
  },
  cancelled: {
    tone: 'info',
    title: 'Sign-in was cancelled',
    body: 'You left before the sign-in was finished. Nothing was changed.',
  },
  cookies: {
    tone: 'warning',
    title: 'Sign-in could not finish in this window',
    body: 'The browser did not send the sign-in cookies back. This happens when STAI is shown inside another page. Open STAI in its own browser tab and log in there.',
  },
  'not-configured': {
    tone: 'error',
    title: 'Sign-in is not set up',
    body: 'The server has no owner account configured, so it refuses every sign-in. Set the owner account ID in the server configuration.',
  },
  'rate-limited': {
    tone: 'warning',
    title: 'Too many sign-in attempts',
    body: 'Wait a minute, then try again.',
  },
  unavailable: {
    tone: 'error',
    title: 'STAI is not ready',
    body: 'The server could not use its database, so no session could be created. Try again shortly. If it keeps happening, check the server logs.',
  },
  expired: {
    tone: 'info',
    title: 'Your session has ended',
    body: 'Log in again to continue.',
  },
  'signout-failed': {
    tone: 'warning',
    title: 'Log out was only partly completed',
    body: 'This browser no longer holds your session, but the server could not remove it from its database. It ends by itself when it expires. If this keeps happening, check the server logs.',
  },
};

// Account IDs are short and plain. Anything else in the URL is not shown.
const ACCOUNT_ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;

function isSigninReason(value: string): value is SigninReason {
  return Object.prototype.hasOwnProperty.call(NOTICES, value);
}

/** Reads the notice from a URL query string such as `window.location.search`. */
export function readSigninNotice(search: string): SigninNotice | null {
  const params = new URLSearchParams(search);
  const reason = params.get('signin');
  if (!reason || !isSigninReason(reason)) {
    return null;
  }

  const account = params.get('account');
  const accountId =
    reason === 'refused' && account && ACCOUNT_ID_PATTERN.test(account)
      ? account
      : null;

  return { reason, accountId, ...NOTICES[reason] };
}

/** Where to send the browser when the server says the session is gone. */
export function sessionExpiredUrl(basePath: string): string {
  const base = basePath.endsWith('/') ? basePath : `${basePath}/`;
  return `${base}?signin=expired`;
}
