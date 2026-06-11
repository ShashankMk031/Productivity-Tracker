/**
 * schedule.js — Reusable task scheduling helpers.
 */

export const DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export const PRESET_OPTIONS = [
  { key: "everyday", label: "Every day", days: DAY_ORDER },
  { key: "weekdays", label: "Weekdays only", days: ["Mon", "Tue", "Wed", "Thu", "Fri"] },
  { key: "weekends", label: "Weekends only", days: ["Sat", "Sun"] },
  { key: "saturday", label: "Only Saturday", days: ["Sat"] },
  { key: "sunday", label: "Only Sunday", days: ["Sun"] },
];

export function normalizeActiveDays(activeDays) {
  if (!Array.isArray(activeDays) || !activeDays.length) {
    return DAY_ORDER.slice();
  }

  const seen = [];
  for (const day of activeDays) {
    if (DAY_ORDER.includes(day) && !seen.includes(day)) {
      seen.push(day);
    }
  }

  return seen.length ? seen : DAY_ORDER.slice();
}

export function sameSchedule(left, right) {
  const a = normalizeActiveDays(left);
  const b = normalizeActiveDays(right);
  return a.length === b.length && a.every((day, index) => day === b[index]);
}

export function getPresetLabel(activeDays) {
  const normalized = normalizeActiveDays(activeDays);
  const preset = PRESET_OPTIONS.find((option) => sameSchedule(option.days, normalized));
  if (preset) return preset.label;
  return `Custom · ${normalized.join(" ")}`;
}
