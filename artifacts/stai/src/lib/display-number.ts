/**
 * Display-only formatting of decimal wire values. The server sends decimals as strings;
 * these helpers convert with Number solely to render them. Never use them for accounting.
 */

export type WireDecimal = number | string | null | undefined;

export function toDisplayNumber(value: WireDecimal): number | null {
  if (value === null || value === undefined || value === '') return null;
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Fixed decimals, grouped. */
export function fmtFixed(value: WireDecimal, digits = 2): string | null {
  const n = toDisplayNumber(value);
  if (n === null) return null;
  return n.toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/** Price with precision adapted to magnitude. */
export function fmtPrice(value: WireDecimal): string | null {
  const n = toDisplayNumber(value);
  if (n === null) return null;
  const abs = Math.abs(n);
  const digits = abs >= 1000 ? 2 : abs >= 1 ? 3 : 6;
  return fmtFixed(n, digits);
}

/** Signed percent; the value is already in percent units. */
export function fmtPct(value: WireDecimal, digits = 2): string | null {
  const n = toDisplayNumber(value);
  if (n === null) return null;
  const s = Math.abs(n).toFixed(digits);
  return `${n > 0 ? '+' : n < 0 ? '-' : ''}${s}%`;
}

/** Compact volume like 12.4M. */
export function fmtCompact(value: WireDecimal): string | null {
  const n = toDisplayNumber(value);
  if (n === null) return null;
  return n.toLocaleString('en-US', {
    notation: 'compact',
    maximumFractionDigits: 2,
  });
}

/** Signed money with fixed decimals. */
export function fmtSigned(value: WireDecimal, digits = 2): string | null {
  const n = toDisplayNumber(value);
  if (n === null) return null;
  const body = Math.abs(n).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return `${n > 0 ? '+' : n < 0 ? '-' : ''}${body}`;
}

export function signTone(value: WireDecimal): string {
  const n = toDisplayNumber(value);
  if (n === null || n === 0) return 'text-foreground';
  return n > 0 ? 'text-profit' : 'text-loss';
}

export function fmtAge(seconds: number | null | undefined): string | null {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds))
    return null;
  const s = Math.max(0, seconds);
  if (s < 60) return `${s.toFixed(s < 10 ? 1 : 0)} s`;
  if (s < 3600) return `${Math.floor(s / 60)} m ${Math.floor(s % 60)} s`;
  return `${Math.floor(s / 3600)} h ${Math.floor((s % 3600) / 60)} m`;
}
