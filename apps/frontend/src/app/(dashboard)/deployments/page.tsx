"use client";

import { ResourceList } from "@/components/ResourceList";

interface Deployment {
  id: string;
  number: number;
  commit_sha?: string | null;
  initiated_by?: string | null;
  mode: string;
  status: string;
  health_result: string;
  rollback_available: boolean;
}

export default function DeploymentsPage() {
  return (
    <ResourceList<Deployment>
      title="Развёртывания"
      path="/deployments"
      columns={[
        { key: "number", label: "№" },
        {
          key: "commit_sha",
          label: "Коммит",
          render: (d) => (d.commit_sha ? d.commit_sha.slice(0, 8) : "—"),
        },
        { key: "initiated_by", label: "Кем" },
        { key: "mode", label: "Режим" },
        { key: "status", label: "Статус", badge: true },
        { key: "health_result", label: "Состояние", badge: true },
      ]}
    />
  );
}
