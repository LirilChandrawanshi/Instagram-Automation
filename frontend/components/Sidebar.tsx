"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { name: "Dashboard", href: "/dashboard" },
  { name: "Accounts", href: "/accounts" },
  { name: "Automation", href: "/automation" },
  { name: "Schedule posts", href: "/schedule" },
  { name: "Comment-to-DM", href: "/comment-dm" },
  { name: "Instagram API", href: "/instagram-api" },
  { name: "Analytics", href: "/analytics" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 w-64 border-r border-slate-200 bg-white">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center border-b border-slate-200 px-6">
          <Link href="/dashboard" className="text-lg font-semibold text-slate-900">
            Instagram Automation
          </Link>
        </div>
        <nav className="flex-1 space-y-0.5 p-4">
          {nav.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-primary-50 text-primary-700"
                    : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
