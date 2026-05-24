"use client";

import { useState } from "react";
import { ResourceList } from "@/components/ResourceList";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { Publication } from "@/lib/types";

export default function PublicationsPage() {
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function showPreview() {
    setBusy(true);
    try {
      const cfg = await api.get<string>("/publications/preview");
      setPreview(cfg);
    } catch (e) {
      setPreview(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  async function apply() {
    setBusy(true);
    try {
      await api.post("/publications/apply");
      alert("Конфигурация применена");
    } catch (e) {
      alert(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <ResourceList<Publication>
        title="Публикации"
        path="/publications"
        actions={
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={showPreview} disabled={busy}>
              Предпросмотр
            </button>
            <button className="btn" onClick={apply} disabled={busy}>
              Применить
            </button>
          </div>
        }
        columns={[
          { key: "domain_or_sni", label: "Домен / SNI" },
          { key: "entrypoint_type", label: "Точка входа" },
          { key: "tls_mode", label: "TLS" },
          { key: "priority", label: "Приоритет" },
          {
            key: "maintenance_mode",
            label: "Обслуживание",
            render: (p) =>
              p.maintenance_mode ? <StatusBadge value="degraded" /> : "—",
          },
          {
            key: "public_enabled",
            label: "Публично",
            render: (p) => (
              <StatusBadge value={p.public_enabled ? "online" : "disabled"} />
            ),
          },
        ]}
      />
      {preview !== null && (
        <div className="card">
          <h2 className="mb-2 font-medium">
            Сгенерированная конфигурация Traefik
          </h2>
          <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-slate-300">
            {preview}
          </pre>
        </div>
      )}
    </div>
  );
}
