"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/sites", label: "Sites" },
  { href: "/peers", label: "VPN / Peers" },
  { href: "/nodes", label: "Nodes" },
  { href: "/services", label: "Services" },
  { href: "/publications", label: "Publications" },
  { href: "/dns", label: "DNS / TLS" },
  { href: "/deployments", label: "Deployments" },
  { href: "/audit", label: "Audit Log" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-border bg-panel">
      <div className="px-4 py-5 text-lg font-semibold">Control Plane</div>
      <nav className="flex-1 space-y-1 px-2">
        {NAV.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
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
        Log out
      </button>
    </aside>
  );
}
