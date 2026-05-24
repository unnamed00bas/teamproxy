"use client";

import { useState } from "react";
import { ResourceList } from "@/components/ResourceList";
import { NodeWizard } from "@/components/NodeWizard";

interface Node {
  id: string;
  hostname: string;
  private_ip?: string | null;
  platform?: string | null;
  is_gateway: boolean;
  status: string;
}

export default function NodesPage() {
  const [wizardOpen, setWizardOpen] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);

  return (
    <>
      <ResourceList<Node>
        title="Узлы"
        path="/nodes"
        refreshToken={refreshToken}
        actions={
          <button className="btn" onClick={() => setWizardOpen(true)}>
            Добавить узел
          </button>
        }
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
      {wizardOpen && (
        <NodeWizard
          onClose={() => setWizardOpen(false)}
          onCreated={() => setRefreshToken((t) => t + 1)}
        />
      )}
    </>
  );
}
