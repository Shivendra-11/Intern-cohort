import { useTheme } from "../context/ThemeContext";
import { RepoSelector } from "./RepoSelector";

const PAGE_ICONS: Record<string, string> = {
  Overview: "◉",
  Inventory: "▣",
  Routes: "⇄",
  Tests: "✓",
  Projects: "◫",
  Graphs: "◎",
  Architecture: "⬡",
};

interface HeaderProps {
  title: string;
  onMenuToggle: () => void;
}

export function Header({ title, onMenuToggle }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const icon = PAGE_ICONS[title] ?? "◉";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="icon-btn menu-toggle"
          onClick={onMenuToggle}
          aria-label="Toggle menu"
        >
          ☰
        </button>
        <div className="topbar-breadcrumb">
          <span>Repo Intelligence</span>
          <span className="topbar-sep">/</span>
          <span>
            <span aria-hidden style={{ marginRight: "0.3em" }}>{icon}</span>
            {title}
          </span>
        </div>
      </div>
      <div className="topbar-actions">
        <RepoSelector />
        <button
          type="button"
          className="icon-btn"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
