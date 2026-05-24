"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Site } from "@/lib/types";

interface SitesPage {
  items: Site[];
}

interface Info {
  wg_hub_configured?: boolean;
  wg_hub_endpoint?: string;
  wg_hub_tunnel_subnet?: string;
}

interface ProvisionResult {
  peer_id: string;
  public_key: string;
  private_key: string;
  config: string;
  assigned_tunnel_ip: string | null;
  hub_configured: boolean;
}

export function GatewayProvisionModal({
  onClose,
  onProvisioned,
}: {
  onClose: () => void;
  onProvisioned: () => void;
}) {
  const [sites, setSites] = useState<Site[]>([]);
  const [info, setInfo] = useState<Info | null>(null);
  const [siteId, setSiteId] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProvisionResult | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<SitesPage>("/sites"),
      api.get<Info>("/settings/info").catch(() => ({}) as Info),
    ])
      .then(([s, i]) => {
        setSites(s.items);
        setInfo(i);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка"))
      .finally(() => setLoading(false));
  }, []);

  async function provision() {
    setBusy(true);
    setError(null);
    try {
      const res = await api.post<ProvisionResult>("/peers/provision-gateway", {
        site_id: siteId,
        name: name.trim() || null,
      });
      setResult(res);
      onProvisioned();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать шлюз");
    } finally {
      setBusy(false);
    }
  }

  async function copyConfig() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.config);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="card flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden p-0">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-lg font-semibold">Подключить шлюз сайта</h2>
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost px-2 py-1"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          {!result ? (
            <>
              <p className="text-sm text-slate-400">
                Будет создан пир-шлюз: сгенерируются ключи, выделится IP в
                туннеле, заполнятся параметры хаба и сайт привяжется к шлюзу.
                Установка конфига на сервер — вручную.
              </p>

              {info && info.wg_hub_configured === false && (
                <div className="rounded-md border border-yellow-500/40 bg-yellow-500/10 px-3 py-2 text-xs text-yellow-300">
                  Хаб не настроен (нет публичного ключа/endpoint в настройках) —
                  в конфиге будут заглушки. Задайте WG_HUB_PUBLIC_KEY и
                  WG_HUB_ENDPOINT.
                </div>
              )}

              {loading ? (
                <div className="text-sm text-slate-400">Загрузка…</div>
              ) : sites.length === 0 ? (
                <div className="text-sm text-yellow-400">
                  Нет сайтов. Сначала создайте сайт.
                </div>
              ) : (
                <>
                  <div className="space-y-1">
                    <label className="block text-sm text-slate-300">
                      Сайт <span className="text-red-400">*</span>
                    </label>
                    <select
                      className="input"
                      value={siteId}
                      onChange={(e) => setSiteId(e.target.value)}
                    >
                      <option value="">— не выбрано —</option>
                      {sites.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({s.slug})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="block text-sm text-slate-300">
                      Имя пира
                    </label>
                    <input
                      className="input"
                      placeholder="по умолчанию: <слаг>-gateway"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>
                </>
              )}
            </>
          ) : (
            <>
              <div className="rounded-md border border-yellow-500/40 bg-yellow-500/10 px-3 py-2 text-xs text-yellow-300">
                Приватный ключ показывается один раз и нигде не сохраняется.
                Скопируйте конфиг в <code>/etc/wireguard/wg0.conf</code> на шлюзе
                и поднимите туннель:{" "}
                <code>systemctl enable --now wg-quick@wg0</code>.
              </div>
              {!result.hub_configured && (
                <div className="rounded-md border border-yellow-500/40 bg-yellow-500/10 px-3 py-2 text-xs text-yellow-300">
                  Хаб не настроен — замените заглушки PublicKey/Endpoint вручную.
                </div>
              )}
              <div className="text-sm text-slate-300">
                IP в туннеле:{" "}
                <span className="font-medium text-slate-100">
                  {result.assigned_tunnel_ip ?? "—"}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">
                    Конфиг wg-quick
                  </span>
                  <button
                    type="button"
                    className="btn-ghost px-2 py-1 text-xs"
                    onClick={copyConfig}
                  >
                    {copied ? "Скопировано" : "Скопировать"}
                  </button>
                </div>
                <pre className="max-h-64 overflow-auto rounded-md border border-border bg-surface p-3 text-xs text-slate-300">
                  {result.config}
                </pre>
              </div>
            </>
          )}

          {error && <div className="text-sm text-red-400">Ошибка: {error}</div>}
        </div>

        <div className="flex items-center justify-between gap-2 border-t border-border px-5 py-4">
          {!result ? (
            <>
              <button
                type="button"
                className="btn-ghost"
                onClick={onClose}
                disabled={busy}
              >
                Отмена
              </button>
              <button
                type="button"
                className="btn"
                onClick={provision}
                disabled={busy || !siteId}
              >
                {busy ? "Создание…" : "Подключить шлюз"}
              </button>
            </>
          ) : (
            <button type="button" className="btn ml-auto" onClick={onClose}>
              Готово
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
