import { Link, Outlet, useLocation } from "react-router-dom";

const navItems = [
  { to: "/", label: "Search" },
  { to: "/ask", label: "Ask" },
  { to: "/insights", label: "Insights" },
  { to: "/topics", label: "Topics" },
  { to: "/segments", label: "Segments" },
  { to: "/export", label: "Export" },
];

export function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">Review Discovery Engine</h1>
            <p className="text-sm text-slate-500">Spotify review research assistant</p>
          </div>
        </div>
      </header>
      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-6">
        <aside className="w-48 shrink-0">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const active = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`block rounded-md px-3 py-2 text-sm font-medium ${
                    active
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
