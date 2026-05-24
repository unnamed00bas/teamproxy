"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";

const NAV = [
  { href: "/", label: "Панель" },
  { href: "/sites", label: "Сайты" },
  { href: "/peers", label: "VPN / Пиры" },
  { href: "/nodes", label: "Узлы" },
  { href: "/services", label: "Сервисы" },
  { href: "/publications", label: "Публикации" },
  { href: "/dns", label: "DNS / TLS" },
  { href: "/deployments", label: "Развёртывания" },
  { href: "/audit", label: "Журнал аудита" },
  { href: "/settings", label: "Настройки" },
];

export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-screen w-60 flex-col border-r border-border bg-panel transition-transform duration-200 md:static md:z-auto md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="px-4 py-5 text-lg font-semibold">Control Plane</div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-2">
          {NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`block rounded-md px-3 py-2 text-sm ${
                  active ? "bg-accent text-white" : "hover:bg-surface"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button onClick={logout} className="btn-ghost m-3">
          Выйти
        </button>
      </aside>
    </>
  );
}
