const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Erro ${res.status}`);
  }
  return res.json();
}

// ── Veículos ──────────────────────────────────────────────────────────────
export function fetchDashboardStats() {
  return request("/veiculos/stats/dashboard");
}

export function fetchVeiculos() {
  return request("/veiculos/");
}

export function fetchVeiculo(id) {
  return request(`/veiculos/${id}`);
}

// ── Ocorrências ───────────────────────────────────────────────────────────
export function fetchOcorrencias() {
  return request("/ocorrencias/");
}

export function criarOcorrencia(data) {
  return request("/ocorrencias/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Manutenções ───────────────────────────────────────────────────────────
export function fetchManutencoes() {
  return request("/manutencoes/agendadas");
}

export function fetchManutencoesPrioridade() {
  return request("/manutencoes/prioridade");
}

// ── Relatórios ────────────────────────────────────────────────────────────
export function fetchRelatorioCustos() {
  return request("/relatorios/custos");
}

export function fetchRelatorioDisponibilidade() {
  return request("/relatorios/disponibilidade");
}

export function fetchRelatorioTendencia() {
  return request("/relatorios/tendencia");
}

// ── Alertas ───────────────────────────────────────────────────────────────
export function fetchAlertas(lido) {
  const query = lido !== undefined ? `?lido=${lido}` : "";
  return request(`/alertas/${query}`);
}

export function marcarAlertaLido(id) {
  return request(`/alertas/${id}/lido`, { method: "PUT" });
}

export function fetchDiagnostico(id) {
  return request(`/alertas/diagnostico/${id}`);
}
