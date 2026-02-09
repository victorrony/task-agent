"""
FINANCE TOOLS - Gestão de Contas, Transações e Portfólio
=======================================================
Centraliza todas as operações de leitura e escrita financeira.
"""

from langchain_core.tools import tool
from datetime import datetime, timedelta
from contextvars import ContextVar
from ..db import get_db_connection
from ..logic import FinancialAdvisor

# ═══════════════════════════════════════════════════════════
# PEÇA 1: GESTÃO DE CONTEXTO (MULTI-USER)
# ═══════════════════════════════════════════════════════════
USER_ID_CTX: ContextVar[int] = ContextVar("user_id", default=1)

def set_user_id(user_id: int):
    """Define o ID do utilizador ativo para esta thread/sessão."""
    USER_ID_CTX.set(user_id)

def get_current_user_id() -> int:
    """Retorna o ID do utilizador ativo nesta thread/sessão."""
    return USER_ID_CTX.get()

def log_tool_action(action: str, details: str):
    """Regista uma ação de ferramenta num ficheiro de log local (Auditoria L4 Simples)."""
    uid = get_current_user_id()
    try:
        with open("tool_audit_logs.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | USER {uid} | {action} | {details}\n")
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════
# PEÇA 2: TOOLS DE CONTA E TRANSAÇÕES
# ═══════════════════════════════════════════════════════════

@tool
def get_account_balance() -> str:
    """Consulta o saldo atual da conta bancária (somente leitura)."""
    log_tool_action("GET_BALANCE", "Acesso ao saldo")
    try:
        with get_db_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            row = conn.execute(
                "SELECT balance, currency, updated_at FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                (get_current_user_id(),)
            ).fetchone()

        if not row: return "Nenhum saldo registrado."
        return f"Saldo atual: {row['currency']} {row['balance']:,.2f} (atualizado em {row['updated_at']})"
    except Exception as e:
        return f"Erro ao consultar saldo: {str(e)}"

@tool
def add_transaction(amount: float, transaction_type: str, description: str, category: str = "outros", date: str = None) -> str:
    """
    Registra uma nova transação financeira.
    
    Args:
        amount: Valor positivo.
        transaction_type: 'entrada' ou 'saida'.
        description: Breve descrição.
        category: Categoria (ex: alimentacao, lazer, saude, divida).
        date: Data no formato YYYY-MM-DD (opcional).
    """
    log_tool_action("ADD_TRANSACTION", f"{transaction_type}: {amount} Cat: {category}")
    try:
        uid = get_current_user_id()
        if transaction_type not in ['entrada', 'saida']: return "Erro: tipo deve ser 'entrada' ou 'saida'."
        trans_date = date or datetime.now().strftime("%Y-%m-%d")

        with get_db_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()

            # 1. Verifica Limites (Guardrail para Saídas)
            if transaction_type == 'saida':
                limit_row = cursor.execute(
                    "SELECT monthly_limit, is_hard_limit FROM spending_limits WHERE user_id = ? AND LOWER(category) = LOWER(?)",
                    (uid, category)
                ).fetchone()
                
                if limit_row:
                    first_day = datetime.now().replace(day=1).strftime("%Y-%m-%d")
                    spent_row = cursor.execute(
                        "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'saida' AND LOWER(category) = LOWER(?) AND date >= ?",
                        (uid, category, first_day)
                    ).fetchone()
                    total_spent = (spent_row['SUM(amount)'] or 0) + amount
                    
                    if limit_row['is_hard_limit'] and total_spent > limit_row['monthly_limit']:
                        return f"❌ BLOQUEADO: Limite RÍGIDO de R$ {limit_row['monthly_limit']:.2f} para '{category}' excedido."

            # 2. Calcula Novo Saldo
            bal_row = cursor.execute(
                "SELECT balance FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                (uid,)
            ).fetchone()
            current_balance = bal_row['balance'] if bal_row else 0
            new_balance = current_balance + amount if transaction_type == 'entrada' else current_balance - amount

            # 3. Persiste
            cursor.execute(
                "INSERT INTO transactions (user_id, date, description, amount, type, category, balance_after) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (uid, trans_date, description, amount, transaction_type, category, new_balance)
            )
            cursor.execute("INSERT INTO account_balance (user_id, balance) VALUES (?, ?)", (uid, new_balance))
            conn.commit()
            
        return f"✅ Transação registada. Novo saldo: CVE {new_balance:,.2f}"
    except Exception as e:
        return f"Erro ao registar transação: {str(e)}"

# ═══════════════════════════════════════════════════════════
# PEÇA 3: TOOLS DE INVESTIMENTO E PORTFÓLIO
# ═══════════════════════════════════════════════════════════

@tool
def manage_portfolio(action: str, symbol: str = None, quantity: float = 0, price: float = 0) -> str:
    """Gere o portfólio de ativos (add, remove, list)."""
    log_tool_action("MANAGE_PORTFOLIO", f"{action} Ativo: {symbol}")
    uid = get_current_user_id()
    try:
        with get_db_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            if action == "add":
                conn.execute("INSERT INTO portfolio (user_id, symbol, quantity, purchase_price) VALUES (?, ?, ?, ?)", 
                             (uid, symbol.upper(), quantity, price))
                conn.commit()
                return f"✅ Ativo {symbol} adicionado ao portfólio."
            elif action == "list":
                rows = conn.execute("SELECT symbol, quantity, purchase_price FROM portfolio WHERE user_id = ?", (uid,)).fetchall()
                if not rows: return "Portfólio vazio."
                res = "📊 Seu Portfólio:\n" + "\n".join([f"- {r['symbol']}: {r['quantity']} @ CVE {r['purchase_price']:.2f}" for r in rows])
                return res
        return "Ação inválida."
    except Exception as e:
        return f"Erro no portfólio: {str(e)}"

@tool
def suggest_investments() -> str:
    """
    Gera uma sugestão de alocação estratégica baseada em análise real de saúde financeira.
    Valida reserva de emergência, dívidas e perfil antes de sugerir.
    """
    uid = get_current_user_id()
    advisor = FinancialAdvisor(uid)
    status = advisor.get_user_status()
    
    # Validação de Viabilidade (Regra 0)
    can_invest, reasons = advisor.evaluate_investment_viability(status)
    
    if not can_invest:
        msg = "⚠️ INVESTIMENTO NÃO RECOMENDADO AGORA\n"
        msg += "Motivos:\n" + "\n".join([f"- {r}" for r in reasons])
        msg += "\n💡 Foco Sugerido: Fortalecer reserva e eliminar dívidas (Regra 0)."
        return msg

    # Alocação
    allocation = advisor.get_recommended_allocation(status)
    res = "🎯 PLANO ESTRATÉGICO DE ALOCAÇÃO\n"
    res += f"Perfil: {status['risk_profile'] or 'Automático'}\n"
    res += "-" * 30 + "\n"
    for k, v in allocation.items():
        res += f"{k}: {v}\n"
    return res

# ═══════════════════════════════════════════════════════════
# PEÇA 4: TOOLS DE PERFIL E PREFERÊNCIAS
# ═══════════════════════════════════════════════════════════

@tool
def set_user_preference(key: str, value: str) -> str:
    """Define uma preferência (ex: 'idade', 'perfil_risco') do utilizador."""
    uid = get_current_user_id()
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_preferences (user_id, key, value) VALUES (?, ?, ?)",
                (uid, key.lower(), value.lower())
            )
            conn.commit()
        return f"✅ '{key}' definido como '{value}'."
    except Exception as e:
        return f"Erro: {str(e)}"

@tool
def get_user_profile() -> str:
    """Consulta o perfil e preferências atuais do utilizador."""
    uid = get_current_user_id()
    try:
        with get_db_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            rows = conn.execute("SELECT key, value FROM user_preferences WHERE user_id = ?", (uid,)).fetchall()
        
        if not rows: return "Perfil incompleto."
        res = "📋 PERFIL:\n" + "\n".join([f"- {r['key'].capitalize()}: {r['value']}" for r in rows])
        return res
    except Exception as e:
        return f"Erro: {str(e)}"
