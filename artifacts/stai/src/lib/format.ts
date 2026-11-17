/**
 * Time formatting. The server stores and sends UTC; the interface shows Asia/Manila.
 * Use these helpers for every timestamp so the rule holds on every screen.
 */

export const DISPLAY_TIME_ZONE = 'Asia/Manila';
export const DISPLAY_TIME_ZONE_LABEL = 'Manila';

type TimeInput = string | number | Date;

function toDate(value: TimeInput): Date | null {
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatter(timeZone: string, options: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone,
    hourCycle: 'h23',
    ...options,
  });
}

const DATE_TIME: Intl.DateTimeFormatOptions = {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
};

const TIME_ONLY: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
};

const manilaDateTime = formatter(DISPLAY_TIME_ZONE, DATE_TIME);
const manilaTime = formatter(DISPLAY_TIME_ZONE, TIME_ONLY);
const utcDateTime = formatter('UTC', DATE_TIME);
const utcTime = formatter('UTC', TIME_ONLY);

/** For example "17 Nov 2026, 21:05:09", in Manila time. Returns "" for an invalid value. */
export function formatManilaDateTime(value: TimeInput): string {
  const date = toDate(value);
  return date ? manilaDateTime.format(date) : '';
}

/** For example "21:05:09", in Manila time. */
export function formatManilaTime(value: TimeInput): string {
  const date = toDate(value);
  return date ? manilaTime.format(date) : '';
}

/** For example "17 Nov 2026, 13:05:09", in UTC. */
export function formatUtcDateTime(value: TimeInput): string {
  const date = toDate(value);
  return date ? utcDateTime.format(date) : '';
}

/** For example "13:05:09", in UTC. */
export function formatUtcTime(value: TimeInput): string {
  const date = toDate(value);
  return date ? utcTime.format(date) : '';
}
