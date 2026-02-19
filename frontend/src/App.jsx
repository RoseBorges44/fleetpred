import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import VeiculoDetalhe from "./pages/VeiculoDetalhe";
import Ocorrencia from "./pages/Ocorrencia";
import Diagnostico from "./pages/Diagnostico";
import PlanoManutencao from "./pages/PlanoManutencao";
import Relatorios from "./pages/Relatorios";

const navItems = [
  { to: "/", icon: "◫", label: "Dashboard" },
  { to: "/veiculo", icon: "◉", label: "Ficha Veículo" },
  { to: "/ocorrencia", icon: "✎", label: "Registro Ocorrência" },
  { to: "/diagnostico", icon: "⚡", label: "Diagnóstico IA" },
  { to: "/manutencao", icon: "▦", label: "Plano Manutenção" },
  { to: "/relatorios", icon: "◰", label: "Relatórios" },
];

export default function App() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">🚛</span>
          <span className="logo-text">FLEETPRED</span>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                "nav-link" + (isActive ? " active" : "")
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="text-dim">v0.1.0</span>
        </div>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/veiculo" element={<VeiculoDetalhe />} />
          <Route path="/veiculo/:id" element={<VeiculoDetalhe />} />
          <Route path="/ocorrencia" element={<Ocorrencia />} />
          <Route path="/ocorrencia/:veiculoId" element={<Ocorrencia />} />
          <Route path="/diagnostico" element={<Diagnostico />} />
          <Route path="/diagnostico/:id" element={<Diagnostico />} />
          <Route path="/manutencao" element={<PlanoManutencao />} />
          <Route path="/relatorios" element={<Relatorios />} />
        </Routes>
      </main>
    </div>
  );
}
