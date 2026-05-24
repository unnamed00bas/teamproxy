"use client";

import { ResourceList } from "@/components/ResourceList";
import { StatusBadge } from "@/components/StatusBadge";
import type { Service } from "@/lib/types";

export default function ServicesPage() {
  return (
    <ResourceList<Service>
      title="Сервисы"
      path="/services"
      columns={[
        { key: "name", label: "Название" },
        { key: "protocol_type", label: "Протокол" },
        {
          key: "backend",
          label: "Бэкенд",
          render: (s) => `${s.backend_host}:${s.backend_port}`,
        },
        { key: "exposure_mode", label: "Доступ" },
        {
          key: "enabled",
          label: "Включён",
          render: (s) => (
            <StatusBadge value={s.enabled ? "active" : "disabled"} />
          ),
        },
      ]}
    />
  );
}
