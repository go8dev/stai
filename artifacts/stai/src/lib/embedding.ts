/**
 * Sign-in needs a browser tab of its own.
 *
 * The session cookie is sent only when STAI is the page in the address bar. When the app
 * is shown inside another page, such as an embedded preview pane, the browser withholds
 * that cookie and a sign-in can never complete there. The sign-in screen uses these
 * helpers to say so and to offer the app in its own tab.
 */

/** True when the app is displayed inside another page. */
export function isEmbedded(): boolean {
  try {
    return window.self !== window.top;
  } catch {
    // Reading window.top across origins throws, which itself means "embedded".
    return true;
  }
}

/** Address of this app for a tab of its own. Use it as the `href` of a link with `target="_blank"`. */
export function standaloneUrl(): string {
  return new URL(import.meta.env.BASE_URL, window.location.origin).toString();
}
