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
