"use client";

import { useState } from "react";
import { ResourceList } from "@/components/ResourceList";
import { DnsRecordModal, type DnsRecord } from "@/components/DnsRecordModal";
import { api } from "@/lib/api";

interface Certificate {
  id: string;
  domains: string[];
  status: string;
  not_after?: string | null;
}

export default function DnsPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DnsRecord | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  const refresh = () => setRefreshToken((t) => t + 1);

  function openNew() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(record: DnsRecord) {
    setEditing(record);
    setModalOpen(true);
  }

  async function remove(record: DnsRecord) {
    if (!confirm(`Удалить запись ${record.fqdn}?`)) return;
    await api.del(`/dns/${record.id}`);
    refresh();
  }

  return (
    <div className="space-y-8">
      <ResourceList<DnsRecord>
        title="DNS-записи"
        path="/dns"
        refreshToken={refreshToken}
        actions={
          <button className="btn" onClick={openNew}>
            Добавить запись
          </button>
        }
        columns={[
          { key: "fqdn", label: "FQDN" },
          { key: "record_type", label: "Тип" },
          { key: "value", label: "Значение" },
          {
            key: "ttl",
            label: "TTL",
            render: (d) => (d.ttl != null ? String(d.ttl) : "—"),
          },
          {
            key: "active",
            label: "Активна",
            render: (d) => (d.active ? "да" : "нет"),
          },
        ]}
        rowActions={(d) => (
          <span className="flex justify-end gap-2">
            <button
              className="btn-ghost px-2 py-1 text-xs"
              onClick={() => openEdit(d)}
            >
              Изменить
            </button>
            <button
              className="btn-ghost px-2 py-1 text-xs text-red-400"
              onClick={() => remove(d)}
            >
              Удалить
            </button>
          </span>
        )}
      />
      <ResourceList<Certificate>
        title="TLS-сертификаты"
        path="/tls"
        columns={[
          {
            key: "domains",
            label: "Домены",
            render: (c) => c.domains.join(", "),
          },
          { key: "status", label: "Статус", badge: true },
          {
            key: "not_after",
            label: "Истекает",
            render: (c) =>
              c.not_after ? new Date(c.not_after).toLocaleDateString() : "—",
          },
        ]}
      />
      {modalOpen && (
        <DnsRecordModal
          record={editing}
          onClose={() => setModalOpen(false)}
          onSaved={refresh}
        />
      )}
    </div>
  );
}
