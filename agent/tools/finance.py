"""
FINANCE TOOLS - Gestão de Contas e Transações
"""

from langchain_core.tools import tool
from datetime import datetime, timedelta
import sqlite3
from ..db import get_db_connection

from contextvars import ContextVar

# Global context for current user (thread-safe)
USER_ID_CTX: ContextVar[int] = ContextVar("user_id", default=1)

def set_user_id(user_id: int):
    USER_ID_CTX.set(user_id)

def get_current_user_id() -> int:
    return USER_ID_CTX.get()

@tool
def get_account_balance() -> str:
    """Consulta o saldo atual da conta bancária (somente leitura)."""
    try:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT balance, currency, updated_at FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (get_current_user_id(),)
        ).fetchone()
        conn.close()

        if not row: return "Nenhum saldo registrado."
        return f"Saldo atual: {row['currency']} {row['balance']:,.2f} (atualizado em {row['updated_at']})"
    except Exception as e:
        return f"Erro ao consultar saldo: {str(e)}"

@tool
def add_transaction(amount: float, transaction_type: str, description: str, category: str = "outros", date: str = None) -> str:
    """
    Registra uma nova transação.
    
    Args:
        amount: Valor (positivo)
        transaction_type: 'entrada' ou 'saida'
        description: Descrição
        category: Categoria (ex: alimentacao, lazer)
        date: YYYY-MM-DD (opcional)
    """
    try:
        if transaction_type not in ['entrada', 'saida']: return "Erro: tipo inválido."
        trans_date = date or datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check Risk Limits
        if transaction_type == 'saida':
            limit_row = cursor.execute(
                "SELECT monthly_limit, is_hard_limit FROM spending_limits WHERE user_id = ? AND LOWER(category) = LOWER(?)",
                (get_current_user_id(), category)
            ).fetchone()
            
            if limit_row:
                first_day = datetime.now().replace(day=1).strftime("%Y-%m-%d")
                spent_row = cursor.execute(
                    "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'saida' AND LOWER(category) = LOWER(?) AND date >= ?",
                    (get_current_user_id(), category, first_day)
                ).fetchone()
                total_spent = (spent_row[0] or 0) + amount
                
                if limit_row['is_hard_limit'] and total_spent > limit_row['monthly_limit']:
                    conn.close()
                    return f"❌ BLOQUEADO: Esta transação excede o limite RÍGIDO de R$ {limit_row['monthly_limit']:.2f} para '{category}'."

        # Get Current Balance
        bal_row = cursor.execute(
            "SELECT balance FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (get_current_user_id(),)
        ).fetchone()
        current_balance = bal_row['balance'] if bal_row else 0
        new_balance = current_balance + amount if transaction_type == 'entrada' else current_balance - amount

        # Save
        cursor.execute(
            "INSERT INTO transactions (user_id, date, description, amount, type, category, balance_after) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (get_current_user_id(), trans_date, description, amount, transaction_type, category, new_balance)
        )
        cursor.execute("INSERT INTO account_balance (user_id, balance) VALUES (?, ?)", (get_current_user_id(), new_balance))
        
        conn.commit()
        conn.close()
        return f"✅ Transação registrada. Novo saldo: R$ {new_balance:,.2f}"
    except Exception as e:
        return f"Erro ao registrar transação: {str(e)}"

@tool
def analyze_finances(period_days: int = 30) -> str:
    """Analisa receitas e despesas do período."""
    try:
        conn = get_db_connection()
        start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")
        
        income = conn.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'entrada' AND date >= ?", 
                              (get_current_user_id(), start_date)).fetchone()[0] or 0
        expenses = conn.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'saida' AND date >= ?", 
                               (get_current_user_id(), start_date)).fetchone()[0] or 0
        
        cats = conn.execute("SELECT category, SUM(amount) as total FROM transactions WHERE user_id = ? AND type = 'saida' AND date >= ? GROUP BY category ORDER BY total DESC",
                            (get_current_user_id(), start_date)).fetchall()
        conn.close()

        res = f"Análise ({period_days} dias):\n- Entradas: R$ {income:,.2f}\n- Saídas: R$ {expenses:,.2f}\n\nCategorias:"
        for c in cats:
            res += f"\n  - {c['category']}: R$ {c['total']:,.2f}"
        return res
    except Exception as e:
        return f"Erro na análise: {str(e)}"
