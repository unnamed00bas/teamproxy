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
      title="Узлы"
      path="/nodes"
      columns={[
        { key: "hostname", label: "Хост" },
        { key: "private_ip", label: "Внутренний IP" },
        { key: "platform", label: "Платформа" },
        {
          key: "is_gateway",
          label: "Шлюз",
          render: (n) => (n.is_gateway ? "да" : "—"),
        },
        { key: "status", label: "Статус", badge: true },
      ]}
    />
  );
}
