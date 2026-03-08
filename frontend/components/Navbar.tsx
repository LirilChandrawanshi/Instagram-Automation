"use client";

import { useRouter } from "next/navigation";

interface NavbarProps {
  userEmail?: string | null;
}

export default function Navbar({ userEmail }: NavbarProps) {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div className="flex-1" />
      <div className="flex items-center gap-4">
        {userEmail && (
          <span className="text-sm text-slate-600">{userEmail}</span>
        )}
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Log out
        </button>
      </div>
    </header>
  );
}
