"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export interface DnsRecord {
  id: string;
  fqdn: string;
  record_type: string;
  value?: string | null;
  ttl?: number | null;
  active: boolean;
  publication_id?: string | null;
}

interface Publication {
  id: string;
  domain_or_sni?: string | null;
}

interface PublicationsPage {
  items: Publication[];
}

const RECORD_TYPES = ["A", "AAAA", "CNAME", "TXT", "MX", "NS"];

export function DnsRecordModal({
  record,
  onClose,
  onSaved,
}: {
  record: DnsRecord | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editing = record !== null;
  const [fqdn, setFqdn] = useState(record?.fqdn ?? "");
  const [recordType, setRecordType] = useState(record?.record_type ?? "A");
  const [value, setValue] = useState(record?.value ?? "");
  const [ttl, setTtl] = useState<string>(
    record?.ttl != null ? String(record.ttl) : "3600",
  );
  const [active, setActive] = useState(record?.active ?? true);
  const [publicationId, setPublicationId] = useState(
    record?.publication_id ?? "",
  );
  const [publications, setPublications] = useState<Publication[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<PublicationsPage>("/publications")
      .then((p) => setPublications(p.items))
      .catch(() => setPublications([]));
  }, []);

  async function save() {
    setBusy(true);
    setError(null);
    const body = {
      fqdn: fqdn.trim(),
      record_type: recordType,
      value: value.trim() || null,
      ttl: ttl.trim() ? Number(ttl) : null,
      active,
      publication_id: publicationId || null,
    };
    try {
      if (editing) {
        await api.patch(`/dns/${record!.id}`, body);
      } else {
        await api.post("/dns", body);
      }
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="card flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden p-0">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-lg font-semibold">
            {editing ? "Изменить запись" : "Новая DNS-запись"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost px-2 py-1"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          <div className="space-y-1">
            <label className="block text-sm text-slate-300">
              FQDN <span className="text-red-400">*</span>
            </label>
            <input
              className="input"
              placeholder="app.mishteam.site"
              value={fqdn}
              onChange={(e) => setFqdn(e.target.value)}
            />
          </div>

          <div className="flex gap-3">
            <div className="w-32 space-y-1">
              <label className="block text-sm text-slate-300">Тип</label>
              <select
                className="input"
                value={recordType}
                onChange={(e) => setRecordType(e.target.value)}
              >
                {RECORD_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-28 space-y-1">
              <label className="block text-sm text-slate-300">TTL, сек</label>
              <input
                className="input"
                type="number"
                min={60}
                placeholder="3600"
                value={ttl}
                onChange={(e) => setTtl(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-sm text-slate-300">
              Значение
              <span className="ml-1 text-xs text-slate-500">
                {recordType === "A"
                  ? "(IPv4)"
                  : recordType === "AAAA"
                    ? "(IPv6)"
                    : recordType === "CNAME"
                      ? "(хост)"
                      : ""}
              </span>
            </label>
            <input
              className="input"
              placeholder={
                recordType === "CNAME" ? "app.mishteam.site" : "203.0.113.10"
              }
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-sm text-slate-300">
              Публикация (необязательно)
            </label>
            <select
              className="input"
              value={publicationId}
              onChange={(e) => setPublicationId(e.target.value)}
            >
              <option value="">— не привязана —</option>
              {publications.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.domain_or_sni || p.id}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />
            Активна
          </label>

          {error && <div className="text-sm text-red-400">Ошибка: {error}</div>}
        </div>

        <div className="flex items-center justify-between gap-2 border-t border-border px-5 py-4">
          <button
            type="button"
            className="btn-ghost"
            onClick={onClose}
            disabled={busy}
          >
            Отмена
          </button>
          <button
            type="button"
            className="btn"
            onClick={save}
            disabled={busy || !fqdn.trim()}
          >
            {busy ? "Сохранение…" : "Сохранить"}
          </button>
        </div>
      </div>
    </div>
  );
}
