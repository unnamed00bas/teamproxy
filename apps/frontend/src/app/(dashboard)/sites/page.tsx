"use client";

import { ResourceList } from "@/components/ResourceList";
import type { Site } from "@/lib/types";

export default function SitesPage() {
  return (
    <ResourceList<Site>
      title="Сайты"
      path="/sites"
      columns={[
        { key: "name", label: "Название" },
        { key: "slug", label: "Слаг" },
        { key: "status", label: "Статус", badge: true },
        { key: "nodes_count", label: "Узлы" },
        { key: "services_count", label: "Сервисы" },
        { key: "publications_count", label: "Публикации" },
        { key: "peers_count", label: "Пиры" },
      ]}
    />
  );
}
