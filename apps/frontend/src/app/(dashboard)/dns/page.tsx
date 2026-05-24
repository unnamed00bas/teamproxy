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
        title="DNS Records"
        path="/dns"
        columns={[
          { key: "fqdn", label: "FQDN" },
          { key: "record_type", label: "Type" },
          {
            key: "active",
            label: "Active",
            render: (d) => (d.active ? "yes" : "no"),
          },
        ]}
      />
      <ResourceList<Certificate>
        title="TLS Certificates"
        path="/tls"
        columns={[
          {
            key: "domains",
            label: "Domains",
            render: (c) => c.domains.join(", "),
          },
          { key: "status", label: "Status", badge: true },
          {
            key: "not_after",
            label: "Expires",
            render: (c) =>
              c.not_after ? new Date(c.not_after).toLocaleDateString() : "—",
          },
        ]}
      />
    </div>
  );
}
