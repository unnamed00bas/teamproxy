"use client";

import { ResourceList } from "@/components/ResourceList";
import type { Site } from "@/lib/types";

export default function SitesPage() {
  return (
    <ResourceList<Site>
      title="Sites"
      path="/sites"
      columns={[
        { key: "name", label: "Name" },
        { key: "slug", label: "Slug" },
        { key: "status", label: "Status", badge: true },
        { key: "nodes_count", label: "Nodes" },
        { key: "services_count", label: "Services" },
        { key: "publications_count", label: "Publications" },
        { key: "peers_count", label: "Peers" },
      ]}
    />
  );
}
