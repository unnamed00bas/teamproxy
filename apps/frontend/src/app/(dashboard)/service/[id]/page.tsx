"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ProtocolType, PublishedService } from "@/lib/types";

const PROTOCOLS: ProtocolType[] = ["http", "https", "tcp", "udp"];

export default function ServiceSettingsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const [svc, setSvc] = useState<PublishedService | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [protocol, setProtocol] = useState<ProtocolType>("http");
  const [backendHost, setBackendHost] = useState("");
  const [backendPort, setBackendPort] = useState("");
  const [tls, setTls] = useState(true);

  useEffect(() => {
    api
      .get<PublishedService>(`/published-services/${id}`)
      .then((s) => {
        setSvc(s);
        setName(s.name);
        setDomain(s.domain ?? "");
        setProtocol(s.protocol_type);
        setBackendHost(s.backend_host);
        setBackendPort(String(s.backend_port));
        setTls(s.tls_enabled);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  async function save() {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await api.patch<PublishedService>(`/published-services/${id}`, {
        name: name.trim(),
        domain: domain.trim() || null,
        protocol_type: protocol,
        backend_host: backendHost.trim(),
        backend_port: Number(backendPort),
        tls_enabled: tls,
      });
      setSvc(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!confirm("Удалить этот сервис? Туннель в wg-easy останется.")) return;
    setSaving(true);
    try {
      await api.del(`/published-services/${id}`);
      router.push("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось удалить");
      setSaving(false);
    }
  }

  if (error && !svc) return <div className="text-red-400">Ошибка: {error}</div>;
  if (!svc) return <div className="text-slate-400">Загрузка…</div>;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="flex items-center gap-3">
        <button type="button" className="btn-ghost px-2 py-1" onClick={() => router.push("/")}>
          ←
        </button>
        <h1 className="text-xl font-semibold">Настройки сервиса</h1>
      </div>

      <div className="card space-y-4">
        <Field label="Название">
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label="Домен (DNS-адрес)">
          <input
            className="input"
            placeholder="grafana.example.com"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
          />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Протокол">
            <select
              className="input"
              value={protocol}
              onChange={(e) => setProtocol(e.target.value as ProtocolType)}
            >
              {PROTOCOLS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Порт">
            <input
              className="input"
              inputMode="numeric"
              value={backendPort}
              onChange={(e) => setBackendPort(e.target.value)}
            />
          </Field>
        </div>
        <Field label="Адрес сервиса (хост)">
          <input
            className="input"
            value={backendHost}
            onChange={(e) => setBackendHost(e.target.value)}
          />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            className="h-4 w-4 accent-accent"
            checked={tls}
            onChange={(e) => setTls(e.target.checked)}
          />
          Выпустить TLS-сертификат (Let&apos;s Encrypt)
        </label>
      </div>

      <div className="card space-y-1 text-sm">
        <h2 className="mb-2 font-medium">WireGuard</h2>
        <Row label="Конфиг" value={svc.wg?.name ?? "—"} />
        <Row label="IP туннеля" value={svc.wg?.tunnel_ip ?? "—"} />
        <Row label="Публичный ключ" value={svc.wg?.public_key ?? "—"} mono />
        <p className="pt-2 text-xs text-slate-500">
          Управление туннелями — в панели wg-easy (пункт меню «WG-панель»).
        </p>
      </div>

      {error && <div className="text-sm text-red-400">Ошибка: {error}</div>}

      <div className="flex items-center justify-between">
        <button type="button" className="btn-ghost text-red-400" onClick={remove} disabled={saving}>
          Удалить
        </button>
        <button type="button" className="btn" onClick={save} disabled={saving}>
          {saving ? "Сохранение…" : saved ? "Сохранено" : "Сохранить"}
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="block text-sm text-slate-300">{label}</label>
      {children}
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-3">
      <span className="shrink-0 text-slate-500">{label}</span>
      <span className={`truncate text-right text-slate-300 ${mono ? "font-mono text-xs" : ""}`} title={value}>
        {value}
      </span>
    </div>
  );
}
