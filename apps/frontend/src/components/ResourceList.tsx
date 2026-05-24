"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "./StatusBadge";

export interface Column<T> {
  key: keyof T | string;
  label: string;
  render?: (row: T) => React.ReactNode;
  badge?: boolean;
}

interface Page<T> {
  items: T[];
  total: number;
}

export function ResourceList<T extends { id: string }>({
  title,
  path,
  columns,
  actions,
  rowActions,
  refreshToken,
}: {
  title: string;
  path: string;
  columns: Column<T>[];
  actions?: React.ReactNode;
  rowActions?: (row: T) => React.ReactNode;
  refreshToken?: number;
}) {
  const [rows, setRows] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .get<Page<T>>(path)
      .then((page) => {
        if (cancelled) return;
        setRows(page.items);
        setTotal(page.total);
        setError(null);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [path, refreshToken]);

  const filtered = query
    ? rows.filter((r) =>
        JSON.stringify(r).toLowerCase().includes(query.toLowerCase()),
      )
    : rows;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">{title}</h1>
        {actions}
      </div>
      <input
        className="input max-w-sm"
        placeholder="Поиск…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {error && <div className="text-red-400">Ошибка: {error}</div>}
      <div className="card overflow-x-auto p-0">
        <table className="data">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={String(c.key)}>{c.label}</th>
              ))}
              {rowActions && <th className="text-right" />}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length + (rowActions ? 1 : 0)}>
                  Загрузка…
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (rowActions ? 1 : 0)}
                  className="text-slate-500"
                >
                  Нет записей
                </td>
              </tr>
            ) : (
              filtered.map((row) => (
                <tr key={row.id}>
                  {columns.map((c) => {
                    const value = (row as Record<string, unknown>)[
                      String(c.key)
                    ];
                    return (
                      <td key={String(c.key)}>
                        {c.render
                          ? c.render(row)
                          : c.badge
                            ? <StatusBadge value={String(value ?? "unknown")} />
                            : String(value ?? "—")}
                      </td>
                    );
                  })}
                  {rowActions && (
                    <td className="whitespace-nowrap text-right">
                      {rowActions(row)}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="text-xs text-slate-500">Всего: {total}</div>
    </div>
  );
}
