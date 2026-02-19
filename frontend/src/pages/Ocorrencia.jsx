import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { fetchVeiculos, criarOcorrencia } from "../services/api";

const SISTEMAS = ["Motor", "Freios", "Arrefecimento", "Transmissão", "Suspensão"];

const SINTOMAS_POR_SISTEMA = {
  Motor: [
    "Perda de potência",
    "Ruído anormal",
    "Fumaça excessiva",
    "Consumo elevado de óleo",
    "Vibração anormal",
  ],
  Freios: [
    "Ruído ao frear",
    "Pedal longo",
    "Vibração",
    "Desgaste de lona/pastilha",
    "Aquecimento excessivo",
  ],
  Arrefecimento: [
    "Temperatura elevada",
    "Vazamento de líquido",
    "Ventilador não liga",
    "Consumo de líquido",
  ],
  "Transmissão": [
    "Dificuldade de engate",
    "Ruído em marcha",
    "Trancos",
    "Patinação da embreagem",
  ],
  "Suspensão": [
    "Instabilidade",
    "Ruído em irregularidades",
    "Desgaste de molas",
    "Inclinação lateral",
  ],
};

const SEVERIDADES = ["baixa", "media", "alta", "critica"];

function sevLabel(s) {
  return { baixa: "Baixa", media: "Média", alta: "Alta", critica: "Crítica" }[s];
}

function sevColor(s) {
  if (s === "alta" || s === "critica") return { bg: "var(--danger-dim)", border: "var(--danger)", text: "var(--danger)" };
  if (s === "media") return { bg: "rgba(245,158,11,0.12)", border: "var(--accent)", text: "var(--accent)" };
  return { bg: "var(--info-dim)", border: "var(--info)", text: "var(--info)" };
}

export default function Ocorrencia() {
  const { veiculoId } = useParams();
  const [searchParams] = useSearchParams();
  const preselect = veiculoId || searchParams.get("veiculo") || "";

  const [veiculos, setVeiculos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [resultado, setResultado] = useState(null);

  // Form state
  const [veiculoSel, setVeiculoSel] = useState(preselect);
  const [km, setKm] = useState("");
  const [dataOcorrencia, setDataOcorrencia] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [sistema, setSistema] = useState("");
  const [sintomas, setSintomas] = useState([]);
  const [descricao, setDescricao] = useState("");
  const [severidade, setSeveridade] = useState("");

  useEffect(() => {
    fetchVeiculos().then((v) => {
      setVeiculos(v);
      // Preencher km se veículo pré-selecionado
      if (preselect) {
        const found = v.find((x) => String(x.id) === String(preselect));
        if (found) setKm(String(Math.round(found.km_atual)));
      }
    }).finally(() => setLoading(false));
  }, [preselect]);

  // Ao trocar veículo, preencher km
  function handleVeiculoChange(id) {
    setVeiculoSel(id);
    const found = veiculos.find((x) => String(x.id) === id);
    if (found) setKm(String(Math.round(found.km_atual)));
    else setKm("");
  }

  // Ao trocar sistema, limpar sintomas
  function handleSistemaChange(s) {
    setSistema(s === sistema ? "" : s);
    setSintomas([]);
  }

  function toggleSintoma(s) {
    setSintomas((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  }

  const canSubmit =
    veiculoSel && km && sistema && sintomas.length > 0 && descricao.trim() && severidade;

  async function handleSubmit() {
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      const res = await criarOcorrencia({
        veiculo_id: Number(veiculoSel),
        sistema,
        sintomas,
        descricao: descricao.trim(),
        severidade,
        km_ocorrencia: Number(km),
      });
      setResultado(res);
    } catch (err) {
      alert("Erro ao registrar ocorrência: " + err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="loading">Carregando...</div>;

  // ── Tela de sucesso ────────────────────────────────────────────────────
  if (resultado) {
    const d = resultado.diagnostico;
    const probPct = Math.round(d.probabilidade_falha * 100);
    const circleRadius = 54;
    const circumference = 2 * Math.PI * circleRadius;
    const dashOffset = circumference - (probPct / 100) * circumference;
    const probColor = probPct >= 70 ? "var(--danger)" : probPct >= 50 ? "var(--accent)" : "var(--success)";

    return (
      <div>
        <div className="page-header">
          <h1>✎ Diagnóstico Gerado</h1>
          <p>Ocorrência #{resultado.ocorrencia_id} registrada com sucesso</p>
        </div>

        <div className="grid-2" style={{ marginBottom: 24 }}>
          {/* Probabilidade circular */}
          <div className="box" style={{ display: "flex", alignItems: "center", gap: 32 }}>
            <span className="box-label">Probabilidade de Falha</span>
            <svg width="130" height="130" viewBox="0 0 130 130">
              <circle cx="65" cy="65" r={circleRadius} fill="none" stroke="var(--border)" strokeWidth="8" />
              <circle
                cx="65" cy="65" r={circleRadius} fill="none"
                stroke={probColor} strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                transform="rotate(-90 65 65)"
                style={{ transition: "stroke-dashoffset 0.6s ease" }}
              />
              <text x="65" y="60" textAnchor="middle" fill={probColor} fontSize="28" fontWeight="700" fontFamily="var(--font-mono)">
                {probPct}%
              </text>
              <text x="65" y="80" textAnchor="middle" fill="var(--text-dim)" fontSize="10">
                probabilidade
              </text>
            </svg>
            <div>
              <div style={{ marginBottom: 12 }}>
                <span className="text-dim" style={{ fontSize: "0.72rem", textTransform: "uppercase" }}>Componente</span>
                <p style={{ fontSize: "1.1rem", fontWeight: 600 }}>{d.componente}</p>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span className="text-dim" style={{ fontSize: "0.72rem", textTransform: "uppercase" }}>Horizonte</span>
                <p className="font-mono" style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--accent)" }}>
                  {d.horizonte_dias} dias
                </p>
              </div>
              <span className={`badge ${d.severidade === "critica" ? "critico" : d.severidade === "alta" ? "critico" : "atencao"}`}>
                {d.severidade}
              </span>
            </div>
          </div>

          {/* Recomendação */}
          <div className="box">
            <span className="box-label">Recomendação</span>
            <p style={{ lineHeight: 1.7, marginTop: 4 }}>{d.recomendacao}</p>
            <div style={{ marginTop: 16 }}>
              <span className="text-dim" style={{ fontSize: "0.72rem", textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                Peças Sugeridas
              </span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {d.pecas_sugeridas.map((p, i) => (
                  <span key={i} className="chip">{p}</span>
                ))}
              </div>
            </div>
            <div style={{ marginTop: 16 }}>
              <span className="text-dim" style={{ fontSize: "0.72rem", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
                Economia Estimada
              </span>
              <span className="font-mono text-success" style={{ fontSize: "1.1rem", fontWeight: 600 }}>
                {Number(d.economia_estimada).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
              </span>
            </div>
          </div>
        </div>

        {/* Sintomas correlacionados */}
        <div className="box" style={{ marginBottom: 24 }}>
          <span className="box-label">Sintomas Correlacionados</span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
            {d.sintomas_correlacionados.map((s, i) => (
              <span key={i} className="chip" style={{ background: "var(--accent-dim)", borderColor: "var(--accent)", color: "var(--accent)" }}>
                {s}
              </span>
            ))}
          </div>
          <p className="text-dim" style={{ fontSize: "0.78rem", marginTop: 12 }}>{d.base_historica}</p>
        </div>

        {/* JSON da resposta mock */}
        <div className="box">
          <span className="box-label">Resposta do Modelo ({d.modelo_versao})</span>
          <pre style={{
            background: "var(--bg)",
            padding: 16,
            borderRadius: "var(--radius-sm)",
            fontSize: "0.78rem",
            fontFamily: "var(--font-mono)",
            color: "var(--text-muted)",
            overflowX: "auto",
            marginTop: 4,
            lineHeight: 1.6,
          }}>
            {JSON.stringify(d, null, 2)}
          </pre>
        </div>

        <button
          className="btn btn-secondary mt-4"
          onClick={() => setResultado(null)}
        >
          ← Registrar outra ocorrência
        </button>
      </div>
    );
  }

  // ── Formulário ─────────────────────────────────────────────────────────
  return (
    <div>
      <div className="page-header">
        <h1>✎ Registro de Ocorrência</h1>
        <p>Registre um problema e receba um diagnóstico preditivo baseado em IA</p>
      </div>

      {/* Identificação */}
      <div className="box" style={{ marginBottom: 20 }}>
        <span className="box-label">Identificação</span>
        <div className="grid-3" style={{ marginTop: 4 }}>
          <div className="form-group">
            <label className="form-label">Veículo</label>
            <select
              className="form-select"
              value={veiculoSel}
              onChange={(e) => handleVeiculoChange(e.target.value)}
            >
              <option value="">Selecione...</option>
              {veiculos.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.placa} — {v.modelo}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Quilometragem</label>
            <input
              className="form-input"
              type="number"
              placeholder="km atual"
              value={km}
              onChange={(e) => setKm(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Data</label>
            <input
              className="form-input"
              type="date"
              value={dataOcorrencia}
              onChange={(e) => setDataOcorrencia(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Sistema Afetado */}
      <div className="box" style={{ marginBottom: 20 }}>
        <span className="box-label">Sistema Afetado</span>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 4 }}>
          {SISTEMAS.map((s) => {
            const active = sistema === s;
            return (
              <button
                key={s}
                onClick={() => handleSistemaChange(s)}
                style={{
                  padding: "10px 20px",
                  borderRadius: "var(--radius-sm)",
                  border: active ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                  background: active ? "var(--accent-dim)" : "var(--surface-alt)",
                  color: active ? "var(--accent)" : "var(--text-muted)",
                  fontWeight: active ? 600 : 500,
                  fontSize: "0.85rem",
                  cursor: "pointer",
                  fontFamily: "var(--font-sans)",
                  transition: "all 0.15s ease",
                }}
              >
                {s}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sintomas — condicional */}
      {sistema && (
        <div className="box" style={{ marginBottom: 20 }}>
          <span className="box-label">Sintomas — {sistema}</span>
          <p className="text-dim" style={{ fontSize: "0.75rem", fontStyle: "italic", marginTop: 4, marginBottom: 12 }}>
            Formulário condicional — selecione os sintomas observados
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {SINTOMAS_POR_SISTEMA[sistema].map((s) => {
              const checked = sintomas.includes(s);
              return (
                <label
                  key={s}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "10px 14px",
                    borderRadius: "var(--radius-sm)",
                    border: checked ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                    background: checked ? "var(--accent-dim)" : "transparent",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleSintoma(s)}
                    style={{ display: "none" }}
                  />
                  <span style={{
                    width: 18,
                    height: 18,
                    borderRadius: 4,
                    border: checked ? "2px solid var(--accent)" : "2px solid var(--border)",
                    background: checked ? "var(--accent)" : "transparent",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    fontSize: "0.7rem",
                    color: "#000",
                    fontWeight: 700,
                  }}>
                    {checked && "✓"}
                  </span>
                  <span style={{
                    fontSize: "0.85rem",
                    color: checked ? "var(--accent)" : "var(--text-muted)",
                    fontWeight: checked ? 600 : 400,
                  }}>
                    {s}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* Detalhes */}
      <div className="box" style={{ marginBottom: 24 }}>
        <span className="box-label">Detalhes</span>
        <div className="form-group" style={{ marginTop: 4, marginBottom: 16 }}>
          <label className="form-label">Descrição</label>
          <textarea
            className="form-textarea"
            rows={4}
            placeholder="Descreva o problema observado, contexto (carga, rota, clima), quando começou..."
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
          />
        </div>
        <div>
          <label className="form-label" style={{ marginBottom: 8, display: "block" }}>Severidade</label>
          <div style={{ display: "flex", gap: 8 }}>
            {SEVERIDADES.map((s) => {
              const active = severidade === s;
              const colors = sevColor(s);
              return (
                <button
                  key={s}
                  onClick={() => setSeveridade(s)}
                  style={{
                    padding: "8px 18px",
                    borderRadius: "var(--radius-sm)",
                    border: active ? `1.5px solid ${colors.border}` : "1px solid var(--border)",
                    background: active ? colors.bg : "transparent",
                    color: active ? colors.text : "var(--text-dim)",
                    fontWeight: active ? 600 : 500,
                    fontSize: "0.82rem",
                    cursor: "pointer",
                    fontFamily: "var(--font-sans)",
                    transition: "all 0.15s ease",
                  }}
                >
                  {sevLabel(s)}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Submit */}
      <button
        className="btn btn-primary"
        disabled={!canSubmit || submitting}
        onClick={handleSubmit}
        style={{ width: "100%", padding: "14px 0", fontSize: "0.95rem" }}
      >
        {submitting ? "Analisando..." : "Enviar Ocorrência → Gerar Diagnóstico IA"}
      </button>

      {!canSubmit && veiculoSel && (
        <p className="text-dim" style={{ textAlign: "center", marginTop: 8, fontSize: "0.75rem" }}>
          Preencha todos os campos: veículo, km, sistema, pelo menos 1 sintoma, descrição e severidade
        </p>
      )}
    </div>
  );
}
