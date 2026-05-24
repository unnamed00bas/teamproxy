"use client";

import { ResourceList } from "@/components/ResourceList";

interface Node {
  id: string;
  hostname: string;
  private_ip?: string | null;
  platform?: string | null;
  is_gateway: boolean;
  status: string;
}

export default function NodesPage() {
  return (
    <ResourceList<Node>
      title="Nodes"
      path="/nodes"
      columns={[
        { key: "hostname", label: "Hostname" },
        { key: "private_ip", label: "Private IP" },
        { key: "platform", label: "Platform" },
        {
          key: "is_gateway",
          label: "Gateway",
          render: (n) => (n.is_gateway ? "yes" : "—"),
        },
        { key: "status", label: "Status", badge: true },
      ]}
    />
  );
}
