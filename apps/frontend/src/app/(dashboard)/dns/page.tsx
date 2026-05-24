"use client";

import { ResourceList } from "@/components/ResourceList";

interface Domain {
  id: string;
  fqdn: string;
  record_type: string;
  active: boolean;
  publication_id?: string | null;
}

interface Certificate {
  id: string;
  domains: string[];
  status: string;
  not_after?: string | null;
}

export default function DnsPage() {
  return (
    <div className="space-y-8">
      <ResourceList<Domain>
        title="DNS-записи"
        path="/dns"
        columns={[
          { key: "fqdn", label: "FQDN" },
          { key: "record_type", label: "Тип" },
          {
            key: "active",
            label: "Активна",
            render: (d) => (d.active ? "да" : "нет"),
          },
        ]}
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
    </div>
  );
}
