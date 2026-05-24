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
}: {
  title: string;
  path: string;
  columns: Column<T>[];
  actions?: React.ReactNode;
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
  }, [path]);

  const filtered = query
    ? rows.filter((r) =>
        JSON.stringify(r).toLowerCase().includes(query.toLowerCase()),
      )
    : rows;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{title}</h1>
        {actions}
      </div>
      <input
        className="input max-w-sm"
        placeholder="Filter…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {error && <div className="text-red-400">Error: {error}</div>}
      <div className="card overflow-x-auto p-0">
        <table className="data">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={String(c.key)}>{c.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length}>Loading…</td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="text-slate-500">
                  No records
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
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="text-xs text-slate-500">{total} total</div>
    </div>
  );
}
