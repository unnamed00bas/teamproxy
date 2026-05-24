"use client";

import { ResourceList } from "@/components/ResourceList";
import type { AuditEvent } from "@/lib/types";

export default function AuditPage() {
  return (
    <ResourceList<AuditEvent>
      title="Журнал аудита"
      path="/audit"
      columns={[
        {
          key: "created_at",
          label: "Время",
          render: (e) => new Date(e.created_at).toLocaleString(),
        },
        { key: "actor_email", label: "Пользователь" },
        { key: "action", label: "Действие" },
        { key: "target_type", label: "Объект" },
        { key: "result", label: "Результат", badge: true },
      ]}
    />
  );
}
