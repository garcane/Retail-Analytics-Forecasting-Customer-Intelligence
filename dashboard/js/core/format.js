// Number, currency, percentage and date formatting. One place, so every view shows the same figure the same way.

const cache = new Map();
function nf(options) {
  const key = JSON.stringify(options);
  if (!cache.has(key)) cache.set(key, new Intl.NumberFormat("en-GB", options));
  return cache.get(key);
}

const isNum = (v) => typeof v === "number" && Number.isFinite(v);
export const DASH = "–";

export function int(v) {
  return isNum(v) ? nf({ maximumFractionDigits: 0 }).format(v) : DASH;
}

export function num(v, digits = 2) {
  return isNum(v) ? nf({ minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v) : DASH;
}

/** Compact: 1,284 / 12.9K / 4.2M. Values under 10,000 stay in full. */
export function compact(v, digits = 1) {
  if (!isNum(v)) return DASH;
  if (Math.abs(v) < 10000) return nf({ maximumFractionDigits: Math.abs(v) < 10 ? 2 : 0 }).format(v);
  return nf({ notation: "compact", maximumFractionDigits: digits }).format(v);
}

/** Brazilian reais, the dataset's currency. */
export function brl(v, { compact: short = false, digits = 2 } = {}) {
  if (!isNum(v)) return DASH;
  return `R$ ${short ? compact(v) : nf({ minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v)}`;
}

/** pct(0.081) -> "8.1%" when fraction; pct(8.1, 1, {fraction: false}) -> "8.1%" */
export function pct(v, digits = 1, { fraction = true } = {}) {
  if (!isNum(v)) return DASH;
  return `${nf({ minimumFractionDigits: digits, maximumFractionDigits: digits }).format(fraction ? v * 100 : v)}%`;
}

export function signed(v, digits = 1, suffix = "") {
  if (!isNum(v)) return DASH;
  const s = nf({ minimumFractionDigits: digits, maximumFractionDigits: digits, signDisplay: "exceptZero" }).format(v);
  return s + suffix;
}

export function ratio(v, digits = 2) {
  return isNum(v) ? `${num(v, digits)}×` : DASH;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Parse "YYYY-MM", "YYYY-MM-DD" or ISO timestamps as UTC milliseconds. */
export function toTime(value) {
  if (value instanceof Date) return value.getTime();
  if (typeof value === "number") return value;
  const s = String(value);
  if (/^\d{4}-\d{2}$/.test(s)) return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, 1);
  return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
}

export function month(value) {
  const d = new Date(toTime(value));
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

export function day(value) {
  const d = new Date(toTime(value));
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

export function monthShort(value) {
  const d = new Date(toTime(value));
  return `${MONTHS[d.getUTCMonth()]} ${String(d.getUTCFullYear()).slice(2)}`;
}
