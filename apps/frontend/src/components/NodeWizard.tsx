"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Site } from "@/lib/types";

const STEPS = ["Сайт", "Параметры", "Роль", "Проверка"];

const PLATFORMS = ["linux", "docker", "kubernetes", "windows", "bsd"];

interface NodePage {
  items: Site[];
  total: number;
}

interface Form {
  site_id: string;
  hostname: string;
  private_ip: string;
  platform: string;
  is_gateway: boolean;
  notes: string;
}

const EMPTY: Form = {
  site_id: "",
  hostname: "",
  private_ip: "",
  platform: "",
  is_gateway: false,
  notes: "",
};

export function NodeWizard({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Form>(EMPTY);
  const [sites, setSites] = useState<Site[]>([]);
  const [sitesLoading, setSitesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get<NodePage>("/sites")
      .then((page) => setSites(page.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка"))
      .finally(() => setSitesLoading(false));
  }, []);

  function set<K extends keyof Form>(key: K, value: Form[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function canAdvance(): boolean {
    if (step === 0) return !!form.site_id;
    if (step === 1) return form.hostname.trim().length > 0;
    return true;
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/nodes", {
        site_id: form.site_id,
        hostname: form.hostname.trim(),
        private_ip: form.private_ip.trim() || null,
        platform: form.platform.trim() || null,
        is_gateway: form.is_gateway,
        notes: form.notes.trim() || null,
      });
      onCreated();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать узел");
    } finally {
      setSubmitting(false);
    }
  }

  const selectedSite = sites.find((s) => s.id === form.site_id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="card flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden p-0">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-lg font-semibold">Новый узел</h2>
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost px-2 py-1"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>

        <div className="flex gap-1 border-b border-border px-5 py-3 text-xs">
          {STEPS.map((label, i) => (
            <div key={label} className="flex flex-1 items-center gap-2">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-medium ${
                  i === step
                    ? "bg-accent text-white"
                    : i < step
                      ? "bg-accent/30 text-accent"
                      : "bg-surface text-slate-400"
                }`}
              >
                {i + 1}
              </span>
              <span
                className={`hidden truncate sm:inline ${
                  i === step ? "text-slate-200" : "text-slate-500"
                }`}
              >
                {label}
              </span>
            </div>
          ))}
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          {step === 0 && (
            <div className="space-y-3">
              <label className="block text-sm text-slate-300">
                Выберите сайт, к которому относится узел
              </label>
              {sitesLoading ? (
                <div className="text-sm text-slate-400">Загрузка…</div>
              ) : sites.length === 0 ? (
                <div className="text-sm text-yellow-400">
                  Нет доступных сайтов. Сначала создайте сайт.
                </div>
              ) : (
                <select
                  className="input"
                  value={form.site_id}
                  onChange={(e) => set("site_id", e.target.value)}
                >
                  <option value="">— не выбрано —</option>
                  {sites.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.slug})
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="block text-sm text-slate-300">
                  Имя хоста <span className="text-red-400">*</span>
                </label>
                <input
                  className="input"
                  placeholder="node-01.example.local"
                  value={form.hostname}
                  onChange={(e) => set("hostname", e.target.value)}
                  autoFocus
                />
              </div>
              <div className="space-y-1">
                <label className="block text-sm text-slate-300">
                  Внутренний IP
                </label>
                <input
                  className="input"
                  placeholder="10.0.0.12"
                  value={form.private_ip}
                  onChange={(e) => set("private_ip", e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="block text-sm text-slate-300">Платформа</label>
                <input
                  className="input"
                  list="node-platforms"
                  placeholder="linux"
                  value={form.platform}
                  onChange={(e) => set("platform", e.target.value)}
                />
                <datalist id="node-platforms">
                  {PLATFORMS.map((p) => (
                    <option key={p} value={p} />
                  ))}
                </datalist>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 accent-accent"
                  checked={form.is_gateway}
                  onChange={(e) => set("is_gateway", e.target.checked)}
                />
                <span className="text-sm">
                  <span className="text-slate-200">Шлюз сайта</span>
                  <span className="block text-xs text-slate-500">
                    Узел маршрутизирует трафик для других узлов сайта
                  </span>
                </span>
              </label>
              <div className="space-y-1">
                <label className="block text-sm text-slate-300">Заметки</label>
                <textarea
                  className="input min-h-20 resize-y"
                  placeholder="Назначение, расположение, ответственный…"
                  value={form.notes}
                  onChange={(e) => set("notes", e.target.value)}
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <dl className="space-y-2 text-sm">
              <Row label="Сайт" value={selectedSite ? `${selectedSite.name} (${selectedSite.slug})` : "—"} />
              <Row label="Имя хоста" value={form.hostname.trim() || "—"} />
              <Row label="Внутренний IP" value={form.private_ip.trim() || "—"} />
              <Row label="Платформа" value={form.platform.trim() || "—"} />
              <Row label="Шлюз" value={form.is_gateway ? "да" : "нет"} />
              <Row label="Заметки" value={form.notes.trim() || "—"} />
            </dl>
          )}

          {error && <div className="text-sm text-red-400">Ошибка: {error}</div>}
        </div>

        <div className="flex items-center justify-between gap-2 border-t border-border px-5 py-4">
          <button
            type="button"
            className="btn-ghost"
            onClick={() => (step === 0 ? onClose() : setStep((s) => s - 1))}
            disabled={submitting}
          >
            {step === 0 ? "Отмена" : "Назад"}
          </button>
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              className="btn"
              onClick={() => setStep((s) => s + 1)}
              disabled={!canAdvance()}
            >
              Далее
            </button>
          ) : (
            <button
              type="button"
              className="btn"
              onClick={submit}
              disabled={submitting || !form.hostname.trim() || !form.site_id}
            >
              {submitting ? "Создание…" : "Создать узел"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border/50 pb-1">
      <dt className="text-slate-400">{label}</dt>
      <dd className="text-right text-slate-200">{value}</dd>
    </div>
  );
}
