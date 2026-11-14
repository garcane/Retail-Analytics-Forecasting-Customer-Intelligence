// Display names for model, feature-set and forecast-method keys found in the data files.
// Unknown keys still render (humanised), so a new model or method appears without touching this file;
// add an entry here only to give it a nicer name or a description.

export function humanize(key) {
  const s = String(key).replace(/[_|]+/g, " ").replace(/\s+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const FAMILIES = {
  logistic_regression: "Logistic regression",
  gradient_boosting: "Gradient boosting",
};

const BASELINES = {
  constant_train_rate: { label: "Constant (training late rate)", description: "Predicts the training late rate for every order" },
  seller_history_rate: { label: "Seller's past late rate", description: "Each seller's point-in-time late rate" },
};

export const FEATURE_SETS = {
  v1: "Basket, promise, route, payment and calendar features (the reference model)",
  v2: "v1 + route and category late-rate history",
  v3: "v2 + system-wide late rate over the trailing 28 days",
  v4: "v3 expressed relative to the system rate",
  v5: "v1 + delivery-time slack (promise vs typical route time)",
};

/** {key, label, family, featureSet, baseline} for a late-delivery model key such as "gradient_boosting_v2". */
export function modelInfo(key) {
  if (BASELINES[key]) return { key, label: BASELINES[key].label, family: "Baseline", featureSet: null, baseline: true };
  const m = /^(.*)_(v\d+)$/.exec(key);
  if (m) {
    const family = FAMILIES[m[1]] || humanize(m[1]);
    return { key, label: `${family} ${m[2]}`, family, featureSet: m[2], baseline: false };
  }
  return { key, label: humanize(key), family: humanize(key), featureSet: null, baseline: false };
}

export const modelLabel = (key) => modelInfo(key).label;

const METHODS = {
  actual: "Actual",
  naive_last_week: "Naive (last week)",
  moving_average_4: "4-week average",
  moving_average_8: "8-week average",
  linear_trend_12: "12-week linear trend",
  simple_exp_smoothing: "Exponential smoothing",
  damped_trend: "Damped trend (Holt)",
  ar1_trend_26w: "AR(1) + trend, 26 weeks",
  combo_naive_ma8: "Blend: naive + 8-week average",
};

export const methodLabel = (key) => METHODS[key] || humanize(key);

export const METRICS = {
  pr_auc: { label: "PR-AUC", higherIsBetter: true, description: "Area under the precision-recall curve; the base rate is the no-skill level" },
  roc_auc: { label: "ROC-AUC", higherIsBetter: true, description: "Probability a late order is ranked above an on-time one; 0.5 is chance" },
  precision_at_top: { label: "Precision, top 10%", higherIsBetter: true, description: "Share of flagged orders (riskiest 10%) that were late" },
  recall_at_top: { label: "Recall, top 10%", higherIsBetter: true, description: "Share of all late orders caught in the riskiest 10%" },
  brier: { label: "Brier score", higherIsBetter: false, description: "Mean squared error of the predicted probability; lower is better" },
};
