import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/", label: "Overview", icon: "◉" },
  { to: "/inventory", label: "Inventory", icon: "▣" },
  { to: "/routes", label: "Routes", icon: "⇄" },
  { to: "/tests", label: "Tests", icon: "✓" },
  { to: "/projects", label: "Projects", icon: "◫" },
  { to: "/graphs", label: "Graphs", icon: "◎" },
  { to: "/architecture", label: "Architecture", icon: "⬡" },
];

interface SidebarProps {
  repoName?: string;
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ repoName, open, onClose }: SidebarProps) {
  const now = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" });

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="sidebar-brand">
        <div className="sidebar-logo" aria-hidden>⬡</div>
        <div className="sidebar-brand-text">
          <h1>Repo Intelligence</h1>
          <p title={repoName}>{repoName ?? "Loading…"}</p>
        </div>
      </div>

      <div className="sidebar-section-label">Navigation</div>
      <nav className="sidebar-nav" onClick={onClose}>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <span className="nav-icon" aria-hidden>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span>{now}</span>
        <div className="sidebar-footer-dot" title="API connected" />
      </div>
    </aside>
  );
}
