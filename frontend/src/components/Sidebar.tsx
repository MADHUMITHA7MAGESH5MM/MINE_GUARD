import { type Page } from "../App";

const NAV_ITEMS: { id: Page; label: string; icon: string; group?: string }[] = [
  { id: "command", label: "Command Center", icon: "◈", group: "Operations" },
  { id: "ai-analysis", label: "AI Incident Analysis", icon: "◎", group: "Operations" },
  { id: "repository", label: "Incident Repository", icon: "≡", group: "Operations" },
  { id: "review", label: "Human Review Center", icon: "⊡", group: "Workflow" },
  { id: "precursor", label: "Precursor Intelligence", icon: "⬡", group: "Workflow" },
  { id: "analytics", label: "Analytics Suite", icon: "◰", group: "Intelligence" },
 
  { id: "simulator", label: "Fatality Simulator", icon: "△", group: "Intelligence" },
  { id: "digital-twin", label: "Site Digital Twin", icon: "⊕", group: "Field" },
];

export default function Sidebar({ page, setPage }: { page: Page; setPage: (p: Page) => void }) {
  const groups = ["Operations", "Workflow", "Intelligence", "Field"];

  return (
    <aside className="flex flex-col w-[220px] min-h-screen border-r flex-shrink-0"
      style={{ background: "#060E1C", borderColor: "rgba(255,255,255,0.07)" }}>
      {/* Logo */}
      <div className="px-5 py-5 border-b" style={{ borderColor: "rgba(255,255,255,0.07)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded flex items-center justify-center text-white text-xs font-bold"
            style={{ background: "#E8531D" }}>
            MG
          </div>
          <div>
            <div className="text-white font-semibold text-sm tracking-wide" style={{ fontFamily: "'DM Sans', sans-serif" }}>
              MINEGUARD
            </div>
            <div className="text-[10px] tracking-widest uppercase" style={{ color: "#4A6080" }}>
              DGMS · Mining
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 overflow-y-auto">
        {groups.map(group => {
          const items = NAV_ITEMS.filter(i => i.group === group);
          return (
            <div key={group} className="mb-4">
              <div className="px-5 mb-1.5 text-[10px] uppercase tracking-widest font-medium"
                style={{ color: "#2D4560" }}>
                {group}
              </div>
              {items.map(item => {
                const active = page === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setPage(item.id)}
                    className="w-full flex items-center gap-3 px-5 py-2 text-left transition-all duration-150 text-sm"
                    style={{
                      background: active ? "rgba(232,83,29,0.1)" : "transparent",
                      color: active ? "#E8531D" : "#6B8AAA",
                      borderLeft: active ? "2px solid #E8531D" : "2px solid transparent",
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    <span className="text-base leading-none">{item.icon}</span>
                    <span className="font-medium text-[13px]">{item.label}</span>
                  </button>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* User */}
      <div className="px-5 py-4 border-t" style={{ borderColor: "rgba(255,255,255,0.07)" }}>
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold text-white"
            style={{ background: "#1E2F47" }}>
            RS
          </div>
          <div>
            <div className="text-[12px] font-medium text-white">R. Sharma</div>
            <div className="text-[10px]" style={{ color: "#3A5570" }}>Safety Manager</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
