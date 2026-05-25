"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type {
  ProtocolType,
  PublishedServiceCreateResult,
  WgClientOption,
} from "@/lib/types";

const PROTOCOLS: ProtocolType[] = ["http", "https", "tcp", "udp"];

type WgMode = "existing" | "new";

export function ServiceWizard({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [protocol, setProtocol] = useState<ProtocolType>("http");
  const [backendHost, setBackendHost] = useState("");
  const [backendPort, setBackendPort] = useState("");
  const [tls, setTls] = useState(true);

  const [wgMode, setWgMode] = useState<WgMode>("existing");
  const [wgClients, setWgClients] = useState<WgClientOption[]>([]);
  const [wgClientsError, setWgClientsError] = useState<string | null>(null);
  const [wgClientId, setWgClientId] = useState("");
  const [wgNewName, setWgNewName] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PublishedServiceCreateResult | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (step !== 1) return;
    api
      .get<WgClientOption[]>("/published-services/wg-clients")
      .then((items) => {
        setWgClients(items);
        setWgClientsError(null);
      })
      .catch((e) =>
        setWgClientsError(
          e instanceof ApiError
            ? e.message
            : "Не удалось получить список WG-конфигов",
        ),
      );
  }, [step]);

  const step0Valid =
    name.trim().length > 0 && backendPort.trim().length > 0 && !isNaN(Number(backendPort));
  const step1Valid =
    wgMode === "existing" ? wgClientId.length > 0 : wgNewName.trim().length > 0;

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.post<PublishedServiceCreateResult>("/published-services", {
        name: name.trim(),
        domain: domain.trim() || null,
        protocol_type: protocol,
        backend_host: backendHost.trim() || null,
        backend_port: Number(backendPort),
        tls_enabled: tls,
        wg_mode: wgMode,
        wg_client_id: wgMode === "existing" ? wgClientId : null,
        wg_new_name: wgMode === "new" ? wgNewName.trim() : null,
      });
      onCreated();
      if (res.wg_config) {
        setResult(res); // show the downloadable config before closing
      } else {
        onClose();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать сервис");
    } finally {
      setSubmitting(false);
    }
  }

  function downloadConfig() {
    if (!result?.wg_config) return;
    const blob = new Blob([result.wg_config], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = result.wg_config_filename || "wg.conf";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function copyConfig() {
    if (!result?.wg_config) return;
    try {
      await navigator.clipboard.writeText(result.wg_config);
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
          <h2 className="text-lg font-semibold">
            {result ? "Конфиг WireGuard" : "Новый сервис"}
          </h2>
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
          {result ? (
            <>
              <div className="rounded-md border border-yellow-500/40 bg-yellow-500/10 px-3 py-2 text-xs text-yellow-300">
                Конфиг показывается один раз. Скачайте его и разверните на
                компьютере: положите в <code>/etc/wireguard/wg0.conf</code> и
                поднимите туннель{" "}
                <code>systemctl enable --now wg-quick@wg0</code>.
              </div>
              <pre className="max-h-64 overflow-auto rounded-md border border-border bg-surface p-3 text-xs text-slate-300">
                {result.wg_config}
              </pre>
            </>
          ) : step === 0 ? (
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="block text-sm text-slate-300">
                  Название <span className="text-red-400">*</span>
                </label>
                <input
                  className="input"
                  placeholder="Например: Grafana"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="space-y-1">
                <label className="block text-sm text-slate-300">
                  Домен (DNS-адрес)
                </label>
                <input
                  className="input"
                  placeholder="grafana.example.com"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-sm text-slate-300">Протокол</label>
                  <select
                    className="input"
                    value={protocol}
                    onChange={(e) => setProtocol(e.target.value as ProtocolType)}
                  >
                    {PROTOCOLS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="block text-sm text-slate-300">
                    Порт <span className="text-red-400">*</span>
                  </label>
                  <input
                    className="input"
                    placeholder="3000"
                    inputMode="numeric"
                    value={backendPort}
                    onChange={(e) => setBackendPort(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="block text-sm text-slate-300">
                  Адрес сервиса (хост)
                </label>
                <input
                  className="input"
                  placeholder="пусто = IP туннеля выбранного WG"
                  value={backendHost}
                  onChange={(e) => setBackendHost(e.target.value)}
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-accent"
                  checked={tls}
                  onChange={(e) => setTls(e.target.checked)}
                />
                Выпустить TLS-сертификат (Let&apos;s Encrypt)
              </label>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex gap-2">
                <button
                  type="button"
                  className={wgMode === "existing" ? "btn" : "btn-ghost"}
                  onClick={() => setWgMode("existing")}
                >
                  Существующий WG
                </button>
                <button
                  type="button"
                  className={wgMode === "new" ? "btn" : "btn-ghost"}
                  onClick={() => setWgMode("new")}
                >
                  Создать новый
                </button>
              </div>

              {wgMode === "existing" ? (
                wgClientsError ? (
                  <div className="text-sm text-red-400">{wgClientsError}</div>
                ) : wgClients.length === 0 ? (
                  <div className="text-sm text-slate-400">
                    Нет доступных WG-конфигов. Создайте новый.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {wgClients.map((c) => (
                      <label
                        key={c.id}
                        className={`flex cursor-pointer items-center justify-between rounded-md border px-3 py-2 text-sm ${
                          wgClientId === c.id
                            ? "border-accent bg-accent/10"
                            : "border-border hover:bg-surface"
                        }`}
                      >
                        <span>
                          <span className="text-slate-200">{c.name}</span>
                          <span className="ml-2 text-slate-500">
                            {c.tunnel_ip ?? "—"}
                          </span>
                        </span>
                        <input
                          type="radio"
                          name="wg-client"
                          className="h-4 w-4 accent-accent"
                          checked={wgClientId === c.id}
                          onChange={() => setWgClientId(c.id)}
                        />
                      </label>
                    ))}
                  </div>
                )
              ) : (
                <div className="space-y-1">
                  <label className="block text-sm text-slate-300">
                    Имя WG-конфига <span className="text-red-400">*</span>
                  </label>
                  <input
                    className="input"
                    placeholder={name || "office-pc"}
                    value={wgNewName}
                    onChange={(e) => setWgNewName(e.target.value)}
                  />
                  <p className="text-xs text-slate-500">
                    После сохранения вы получите готовый конфиг для скачивания.
                  </p>
                </div>
              )}
            </div>
          )}

          {error && <div className="text-sm text-red-400">Ошибка: {error}</div>}
        </div>

        <div className="flex items-center justify-between gap-2 border-t border-border px-5 py-4">
          {result ? (
            <>
              <button type="button" className="btn-ghost" onClick={copyConfig}>
                {copied ? "Скопировано" : "Скопировать"}
              </button>
              <div className="flex gap-2">
                <button type="button" className="btn-ghost" onClick={downloadConfig}>
                  Скачать
                </button>
                <button type="button" className="btn" onClick={onClose}>
                  Готово
                </button>
              </div>
            </>
          ) : (
            <>
              <button
                type="button"
                className="btn-ghost"
                onClick={() => (step === 0 ? onClose() : setStep(0))}
                disabled={submitting}
              >
                {step === 0 ? "Отмена" : "Назад"}
              </button>
              {step === 0 ? (
                <button
                  type="button"
                  className="btn"
                  onClick={() => setStep(1)}
                  disabled={!step0Valid}
                >
                  Далее
                </button>
              ) : (
                <button
                  type="button"
                  className="btn"
                  onClick={submit}
                  disabled={submitting || !step1Valid}
                >
                  {submitting ? "Сохранение…" : "Сохранить"}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
