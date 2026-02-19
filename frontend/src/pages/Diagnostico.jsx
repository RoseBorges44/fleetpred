import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchAlertas, fetchDiagnostico } from "../services/api";

export default function Diagnostico() {
  const { id: paramId } = useParams();
  const [alertas, setAlertas] = useState([]);
  const [selId, setSelId] = useState(paramId || null);
  const [detalhe, setDetalhe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);

  useEffect(() => {
    fetchAlertas().then((a) => {
      setAlertas(a);
      // Se veio com id na URL mas não tem diagnóstico selecionado, usar o paramId
      if (paramId) setSelId(paramId);
      // Se não veio com id, selecionar o primeiro alerta com diagnóstico
      else if (a.length > 0) {
        const first = a.find((x) => x.diagnostico_id);
        if (first) setSelId(String(first.diagnostico_id));
      }
    }).finally(() => setLoading(false));
  }, [paramId]);

  useEffect(() => {
    if (!selId) { setDetalhe(null); return; }
    setLoadingDetalhe(true);
    fetchDiagnostico(selId)
      .then(setDetalhe)
      .catch(() => setDetalhe(null))
      .finally(() => setLoadingDetalhe(false));
  }, [selId]);

  if (loading) return <div className="loading">Carregando diagnósticos...</div>;

  const d = detalhe;
  const probPct = d ? Math.round(d.probabilidade_falha * 100) : 0;
  const circleR = 32;
  const circumference = 2 * Math.PI * circleR;
  const dashOffset = d ? circumference - (probPct / 100) * circumference : circumference;
  const probColor = probPct >= 70 ? "var(--danger)" : probPct >= 50 ? "var(--accent)" : "var(--success)";

  return (
    <div>
      <div className="page-header">
        <h1>⚡ Diagnóstico IA</h1>
        <p>Análise preditiva de falhas baseada em inteligência artificial</p>
      </div>

      {/* Mock banner */}
      <div style={{
        background: "rgba(168,85,247,0.10)",
        border: "1px solid rgba(168,85,247,0.25)",
        borderRadius: "var(--radius-sm)",
        padding: "10px 16px",
        marginBottom: 20,
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}>
        <span style={{ fontSize: "1.1rem" }}>⚡</span>
        <span style={{ fontSize: "0.8rem", color: "#a855f7", fontWeight: 600 }}>
          RESPOSTAS SIMULADAS (MOCK)
        </span>
        <span style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>
          — será gerado pelo LLM na versão final
        </span>
      </div>

      {/* Layout 1/3 + 2/3 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>

        {/* Lista de alertas */}
        <div className="box" style={{ maxHeight: "calc(100vh - 220px)", overflowY: "auto" }}>
          <span className="box-label">Alertas com Diagnóstico</span>
          <div style={{ marginTop: 8 }}>
            {alertas.filter((a) => a.diagnostico_id).length === 0 && (
              <div className="empty-state">Nenhum diagnóstico disponível</div>
            )}
            {alertas.filter((a) => a.diagnostico_id).map((a) => {
              const active = String(a.diagnostico_id) === String(selId);
              return (
                <div
                  key={a.id}
                  onClick={() => setSelId(String(a.diagnostico_id))}
                  style={{
                    padding: "12px 14px",
                    borderBottom: "1px solid var(--border)",
                    cursor: "pointer",
                    background: active ? "var(--accent-dim)" : "transparent",
                    borderLeft: active ? "3px solid var(--accent)" : "3px solid transparent",
                    transition: "all 0.12s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span className={`badge ${a.tipo}`}>{a.tipo}</span>
                    <span className="font-mono" style={{ fontSize: "0.82rem", fontWeight: 600 }}>{a.placa}</span>
                    {a.diag_probabilidade != null && (
                      <span className="font-mono" style={{
                        fontSize: "0.75rem",
                        marginLeft: "auto",
                        color: a.diag_probabilidade >= 0.7 ? "var(--danger)" : "var(--accent)",
                        fontWeight: 600,
                      }}>
                        {Math.round(a.diag_probabilidade * 100)}%
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", lineHeight: 1.4 }}>
                    {a.mensagem.length > 90 ? a.mensagem.slice(0, 90) + "…" : a.mensagem}
                  </p>
                </div>
              );
            })}

            {/* Alertas sem diagnóstico */}
            {alertas.filter((a) => !a.diagnostico_id).length > 0 && (
              <>
                <div style={{
                  padding: "8px 14px",
                  fontSize: "0.7rem",
                  color: "var(--text-dim)",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  fontWeight: 600,
                  borderBottom: "1px solid var(--border)",
                  marginTop: 4,
                }}>
                  Sem diagnóstico
                </div>
                {alertas.filter((a) => !a.diagnostico_id).map((a) => (
                  <div
                    key={a.id}
                    style={{
                      padding: "10px 14px",
                      borderBottom: "1px solid var(--border)",
                      opacity: 0.5,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className={`badge ${a.tipo}`}>{a.tipo}</span>
                      <span className="font-mono" style={{ fontSize: "0.82rem" }}>{a.placa}</span>
                    </div>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: 4 }}>
                      {a.mensagem.length > 90 ? a.mensagem.slice(0, 90) + "…" : a.mensagem}
                    </p>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>

        {/* Detalhe do diagnóstico */}
        <div>
          {loadingDetalhe && <div className="loading">Carregando diagnóstico...</div>}

          {!loadingDetalhe && !d && (
            <div className="empty-state" style={{ marginTop: 60 }}>
              <p>Selecione um alerta para ver o diagnóstico</p>
            </div>
          )}

          {!loadingDetalhe && d && (
            <>
              {/* Header: círculo + info */}
              <div className="box" style={{ marginBottom: 16 }}>
                <span className="box-label">Diagnóstico #{d.id}</span>
                <div style={{ display: "flex", gap: 24, alignItems: "center", marginTop: 4 }}>
                  <svg width="82" height="82" viewBox="0 0 82 82" style={{ flexShrink: 0 }}>
                    <circle cx="41" cy="41" r={circleR} fill="none" stroke="var(--border)" strokeWidth="6" />
                    <circle
                      cx="41" cy="41" r={circleR} fill="none"
                      stroke={probColor} strokeWidth="6"
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      strokeDashoffset={dashOffset}
                      transform="rotate(-90 41 41)"
                      style={{ transition: "stroke-dashoffset 0.5s ease" }}
                    />
                    <text x="41" y="38" textAnchor="middle" fill={probColor} fontSize="18" fontWeight="700" fontFamily="var(--font-mono)">
                      {probPct}%
                    </text>
                    <text x="41" y="52" textAnchor="middle" fill="var(--text-dim)" fontSize="8">
                      prob. falha
                    </text>
                  </svg>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                      <span className="font-mono" style={{ fontSize: "1rem", fontWeight: 700 }}>{d.placa}</span>
                      <span className="text-muted" style={{ fontSize: "0.85rem" }}>{d.modelo}</span>
                    </div>
                    <p style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 6 }}>{d.componente}</p>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <span className="font-mono" style={{ color: "var(--accent)", fontWeight: 600 }}>
                        {d.horizonte_dias} dias
                      </span>
                      <span className={`badge ${d.severidade === "critica" || d.severidade === "alta" ? "critico" : "atencao"}`}>
                        {d.severidade}
                      </span>
                      <span className="text-dim" style={{ fontSize: "0.75rem" }}>
                        {d.sistema} · {Number(d.km_atual).toLocaleString("pt-BR")} km
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-dim" style={{ fontSize: "0.78rem", marginTop: 12, fontStyle: "italic" }}>
                  {d.base_historica}
                </p>
              </div>

              {/* Grid: sintomas + peças */}
              <div className="grid-2" style={{ marginBottom: 16 }}>
                <div className="box">
                  <span className="box-label">Sintomas Correlacionados</span>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                    {(d.sintomas_correlacionados || []).map((s, i) => (
                      <span key={i} className="chip" style={{
                        background: "var(--accent-dim)",
                        borderColor: "var(--accent)",
                        color: "var(--accent)",
                      }}>{s}</span>
                    ))}
                  </div>
                </div>
                <div className="box">
                  <span className="box-label">Peças Sugeridas</span>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4, marginBottom: 12 }}>
                    {(d.pecas_sugeridas || []).map((p, i) => (
                      <span key={i} className="chip">{p}</span>
                    ))}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className="text-dim" style={{ fontSize: "0.72rem", textTransform: "uppercase" }}>Economia estimada</span>
                    <span className="font-mono text-success" style={{ fontWeight: 600 }}>
                      {Number(d.economia_estimada).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
                    </span>
                  </div>
                </div>
              </div>

              {/* Ação recomendada */}
              <div className="box" style={{ marginBottom: 16 }}>
                <span className="box-label">Ação Recomendada</span>
                <p style={{ lineHeight: 1.7, marginTop: 4, marginBottom: 16 }}>{d.recomendacao}</p>
                <div style={{ display: "flex", gap: 10 }}>
                  <button className="btn btn-danger">
                    Agendar Manutenção Urgente
                  </button>
                  <button className="btn btn-secondary btn-sm">
                    Exportar Relatório
                  </button>
                </div>
              </div>

              {/* Contexto da ocorrência */}
              <div className="box" style={{ marginBottom: 16 }}>
                <span className="box-label">Contexto da Ocorrência</span>
                <p className="text-muted" style={{ fontSize: "0.85rem", marginTop: 4, lineHeight: 1.6 }}>
                  {d.ocorrencia_descricao}
                </p>
                <div style={{ marginTop: 8 }}>
                  <span className={`badge ${d.ocorrencia_severidade === "alta" || d.ocorrencia_severidade === "critica" ? "critico" : "atencao"}`}>
                    {d.ocorrencia_severidade}
                  </span>
                </div>
              </div>

              {/* JSON completo */}
              <div className="box">
                <span className="box-label">Resposta Completa (JSON)</span>
                <pre style={{
                  background: "var(--bg)",
                  padding: 16,
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono)",
                  color: "var(--text-muted)",
                  overflowX: "auto",
                  marginTop: 4,
                  lineHeight: 1.6,
                }}>
                  {JSON.stringify(d, null, 2)}
                </pre>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
