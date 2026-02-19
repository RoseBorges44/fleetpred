import { useEffect, useState } from "react";
import { fetchManutencoes, fetchManutencoesPrioridade } from "../services/api";

const DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

const TIPO_COLORS = {
  preventiva: { bg: "var(--success-dim)", border: "var(--success)", text: "var(--success)" },
  preditiva:  { bg: "rgba(168,85,247,0.12)", border: "#a855f7", text: "#a855f7" },
  corretiva:  { bg: "var(--danger-dim)", border: "var(--danger)", text: "var(--danger)" },
};

function getWeekDays() {
  const today = new Date();
  const dayOfWeek = today.getDay();
  // Monday = 0 in our grid
  const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  const days = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + mondayOffset + i);
    days.push({
      date: d,
      iso: d.toISOString().slice(0, 10),
      day: d.getDate(),
      isToday: d.toDateString() === today.toDateString(),
    });
  }
  return days;
}

export default function PlanoManutencao() {
  const [agendadas, setAgendadas] = useState([]);
  const [prioridade, setPrioridade] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchManutencoes(), fetchManutencoesPrioridade()])
      .then(([a, p]) => { setAgendadas(a); setPrioridade(p); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Carregando plano de manutenção...</div>;

  const weekDays = getWeekDays();
  const totalSemana = agendadas.length;
  const preditivas = agendadas.filter((m) => m.tipo === "preditiva").length;
  const corretivas = agendadas.filter((m) => m.tipo === "corretiva").length;

  // Agrupar manutenções por data
  const porData = {};
  agendadas.forEach((m) => {
    const key = m.data_agendada;
    if (!porData[key]) porData[key] = [];
    porData[key].push(m);
  });

  return (
    <div>
      <div className="page-header">
        <h1>▦ Plano de Manutenção</h1>
        <p>Calendário semanal e fila de prioridade</p>
      </div>

      {/* KPI cards */}
      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(3, 1fr)", marginBottom: 24 }}>
        <div className="kpi-card">
          <span className="kpi-label">Total Semana</span>
          <span className="kpi-value accent">{totalSemana}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Preditivas</span>
          <span className="kpi-value" style={{ color: "#a855f7" }}>{preditivas}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Corretivas</span>
          <span className="kpi-value danger">{corretivas}</span>
        </div>
      </div>

      {/* Calendário semanal */}
      <div className="box" style={{ marginBottom: 24 }}>
        <span className="box-label">Calendário Semanal</span>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(7, 1fr)",
          gap: 10,
          marginTop: 8,
        }}>
          {weekDays.map((wd) => {
            const manutencoesHoje = porData[wd.iso] || [];
            return (
              <div key={wd.iso} style={{
                background: wd.isToday ? "var(--accent-dim)" : "var(--surface-alt)",
                border: wd.isToday ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                padding: 12,
                minHeight: 130,
              }}>
                {/* Header do dia */}
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 10,
                }}>
                  <span style={{
                    fontSize: "0.72rem",
                    color: wd.isToday ? "var(--accent)" : "var(--text-dim)",
                    fontWeight: 600,
                    textTransform: "uppercase",
                  }}>
                    {DIAS_SEMANA[weekDays.indexOf(wd)]}
                  </span>
                  <span style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: wd.isToday ? "1.1rem" : "0.9rem",
                    fontWeight: wd.isToday ? 700 : 500,
                    color: wd.isToday ? "var(--accent)" : "var(--text)",
                  }}>
                    {wd.day}
                  </span>
                </div>

                {/* Cards de manutenção */}
                {manutencoesHoje.map((m) => {
                  const colors = TIPO_COLORS[m.tipo];
                  return (
                    <div key={m.id} style={{
                      background: colors.bg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 4,
                      padding: "6px 8px",
                      marginBottom: 6,
                    }}>
                      <div style={{
                        fontSize: "0.7rem",
                        fontWeight: 600,
                        color: colors.text,
                        fontFamily: "var(--font-mono)",
                      }}>
                        {m.placa}
                      </div>
                      <div style={{
                        fontSize: "0.68rem",
                        color: "var(--text-muted)",
                        lineHeight: 1.3,
                        marginTop: 2,
                      }}>
                        {m.descricao.length > 35 ? m.descricao.slice(0, 35) + "…" : m.descricao}
                      </div>
                    </div>
                  );
                })}

                {manutencoesHoje.length === 0 && (
                  <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textAlign: "center", marginTop: 20 }}>
                    —
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Fila de prioridade */}
      <div className="box">
        <span className="box-label">Fila de Prioridade</span>
        <div style={{ marginTop: 8 }}>
          {prioridade.length === 0 && (
            <div className="empty-state">Nenhuma manutenção agendada</div>
          )}
          {prioridade.map((m, i) => {
            const rank = i + 1;
            const circleColor = rank === 1 ? "var(--danger)" : rank === 2 ? "var(--accent)" : rank <= 5 ? "#a855f7" : "var(--text-dim)";
            const colors = TIPO_COLORS[m.tipo];
            return (
              <div key={m.id} style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                padding: "12px 0",
                borderBottom: "1px solid var(--border)",
              }}>
                {/* Número de posição */}
                <div style={{
                  width: 30,
                  height: 30,
                  borderRadius: "50%",
                  background: circleColor,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: "#fff",
                  flexShrink: 0,
                }}>
                  {rank}
                </div>

                {/* Placa */}
                <span className="font-mono" style={{ fontWeight: 600, fontSize: "0.9rem", minWidth: 80 }}>
                  {m.placa}
                </span>

                {/* Descrição */}
                <span style={{ flex: 1, fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  {m.descricao}
                </span>

                {/* Badge tipo */}
                <span className={`badge ${m.tipo}`}>{m.tipo}</span>

                {/* Prob falha se existir */}
                {m.probabilidade_falha != null && (
                  <span className="font-mono" style={{
                    fontSize: "0.78rem",
                    color: m.probabilidade_falha >= 0.7 ? "var(--danger)" : "var(--accent)",
                    fontWeight: 600,
                    minWidth: 40,
                    textAlign: "right",
                  }}>
                    {Math.round(m.probabilidade_falha * 100)}%
                  </span>
                )}

                {/* Data agendada */}
                <span className="text-dim font-mono" style={{ fontSize: "0.75rem", minWidth: 85 }}>
                  {m.data_agendada}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
