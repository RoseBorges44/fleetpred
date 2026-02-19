import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "fleetpred.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            km_atual REAL NOT NULL,
            motor TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('ok', 'atencao', 'critico')),
            ultimo_oleo_km REAL,
            data_cadastro TEXT NOT NULL DEFAULT (date('now')),
            ativo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS componentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            saude_pct INTEGER NOT NULL CHECK (saude_pct >= 0 AND saude_pct <= 100),
            ultima_inspecao TEXT,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        );

        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            data_ocorrencia TEXT NOT NULL,
            sistema TEXT NOT NULL,
            sintomas TEXT,
            descricao TEXT,
            severidade TEXT NOT NULL CHECK (severidade IN ('baixa', 'media', 'alta', 'critica')),
            km_ocorrencia REAL,
            status TEXT NOT NULL DEFAULT 'aberta' CHECK (status IN ('aberta', 'em_analise', 'resolvida')),
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        );

        CREATE TABLE IF NOT EXISTS manutencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('preventiva', 'preditiva', 'corretiva')),
            descricao TEXT,
            data_realizada TEXT,
            data_agendada TEXT,
            km_realizada REAL,
            custo REAL,
            status TEXT NOT NULL DEFAULT 'agendada' CHECK (status IN ('agendada', 'em_andamento', 'concluida', 'cancelada')),
            pecas TEXT,
            observacoes TEXT,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        );

        CREATE TABLE IF NOT EXISTS diagnosticos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ocorrencia_id INTEGER NOT NULL,
            veiculo_id INTEGER NOT NULL,
            data_diagnostico TEXT NOT NULL DEFAULT (datetime('now')),
            componente TEXT NOT NULL,
            probabilidade_falha REAL NOT NULL,
            horizonte_dias INTEGER NOT NULL,
            severidade TEXT NOT NULL,
            sintomas_correlacionados TEXT,
            recomendacao TEXT,
            pecas_sugeridas TEXT,
            economia_estimada REAL,
            base_historica TEXT,
            FOREIGN KEY (ocorrencia_id) REFERENCES ocorrencias(id),
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        );

        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            diagnostico_id INTEGER,
            tipo TEXT NOT NULL CHECK (tipo IN ('critico', 'atencao', 'info')),
            mensagem TEXT NOT NULL,
            data_criacao TEXT NOT NULL DEFAULT (datetime('now')),
            lido INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id),
            FOREIGN KEY (diagnostico_id) REFERENCES diagnosticos(id)
        );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso.")
