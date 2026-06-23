const MISSING_VALUES = new Set(["", "To be added", "No introduction yet", "未填写", "暂无"]);

export function hasValue(value) {
  return !MISSING_VALUES.has(String(value || "").trim());
}

export function cleanValue(value) {
  const text = String(value || "").trim();
  return hasValue(text) ? text : "";
}

export function joinVisible(values, separator = " · ") {
  return values.map(cleanValue).filter(Boolean).join(separator);
}

export function optionalStat(label, value) {
  const text = cleanValue(value);
  if (!text) return "";
  return `<div class="stat-line"><strong>${label}</strong><span>${text}</span></div>`;
}
