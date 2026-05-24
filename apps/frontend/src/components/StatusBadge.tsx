const COLORS: Record<string, string> = {
  online: "bg-green-500/20 text-green-400",
  active: "bg-green-500/20 text-green-400",
  green: "bg-green-500/20 text-green-400",
  ok: "bg-green-500/20 text-green-400",
  degraded: "bg-yellow-500/20 text-yellow-400",
  stale: "bg-yellow-500/20 text-yellow-400",
  yellow: "bg-yellow-500/20 text-yellow-400",
  pending: "bg-yellow-500/20 text-yellow-400",
  offline: "bg-red-500/20 text-red-400",
  red: "bg-red-500/20 text-red-400",
  error: "bg-red-500/20 text-red-400",
  failed: "bg-red-500/20 text-red-400",
  disabled: "bg-slate-500/20 text-slate-400",
  archived: "bg-slate-500/20 text-slate-400",
  unknown: "bg-slate-500/20 text-slate-400",
};

const LABELS: Record<string, string> = {
  online: "онлайн",
  active: "активен",
  green: "норма",
  ok: "ок",
  degraded: "деградация",
  stale: "устарел",
  yellow: "внимание",
  pending: "ожидание",
  offline: "офлайн",
  red: "ошибка",
  error: "ошибка",
  failed: "сбой",
  disabled: "отключён",
  archived: "архив",
  unknown: "неизвестно",
};

export function StatusBadge({ value }: { value: string }) {
  const cls = COLORS[value] || "bg-slate-500/20 text-slate-400";
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>
      {LABELS[value] ?? value}
    </span>
  );
}
