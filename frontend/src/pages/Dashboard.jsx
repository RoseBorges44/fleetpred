import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { fetchDashboardStats, fetchVeiculos, fetchAlertas } from "../services/api";

const STATUS_COLORS = { critico: "#ef4444", atencao: "#f59e0b", ok: "#22c55e" };

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [veiculos, setVeiculos] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchDashboardStats(),
      fetchVeiculos(),
      fetchAlertas(0),
    ]).then(([s, v, a]) => {
      setStats(s);
      setVeiculos(v);
      setAlertas(a);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Carregando dashboard...</div>;

  const chartData = ["critico", "atencao", "ok"].map((s) => ({
    name: s === "ok" ? "OK" : s.charAt(0).toUpperCase() + s.slice(1),
    value: stats.status_breakdown[s] || 0,
    color: STATUS_COLORS[s],
  }));

  return (
    <div>
      <div className="page-header">
        <h1>◫ Dashboard da Frota</h1>
        <p>Visão geral do estado da frota e alertas preditivos</p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-label">Veículos Ativos</span>
          <span className="kpi-value success">{stats.total_veiculos}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Alertas Preditivos</span>
          <span className="kpi-value danger">{stats.alertas_pendentes}</span>
          <span className="text-dim" style={{ fontSize: "0.75rem" }}>
            {stats.alertas_criticos} crítico{stats.alertas_criticos !== 1 && "s"}
          </span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Manutenções Hoje</span>
          <span className="kpi-value accent">{stats.manutencoes_hoje}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Disponibilidade</span>
          <span className="kpi-value" style={{ color: stats.disponibilidade_pct >= 90 ? "var(--success)" : "var(--warning)" }}>
            {stats.disponibilidade_pct}%
          </span>
        </div>
      </div>

      {/* Main layout 2/3 + 1/3 */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }}>

        {/* Veículos */}
        <div className="box">
          <span className="box-label">Veículos da Frota</span>
          <div style={{ marginTop: 8 }}>
            {veiculos.map((v) => (
              <div
                key={v.id}
                className="vehicle-row"
                onClick={() => navigate(`/veiculo/${v.id}`)}
              >
                <span style={{ fontSize: "1.2rem" }}>🚛</span>
                <span className="placa">{v.placa}</span>
                <span className="modelo">
                  {v.modelo} · {Number(v.km_atual).toLocaleString("pt-BR")} km
                </span>
                <span style={{ fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--text-dim)", minWidth: 45, textAlign: "right" }}>
                  {v.saude_media}%
                </span>
                <span className={`badge ${v.status}`}>{v.status}</span>
                {v.alertas_pendentes > 0 && (
                  <span className="badge critico" style={{ fontSize: "0.68rem" }}>
                    {v.alertas_pendentes} alerta{v.alertas_pendentes > 1 && "s"}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Coluna direita */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Mini gráfico status */}
          <div className="box">
            <span className="box-label">Status da Frota</span>
            <div style={{ marginTop: 12 }}>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={chartData} barSize={36}>
                  <XAxis dataKey="name" axisLine={false} tickLine={false} />
                  <YAxis hide allowDecimals={false} />
                  <Tooltip
                    cursor={{ fill: "rgba(255,255,255,0.03)" }}
                    formatter={(v) => [v, "Veículos"]}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Alertas recentes */}
          <div className="box" style={{ flex: 1 }}>
            <span className="box-label">Alertas Pendentes</span>
            <div style={{ marginTop: 8 }}>
              {alertas.length === 0 && (
                <div className="empty-state">Nenhum alerta pendente</div>
              )}
              {alertas.map((a) => (
                <div
                  key={a.id}
                  style={{
                    padding: "12px 0",
                    borderBottom: "1px solid var(--border)",
                    cursor: a.diagnostico_id ? "pointer" : "default",
                  }}
                  onClick={() => a.diagnostico_id && navigate(`/diagnostico/${a.diagnostico_id}`)}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span className={`badge ${a.tipo}`}>{a.tipo}</span>
                    <span className="font-mono" style={{ fontSize: "0.78rem" }}>{a.placa}</span>
                    <span className="text-dim" style={{ fontSize: "0.72rem", marginLeft: "auto" }}>
                      {a.data_criacao}
                    </span>
                  </div>
                  <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                    {a.mensagem.length > 120 ? a.mensagem.slice(0, 120) + "…" : a.mensagem}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
