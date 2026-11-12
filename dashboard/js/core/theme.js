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

/** Categorical slot colour by position (1-based), as a CSS value that follows the theme. */
export const series = (slot) => `var(--series-${((slot - 1) % 8) + 1})`;
export const MUTED = "var(--series-muted)";
