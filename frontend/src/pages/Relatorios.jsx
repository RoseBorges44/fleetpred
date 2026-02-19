import { useEffect, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import {
  fetchRelatorioCustos,
  fetchRelatorioDisponibilidade,
  fetchRelatorioTendencia,
} from "../services/api";

const GRID_STROKE = "#2e3345";
const TOOLTIP_STYLE = {
  contentStyle: {
    background: "#1a1d27",
    border: "1px solid #2e3345",
    borderRadius: 6,
    fontSize: "0.78rem",
  },
  labelStyle: { color: "#e2e8f0", fontWeight: 600 },
  itemStyle: { color: "#94a3b8" },
};

function fmtBRL(v) {
  return Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtBRLShort(v) {
  if (v >= 1000) return `R$ ${(v / 1000).toFixed(1)}k`;
  return fmtBRL(v);
}

export default function Relatorios() {
  const [custos, setCustos] = useState(null);
  const [disp, setDisp] = useState(null);
  const [tendencia, setTendencia] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchRelatorioCustos(),
      fetchRelatorioDisponibilidade(),
      fetchRelatorioTendencia(),
    ]).then(([c, d, t]) => {
      setCustos(c);
      setDisp(d);
      setTendencia(t);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Carregando relatórios...</div>;

  // Dados para gráfico de custo por tipo
  const custoTipoData = (custos.por_tipo || []).map((t) => ({
    name: t.tipo.charAt(0).toUpperCase() + t.tipo.slice(1),
    valor: t.total,
    tipo: t.tipo,
  }));

  const tipoCores = { Preventiva: "#22c55e", Preditiva: "#a855f7", Corretiva: "#ef4444" };

  // Top 5 veículos
  const topVeiculos = (custos.top_5_veiculos || []).map((v) => ({
    name: `${v.placa}`,
    valor: v.custo_total,
    label: `${v.placa} · ${v.modelo}`,
  }));
  const maxCusto = Math.max(...topVeiculos.map((v) => v.valor), 1);

  // Tendência
  const tendenciaData = (tendencia.tendencia_mensal || []).map((m) => ({
    mes: m.mes.slice(5),
    Corretiva: m.corretiva,
    Preditiva: m.preditiva,
    Preventiva: m.preventiva,
  }));

  // Horas paradas
  const horasData = (disp.horas_paradas_mensal || []).map((h) => ({
    mes: h.mes.slice(5),
    horas: h.horas_paradas,
  }));

  return (
    <div>
      <div className="page-header">
        <h1>◰ Relatórios</h1>
        <p>Análise de custos, disponibilidade e tendências da frota</p>
      </div>

      {/* KPI cards */}
      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(3, 1fr)", marginBottom: 24 }}>
        <div className="kpi-card">
          <span className="kpi-label">Custo Total Manutenção</span>
          <span className="kpi-value danger">{fmtBRL(custos.custo_total)}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Horas Paradas (último mês)</span>
          <span className="kpi-value accent">
            {disp.horas_paradas_mensal?.at(-1)?.horas_paradas || 0}h
          </span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Economia Preditiva</span>
          <span className="kpi-value success">{fmtBRL(custos.economia_preditiva_estimada)}</span>
        </div>
      </div>

      {/* Row 1: Custo por tipo + Tendência */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Custo por tipo */}
        <div className="box">
          <span className="box-label">Custo por Tipo</span>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={custoTipoData} barSize={48}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
              <XAxis dataKey="name" axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} tickFormatter={fmtBRLShort} />
              <Tooltip
                {...TOOLTIP_STYLE}
                formatter={(v) => [fmtBRL(v), "Total"]}
              />
              <Bar dataKey="valor" radius={[4, 4, 0, 0]}>
                {custoTipoData.map((entry, i) => (
                  <Cell key={i} fill={tipoCores[entry.name] || "#94a3b8"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Tendência 6 meses */}
        <div className="box">
          <span className="box-label">Tendência 6 Meses</span>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={tendenciaData}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
              <XAxis dataKey="mes" axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} tickFormatter={fmtBRLShort} />
              <Tooltip
                {...TOOLTIP_STYLE}
                formatter={(v) => [fmtBRL(v)]}
              />
              <Legend />
              <Line
                type="monotone" dataKey="Corretiva" stroke="#ef4444"
                strokeWidth={2} strokeDasharray="6 3"
                dot={{ fill: "#ef4444", r: 4 }}
              />
              <Line
                type="monotone" dataKey="Preditiva" stroke="#a855f7"
                strokeWidth={2}
                dot={{ fill: "#a855f7", r: 4 }}
              />
              <Line
                type="monotone" dataKey="Preventiva" stroke="#22c55e"
                strokeWidth={2}
                dot={{ fill: "#22c55e", r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2: Top 5 veículos + Horas paradas */}
      <div className="grid-2">
        {/* Top 5 veículos */}
        <div className="box">
          <span className="box-label">Top 5 Veículos por Custo</span>
          <div style={{ marginTop: 12 }}>
            {topVeiculos.map((v, i) => {
              const pct = (v.valor / maxCusto) * 100;
              return (
                <div key={i} style={{ marginBottom: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: "0.82rem" }}>
                      <span className="font-mono" style={{ fontWeight: 600 }}>{v.name}</span>
                    </span>
                    <span className="font-mono" style={{ fontSize: "0.8rem", color: "var(--accent)" }}>
                      {fmtBRL(v.valor)}
                    </span>
                  </div>
                  <div style={{
                    height: 10,
                    background: "var(--surface-alt)",
                    borderRadius: 99,
                    overflow: "hidden",
                  }}>
                    <div style={{
                      height: "100%",
                      width: `${pct}%`,
                      borderRadius: 99,
                      background: `linear-gradient(90deg, var(--accent), var(--danger))`,
                      transition: "width 0.4s ease",
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Horas paradas por mês */}
        <div className="box">
          <span className="box-label">Horas Paradas por Mês</span>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={horasData} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
              <XAxis dataKey="mes" axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} />
              <Tooltip
                {...TOOLTIP_STYLE}
                formatter={(v) => [`${v}h`, "Horas paradas"]}
              />
              <Bar dataKey="horas" radius={[4, 4, 0, 0]}>
                {horasData.map((entry, i) => (
                  <Cell key={i} fill={entry.horas > 80 ? "#ef4444" : entry.horas > 50 ? "#f59e0b" : "#22c55e"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
