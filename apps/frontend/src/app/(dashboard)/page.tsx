"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ServiceWizard } from "@/components/ServiceWizard";
import { api } from "@/lib/api";
import type { PublishedService } from "@/lib/types";

function Toggle({
  on,
  busy,
  onChange,
}: {
  on: boolean;
  busy: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      disabled={busy}
      onClick={() => onChange(!on)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors disabled:opacity-50 ${
        on ? "bg-accent" : "bg-surface border border-border"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          on ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

function ServiceCard({
  svc,
  onToggle,
}: {
  svc: PublishedService;
  onToggle: (svc: PublishedService, next: boolean) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);

  async function handleToggle(next: boolean) {
    setBusy(true);
    try {
      await onToggle(svc, next);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium text-slate-100">{svc.name}</div>
          <div className="truncate text-sm text-slate-400">
            {svc.domain ?? "без домена"}
          </div>
        </div>
        <Toggle on={svc.proxy_enabled} busy={busy} onChange={handleToggle} />
      </div>

      <dl className="space-y-1 text-sm">
        <Row label="WG-ключ" value={svc.wg?.name ?? "—"} />
        <Row label="IP туннеля" value={svc.wg?.tunnel_ip ?? "—"} />
        <Row
          label="Бэкенд"
          value={`${svc.protocol_type}://${svc.backend_host}:${svc.backend_port}`}
        />
        {svc.wg?.public_key && (
          <Row label="Публичный ключ" value={svc.wg.public_key} mono truncate />
        )}
      </dl>

      <div className="flex items-center justify-between border-t border-border pt-3">
        <span className={`text-xs ${svc.proxy_enabled ? "text-green-400" : "text-slate-500"}`}>
          {svc.proxy_enabled ? "проксирование включено" : "выключено"}
        </span>
        <Link href={`/service/${svc.id}`} className="btn-ghost px-3 py-1 text-sm">
          Настройки
        </Link>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  mono,
  truncate,
}: {
  label: string;
  value: string;
  mono?: boolean;
  truncate?: boolean;
}) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="shrink-0 text-slate-500">{label}</dt>
      <dd
        className={`text-right text-slate-300 ${mono ? "font-mono text-xs" : ""} ${
          truncate ? "truncate" : ""
        }`}
        title={value}
      >
        {value}
      </dd>
    </div>
  );
}

export default function ServicesPage() {
  const [services, setServices] = useState<PublishedService[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);

  const load = useCallback(() => {
    api
      .get<PublishedService[]>("/published-services")
      .then(setServices)
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleToggle(svc: PublishedService, next: boolean) {
    const updated = await api.post<PublishedService>(
      `/published-services/${svc.id}/toggle?enabled=${next}`,
    );
    setServices((prev) =>
      (prev ?? []).map((s) => (s.id === updated.id ? updated : s)),
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Сервисы</h1>
        <button type="button" className="btn" onClick={() => setWizardOpen(true)}>
          Добавить сервис
        </button>
      </div>

      {error && <div className="text-red-400">Ошибка: {error}</div>}

      {services === null ? (
        <div className="text-slate-400">Загрузка…</div>
      ) : services.length === 0 ? (
        <div className="card text-center text-slate-400">
          Пока нет подключённых сервисов. Нажмите «Добавить сервис».
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {services.map((svc) => (
            <ServiceCard key={svc.id} svc={svc} onToggle={handleToggle} />
          ))}
        </div>
      )}

      {wizardOpen && (
        <ServiceWizard onClose={() => setWizardOpen(false)} onCreated={load} />
      )}
    </div>
  );
}
