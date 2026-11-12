// Minimal scales: linear (with clean ticks), time (UTC ms on a linear scale, month-aligned ticks) and band.

/** 1, 2, 2.5, 5 x 10^k step that gives about `count` ticks between min and max. */
export function niceTicks(min, max, count = 5) {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
  if (min === max) {
    const pad = Math.abs(min) || 1;
    min -= pad;
    max += pad;
  }
  const raw = (max - min) / Math.max(1, count);
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || 10 * mag;
  const start = Math.floor(min / step) * step;
  const ticks = [];
  for (let v = start; v <= max + step * 1e-9; v += step) ticks.push(+v.toPrecision(12));
  if (ticks[ticks.length - 1] < max) ticks.push(+(ticks[ticks.length - 1] + step).toPrecision(12));
  return ticks;
}

export function linear([d0, d1], [r0, r1]) {
  const span = d1 - d0 || 1;
  const f = (v) => r0 + ((v - d0) / span) * (r1 - r0);
  f.invert = (px) => d0 + ((px - r0) / (r1 - r0)) * span;
  f.domain = [d0, d1];
  f.range = [r0, r1];
  return f;
}

/** Domain from values, extended to clean tick ends. `zero` forces 0 into the domain (bars, counts). */
export function niceDomain(values, { zero = false, count = 5, min: forcedMin, max: forcedMax } = {}) {
  const finite = values.filter(Number.isFinite);
  let lo = finite.length ? Math.min(...finite) : 0;
  let hi = finite.length ? Math.max(...finite) : 1;
  if (zero) {
    lo = Math.min(0, lo);
    hi = Math.max(0, hi);
  }
  if (forcedMin !== undefined) lo = forcedMin;
  if (forcedMax !== undefined) hi = forcedMax;
  const ticks = niceTicks(lo, hi, count);
  return { domain: [forcedMin ?? ticks[0], forcedMax ?? ticks[ticks.length - 1]], ticks: ticks.filter((t) => t >= (forcedMin ?? -Infinity) && t <= (forcedMax ?? Infinity)) };
}

const DAY = 86400000;

/** Month-aligned UTC ticks: monthly, quarterly or yearly depending on the span and the room available. */
export function timeTicks(min, max, maxTicks = 8) {
  const spanMonths = (max - min) / (30.44 * DAY);
  const step = [1, 2, 3, 6, 12].find((s) => spanMonths / s <= maxTicks) || 12;
  const d = new Date(min);
  let y = d.getUTCFullYear();
  let m = d.getUTCMonth();
  m = Math.ceil(m / step) * step;
  if (d.getUTCDate() > 1 && m === d.getUTCMonth()) m += step;
  const ticks = [];
  for (;;) {
    y += Math.floor(m / 12);
    m %= 12;
    const t = Date.UTC(y, m, 1);
    if (t > max) break;
    if (t >= min) ticks.push(t);
    m += step;
  }
  return ticks;
}

export function band(keys, [r0, r1], { paddingInner = 0.3, paddingOuter = 0.15 } = {}) {
  const n = keys.length || 1;
  const step = (r1 - r0) / (n - paddingInner + 2 * paddingOuter);
  const width = step * (1 - paddingInner);
  const index = new Map(keys.map((k, i) => [k, i]));
  const f = (key) => r0 + step * paddingOuter + step * index.get(key);
  f.bandwidth = width;
  f.step = step;
  return f;
}
