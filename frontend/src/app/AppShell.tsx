import { NavLink, Outlet } from "react-router-dom";

const navigation = [
  { to: "/", label: "Dashboard" },
  { to: "/profiles", label: "Profiles" },
  { to: "/generate", label: "Generate" },
  { to: "/history", label: "History" },
  { to: "/settings", label: "Settings" },
];

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">LV</div>
          <div>
            <strong>Local Voice Studio</strong>
            <p className="muted">Private local XTTS workspace</p>
          </div>
        </div>
        <nav className="nav-list">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
