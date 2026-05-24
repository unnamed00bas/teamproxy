"use client";

import { ResourceList } from "@/components/ResourceList";
import { StatusBadge } from "@/components/StatusBadge";
import type { Service } from "@/lib/types";

export default function ServicesPage() {
  return (
    <ResourceList<Service>
      title="Services"
      path="/services"
      columns={[
        { key: "name", label: "Name" },
        { key: "protocol_type", label: "Protocol" },
        {
          key: "backend",
          label: "Backend",
          render: (s) => `${s.backend_host}:${s.backend_port}`,
        },
        { key: "exposure_mode", label: "Exposure" },
        {
          key: "enabled",
          label: "Enabled",
          render: (s) => (
            <StatusBadge value={s.enabled ? "active" : "disabled"} />
          ),
        },
      ]}
    />
  );
}
