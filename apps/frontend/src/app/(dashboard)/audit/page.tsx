"use client";

import { ResourceList } from "@/components/ResourceList";
import type { AuditEvent } from "@/lib/types";

export default function AuditPage() {
  return (
    <ResourceList<AuditEvent>
      title="Audit Log"
      path="/audit"
      columns={[
        {
          key: "created_at",
          label: "When",
          render: (e) => new Date(e.created_at).toLocaleString(),
        },
        { key: "actor_email", label: "Actor" },
        { key: "action", label: "Action" },
        { key: "target_type", label: "Target" },
        { key: "result", label: "Result", badge: true },
      ]}
    />
  );
}
