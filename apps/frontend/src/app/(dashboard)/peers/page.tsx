"use client";

import { useState } from "react";
import { ResourceList } from "@/components/ResourceList";
import { GatewayProvisionModal } from "@/components/GatewayProvisionModal";
import type { Peer } from "@/lib/types";

export default function PeersPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);

  return (
    <>
      <ResourceList<Peer>
        title="VPN / Пиры"
        path="/peers"
        refreshToken={refreshToken}
        actions={
          <button className="btn" onClick={() => setModalOpen(true)}>
            Подключить шлюз
          </button>
        }
        columns={[
          { key: "name", label: "Имя" },
          { key: "role", label: "Роль" },
          { key: "assigned_tunnel_ip", label: "IP туннеля" },
          { key: "status", label: "Статус", badge: true },
        ]}
      />
      {modalOpen && (
        <GatewayProvisionModal
          onClose={() => setModalOpen(false)}
          onProvisioned={() => setRefreshToken((t) => t + 1)}
        />
      )}
    </>
  );
}
