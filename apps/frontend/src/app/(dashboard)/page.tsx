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

  if (error) return <div className="text-red-400">Ошибка: {error}</div>;
  if (!stats) return <div>Загрузка…</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Панель управления</h1>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Сайты" value={stats.sites_total} />
        <Stat label="Сайты онлайн" value={stats.sites_online} />
        <Stat label="Активные пиры" value={`${stats.peers_active}/${stats.peers_total}`} />
        <Stat label="Сервисы" value={stats.services_total} />
        <Stat label="Публикации" value={stats.publications_total} />
        <Stat label="Публичные маршруты" value={stats.publications_public} />
        <Stat label="Нерабочие маршруты" value={stats.broken_routes} />
        <Stat label="Истекающие сертификаты" value={stats.expiring_certificates} />
      </div>

      <div className="card">
        <h2 className="mb-3 font-medium">Недавняя активность</h2>
        <div className="overflow-x-auto">
          <table className="data">
            <thead>
              <tr>
                <th>Время</th>
                <th>Пользователь</th>
                <th>Действие</th>
                <th>Объект</th>
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
    </div>
  );
}
