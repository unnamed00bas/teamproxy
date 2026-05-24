"use client";

import { ResourceList } from "@/components/ResourceList";
import type { Peer } from "@/lib/types";

export default function PeersPage() {
  return (
    <ResourceList<Peer>
      title="VPN / Peers"
      path="/peers"
      columns={[
        { key: "name", label: "Name" },
        { key: "role", label: "Role" },
        { key: "assigned_tunnel_ip", label: "Tunnel IP" },
        { key: "status", label: "Status", badge: true },
      ]}
    />
  );
}
