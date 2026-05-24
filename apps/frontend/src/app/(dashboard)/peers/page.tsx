"use client";

import { ResourceList } from "@/components/ResourceList";
import type { Peer } from "@/lib/types";

export default function PeersPage() {
  return (
    <ResourceList<Peer>
      title="VPN / Пиры"
      path="/peers"
      columns={[
        { key: "name", label: "Имя" },
        { key: "role", label: "Роль" },
        { key: "assigned_tunnel_ip", label: "IP туннеля" },
        { key: "status", label: "Статус", badge: true },
      ]}
    />
  );
}
