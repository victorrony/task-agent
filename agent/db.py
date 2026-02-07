"""
DATABASE LAYER - Gerenciamento de Dados SQLite
==============================================
"""

import sqlite3
import os

DB_PATH = "agent_data.db"

def get_db_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa todas as tabelas do sistema."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES (1, 'Usuário Principal')")

    # 2. Notas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            content TEXT,
            category TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Transações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            date DATE NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('entrada', 'saida')) NOT NULL,
            category TEXT,
            balance_after REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Saldo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_balance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            balance REAL NOT NULL,
            currency TEXT DEFAULT 'BRL',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Portfolio
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            asset_type TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date DATE,
            current_price REAL,
            last_update DATETIME,
            notes TEXT
        )
    """)

    # 6. Preferências
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'geral',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key)
        )
    """)

    # 7. Metas Financeiras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline DATE,
            priority TEXT CHECK(priority IN ('alta', 'media', 'baixa')) DEFAULT 'media',
            status TEXT CHECK(status IN ('ativo', 'concluido', 'cancelado')) DEFAULT 'ativo',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. Limites de Gastos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spending_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            is_hard_limit INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category)
        )
    """)

    # 9. Histórico de Chat (Memória do Agente)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            session_id TEXT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_json TEXT, -- Serialized LangChain message
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 10. Log de Auditoria (Decisões do Agente)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            session_id TEXT,
            task TEXT,
            decision_process TEXT,
            tools_used TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 11. Cache de API

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de dados inicializada com sucesso.")
