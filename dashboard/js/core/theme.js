// Light / dark / follow-the-system. Colours live in css/tokens.css; charts re-render on "themechange" so that any
// colour they resolve in JavaScript (heatmap ink) follows the new tokens.

const KEY = "retail-dashboard-theme";
const ORDER = ["auto", "light", "dark"];
const LABEL = { auto: "Theme: system", light: "Theme: light", dark: "Theme: dark" };
const SHORT = { auto: "Auto", light: "Light", dark: "Dark" };

function stored() {
  try {
    return localStorage.getItem(KEY) || "auto";
  } catch {
    return "auto";
  }
}

function apply(mode) {
  const root = document.documentElement;
  if (mode === "auto") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", mode);
  try {
    localStorage.setItem(KEY, mode);
  } catch {
    /* private mode: the choice simply is not remembered */
  }
  window.dispatchEvent(new CustomEvent("themechange", { detail: { mode } }));
}

export function initTheme(button) {
  let mode = ORDER.includes(stored()) ? stored() : "auto";
  apply(mode);
  const sync = () => {
    button.textContent = SHORT[mode];
    button.setAttribute("aria-label", `${LABEL[mode]}. Activate to change.`);
  };
  sync();
  button.addEventListener("click", () => {
    mode = ORDER[(ORDER.indexOf(mode) + 1) % ORDER.length];
    apply(mode);
    sync();
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (mode === "auto") window.dispatchEvent(new CustomEvent("themechange", { detail: { mode } }));
  });
}

/** True when the dark tokens are in effect (chosen, or "auto" on a system in dark mode). */
export function isDark() {
  const chosen = document.documentElement.getAttribute("data-theme");
  if (chosen) return chosen === "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Categorical slot colour by position (1-based), as a CSS value that follows the theme. */
export const series = (slot) => `var(--series-${((slot - 1) % 8) + 1})`;
export const MUTED = "var(--series-muted)";
export const SLOTS = 8;

/**
 * Give each key a fixed categorical slot, in the order given (colour follows the entity, never its rank).
 * `reserved` slots at the start are kept for something else (e.g. "Actual"). Keys beyond the palette get MUTED
 * instead of a wrapped, already-used colour, and a console warning says so (fold them into "Other" or facet).
 */
export function allocateSlots(keys, { reserved = 0 } = {}) {
  const out = {};
  const free = SLOTS - reserved;
  keys.forEach((k, i) => { out[k] = i < free ? series(i + 1 + reserved) : MUTED; });
  if (keys.length > free) console.warn(`allocateSlots: ${keys.length - free} series beyond the ${SLOTS}-colour palette are drawn muted`, keys.slice(free));
  return out;
}
