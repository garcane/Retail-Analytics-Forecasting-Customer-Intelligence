// Loads dashboard/data/*.json (written by src/dashboard/build_data.py). Each file is fetched once and cached.
// A page declares the datasets it needs; optional ones resolve to null when the manifest does not list them.

const cache = new Map();
let manifestPromise = null;

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-cache" });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

export function manifest() {
  if (!manifestPromise) manifestPromise = fetchJson("data/manifest.json");
  return manifestPromise;
}

/**
 * Re-read manifest.json (called on every navigation). If the data was rebuilt since the tab loaded it
 * (generated_at changed), drop every cached dataset so the next page shows the new build, e.g. a risk.json that
 * did not exist when the tab was opened. Returns true when a newer build was found.
 */
export async function refresh() {
  let fresh;
  try {
    fresh = await fetchJson("data/manifest.json");
  } catch {
    return false; // keep serving what is loaded; the page will report its own errors
  }
  const current = manifestPromise ? await manifestPromise.catch(() => null) : null;
  if (current && current.generated_at === fresh.generated_at) return false;
  cache.clear();
  manifestPromise = Promise.resolve(fresh);
  return Boolean(current);
}

export async function dataset(name) {
  if (!cache.has(name)) {
    const m = await manifest();
    const entry = m.datasets[name];
    if (!entry) throw new Error(`dataset "${name}" is not in data/manifest.json; rebuild with src/dashboard/build_data.py`);
    cache.set(name, fetchJson(`data/${entry.file}`));
  }
  return cache.get(name);
}

/** load(["analytics", "kpis"], ["risk"]) -> {analytics, kpis, risk|null} */
export async function load(required = [], optional = []) {
  const m = await manifest();
  const out = {};
  await Promise.all([
    ...required.map(async (name) => { out[name] = await dataset(name); }),
    ...optional.map(async (name) => { out[name] = m.datasets[name] ? await dataset(name) : null; }),
  ]);
  return out;
}
