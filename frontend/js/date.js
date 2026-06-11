/**
 * date.js — IST-aware logical day utilities.
 */

const IST_TIME_ZONE = "Asia/Kolkata";
const DAY_RESET_HOUR_IST = 4;

function getISTParts(input = new Date()) {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: IST_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });

  const mapped = {};
  for (const part of formatter.formatToParts(input)) {
    if (part.type !== "literal") mapped[part.type] = part.value;
  }

  return {
    year: Number(mapped.year),
    month: Number(mapped.month),
    day: Number(mapped.day),
    hour: Number(mapped.hour),
    minute: Number(mapped.minute),
    second: Number(mapped.second),
  };
}

function toUtcLogicalDate(parts) {
  const utcMs = Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
    parts.hour,
    parts.minute,
    parts.second,
  );
  return new Date(utcMs - DAY_RESET_HOUR_IST * 60 * 60 * 1000);
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function parseDateKey(dateStr) {
  const [year, month, day] = dateStr.split("-").map(Number);
  return { year, month, day };
}

function toUTCDate(dateStr) {
  const { year, month, day } = parseDateKey(dateStr);
  return new Date(Date.UTC(year, month - 1, day));
}

export function getLogicalDateIST(input = new Date()) {
  const logical = toUtcLogicalDate(getISTParts(input));
  return `${logical.getUTCFullYear()}-${pad(logical.getUTCMonth() + 1)}-${pad(logical.getUTCDate())}`;
}

export function getLogicalTodayIST() {
  return getLogicalDateIST(new Date());
}

export function isFutureLogicalDate(dateStr, logicalToday = getLogicalTodayIST()) {
  return dateStr > logicalToday;
}

export function isLogicalTodayIST(dateStr, logicalToday = getLogicalTodayIST()) {
  return dateStr === logicalToday;
}

export function formatMonthLabel(year, month) {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    month: "long",
    year: "numeric",
  }).format(new Date(Date.UTC(year, month - 1, 1)));
}

export function formatNoteDate(dateStr) {
  const date = toUTCDate(dateStr);
  const day = date.getUTCDate();
  const month = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", month: "short" }).format(date);
  return `${day} ${month}`;
}

export function getDayKey(dateStr) {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    weekday: "short",
  }).format(toUTCDate(dateStr));
}

export function getMonthFromDateKey(dateStr) {
  const { year, month } = parseDateKey(dateStr);
  return { year, month };
}
