"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DashboardStats } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="card">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-sm text-slate-400">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<DashboardStats>("/health/dashboard")
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="text-red-400">Error: {error}</div>;
  if (!stats) return <div>Loading…</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Sites" value={stats.sites_total} />
        <Stat label="Sites online" value={stats.sites_online} />
        <Stat label="Peers active" value={`${stats.peers_active}/${stats.peers_total}`} />
        <Stat label="Services" value={stats.services_total} />
        <Stat label="Publications" value={stats.publications_total} />
        <Stat label="Public routes" value={stats.publications_public} />
        <Stat label="Broken routes" value={stats.broken_routes} />
        <Stat label="Expiring certs" value={stats.expiring_certificates} />
      </div>

      <div className="card">
        <h2 className="mb-3 font-medium">Recent activity</h2>
        <table className="data">
          <thead>
            <tr>
              <th>When</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Target</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_audit.map((e) => (
              <tr key={e.id}>
                <td>{new Date(e.created_at).toLocaleString()}</td>
                <td>{e.actor_email ?? "—"}</td>
                <td>{e.action}</td>
                <td>{e.target_type ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
