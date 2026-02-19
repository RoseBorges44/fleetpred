#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "Encerrando servidores..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  echo "Pronto."
  exit 0
}

trap cleanup SIGINT SIGTERM

echo "========================================="
echo "  🚛 FleetPred — Manutenção Preditiva"
echo "========================================="
echo ""

# ── Backend ──────────────────────────────────
echo "[backend] Instalando dependências..."
pip install -r "$ROOT/backend/requirements.txt" --quiet

echo "[backend] Iniciando uvicorn na porta 8000..."
cd "$ROOT/backend"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd "$ROOT"

# ── Frontend ─────────────────────────────────
echo "[frontend] Instalando dependências..."
cd "$ROOT/frontend"
npm install --silent

echo "[frontend] Iniciando Vite dev server..."
npm run dev &
FRONTEND_PID=$!
cd "$ROOT"

echo ""
echo "========================================="
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API docs: http://localhost:8000/docs"
echo "========================================="
echo "  Ctrl+C para encerrar os dois servidores"
echo "========================================="
echo ""

wait
