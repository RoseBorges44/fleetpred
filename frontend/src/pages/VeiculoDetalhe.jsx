import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchVeiculos, fetchVeiculo } from "../services/api";

function healthColor(pct) {
  if (pct >= 80) return "var(--success)";
  if (pct >= 50) return "var(--accent)";
  return "var(--danger)";
}

function fmtKm(v) {
  return Number(v).toLocaleString("pt-BR") + " km";
}

function fmtCusto(v) {
  if (v == null) return "—";
  return Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function VeiculoDetalhe() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [lista, setLista] = useState([]);
  const [detalhe, setDetalhe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);

  // Carregar lista de veículos para os chips
  useEffect(() => {
    fetchVeiculos().then(setLista).finally(() => setLoading(false));
  }, []);

  // Carregar detalhe quando id muda
  useEffect(() => {
    if (!id) {
      setDetalhe(null);
      return;
    }
    setLoadingDetalhe(true);
    fetchVeiculo(id).then(setDetalhe).finally(() => setLoadingDetalhe(false));
  }, [id]);

  if (loading) return <div className="loading">Carregando veículos...</div>;

  const v = detalhe?.veiculo;

  return (
    <div>
      <div className="page-header">
        <h1>◉ Ficha do Veículo</h1>
        <p>Selecione um veículo para ver os detalhes</p>
      </div>

      {/* Chips de seleção */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 24 }}>
        {lista.map((vl) => (
          <button
            key={vl.id}
            className="chip"
            onClick={() => navigate(`/veiculo/${vl.id}`)}
            style={{
              cursor: "pointer",
              background: String(vl.id) === id ? "var(--accent-dim)" : undefined,
              borderColor: String(vl.id) === id ? "var(--accent)" : undefined,
              color: String(vl.id) === id ? "var(--accent)" : undefined,
              fontWeight: String(vl.id) === id ? 600 : undefined,
            }}
          >
            <span className={`badge ${vl.status}`} style={{ padding: "1px 6px", fontSize: "0.65rem" }}>
              {vl.status === "ok" ? "●" : vl.status === "atencao" ? "▲" : "✖"}
            </span>
            {vl.placa}
          </button>
        ))}
      </div>

      {/* Nenhum selecionado */}
      {!id && (
        <div className="empty-state">
          <p>Clique em uma placa acima para ver os detalhes do veículo.</p>
        </div>
      )}

      {loadingDetalhe && <div className="loading">Carregando ficha...</div>}

      {v && !loadingDetalhe && (
        <>
          {/* Grid 2 colunas: dados + saúde */}
          <div className="grid-2" style={{ marginBottom: 24 }}>

            {/* Dados do ativo */}
            <div className="box">
              <span className="box-label">Dados do Ativo</span>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, marginTop: 4 }}>
                <span style={{ fontSize: "2rem" }}>🚛</span>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span className="font-mono" style={{ fontSize: "1.3rem", fontWeight: 700 }}>{v.placa}</span>
                    <span className={`badge ${v.status}`}>{v.status}</span>
                  </div>
                  <span className="text-muted" style={{ fontSize: "0.85rem" }}>{v.modelo}</span>
                </div>
              </div>
              <table style={{ width: "100%" }}>
                <tbody>
                  {[
                    ["Ano", v.ano],
                    ["Quilometragem", fmtKm(v.km_atual)],
                    ["Motor", v.motor],
                    ["Último Óleo", v.ultimo_oleo_km ? fmtKm(v.ultimo_oleo_km) : "—"],
                    ["Cadastro", v.data_cadastro],
                  ].map(([label, val]) => (
                    <tr key={label} style={{ background: "transparent" }}>
                      <td style={{ color: "var(--text-dim)", width: 140, padding: "8px 14px 8px 0", border: "none" }}>{label}</td>
                      <td style={{ fontFamily: "var(--font-mono)", fontWeight: 500, padding: "8px 0", border: "none" }}>{val}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Saúde dos componentes */}
            <div className="box">
              <span className="box-label">Saúde dos Componentes</span>
              <div style={{ marginTop: 4 }}>
                {detalhe.componentes.map((c) => (
                  <div key={c.id} className="health-bar-row">
                    <span className="label">{c.nome}</span>
                    <div className="health-bar-track">
                      <div
                        className="health-bar-fill"
                        style={{
                          width: `${c.saude_pct}%`,
                          background: healthColor(c.saude_pct),
                        }}
                      />
                    </div>
                    <span className="pct" style={{ color: healthColor(c.saude_pct) }}>
                      {c.saude_pct}%
                    </span>
                  </div>
                ))}
              </div>
              <div className="text-dim" style={{ fontSize: "0.72rem", marginTop: 12 }}>
                Última inspeção: {detalhe.componentes[0]?.ultima_inspecao || "—"}
              </div>
            </div>
          </div>

          {/* Histórico de manutenções */}
          <div className="box" style={{ marginBottom: 24 }}>
            <span className="box-label">Histórico de Manutenções</span>
            {detalhe.manutencoes.length === 0 ? (
              <div className="empty-state">Nenhuma manutenção registrada</div>
            ) : (
              <div style={{ marginTop: 8 }}>
                {detalhe.manutencoes.map((m) => (
                  <div
                    key={m.id}
                    style={{
                      display: "flex",
                      gap: 16,
                      padding: "14px 0",
                      borderBottom: "1px solid var(--border)",
                      alignItems: "flex-start",
                    }}
                  >
                    {/* Linha vertical da timeline */}
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 14, paddingTop: 4 }}>
                      <div style={{
                        width: 10,
                        height: 10,
                        borderRadius: "50%",
                        background: m.status === "concluida" ? "var(--success)" : m.status === "agendada" ? "var(--info)" : "var(--accent)",
                        flexShrink: 0,
                      }} />
                      <div style={{ width: 2, flex: 1, background: "var(--border)", marginTop: 4 }} />
                    </div>

                    {/* Conteúdo */}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
                        <span className="font-mono text-dim" style={{ fontSize: "0.78rem", minWidth: 85 }}>
                          {m.data_realizada || m.data_agendada}
                        </span>
                        <span className={`badge ${m.tipo}`}>{m.tipo}</span>
                        <span className={`badge ${m.status}`}>{m.status}</span>
                        {m.custo != null && (
                          <span className="font-mono text-accent" style={{ fontSize: "0.78rem", marginLeft: "auto" }}>
                            {fmtCusto(m.custo)}
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: "0.85rem", marginBottom: 2 }}>{m.descricao}</p>
                      {m.km_realizada && (
                        <span className="text-dim" style={{ fontSize: "0.75rem" }}>
                          {fmtKm(m.km_realizada)}
                        </span>
                      )}
                      {m.pecas && (
                        <div style={{ marginTop: 4 }}>
                          {m.pecas.split(",").map((p, i) => (
                            <span key={i} className="chip" style={{ marginRight: 4, marginBottom: 4 }}>
                              {p.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                      {m.observacoes && (
                        <p className="text-dim" style={{ fontSize: "0.75rem", marginTop: 4, fontStyle: "italic" }}>
                          {m.observacoes}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Botões de ação */}
          <div style={{ display: "flex", gap: 12 }}>
            <button
              className="btn btn-primary"
              onClick={() => navigate(`/ocorrencia?veiculo=${v.id}`)}
            >
              ✎ Registrar Ocorrência
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => navigate(`/diagnostico?veiculo=${v.id}`)}
            >
              ⚡ Solicitar Diagnóstico IA
            </button>
          </div>
        </>
      )}
    </div>
  );
}
