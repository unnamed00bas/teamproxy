"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Me {
  email: string;
  role: string;
}

export default function SettingsPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.get<Me>("/auth/me").then(setMe).catch(() => {});
    api
      .get<Record<string, unknown>>("/settings/info")
      .then(setInfo)
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Settings</h1>
      <div className="card">
        <h2 className="mb-2 font-medium">Account</h2>
        <div className="text-sm text-slate-300">
          <div>Email: {me?.email ?? "—"}</div>
          <div>Role: {me?.role ?? "—"}</div>
        </div>
      </div>
      <div className="card">
        <h2 className="mb-2 font-medium">Runtime</h2>
        <pre className="text-xs text-slate-300">
          {info ? JSON.stringify(info, null, 2) : "—"}
        </pre>
      </div>
    </div>
  );
}
