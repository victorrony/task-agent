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
from ..data_service import clear_cache

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
def set_account_balance(balance: float, currency: str = "CVE") -> str:
    """
    Define um novo saldo na conta bancária.

    Args:
        balance: Valor do saldo a ser definido.
        currency: Moeda (padrão: CVE).
    """
    log_tool_action("SET_BALANCE", f"Definir saldo: {currency} {balance}")
    try:
        uid = get_current_user_id()
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO account_balance (user_id, balance, currency) VALUES (?, ?, ?)",
                (uid, balance, currency)
            )
            conn.commit()

        clear_cache(uid)
        return f"✅ Saldo definido: {currency} {balance:,.2f}"
    except Exception as e:
        return f"Erro ao definir saldo: {str(e)}"

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

        clear_cache(uid)
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

# ═══════════════════════════════════════════════════════════
# PEÇA 5: TOOLS DE METAS FINANCEIRAS
# ═══════════════════════════════════════════════════════════

@tool
def manage_goals(action: str, name: str = None, target_amount: float = 0, priority: str = "media", deadline: str = None, amount: float = 0) -> str:
    """
    Gere metas financeiras (create, update, delete, list).

    Args:
        action: 'create', 'update', 'delete' ou 'list'.
        name: Nome da meta (obrigatório para create, update, delete).
        target_amount: Valor objetivo (obrigatório para create).
        priority: Prioridade da meta ('alta', 'media', 'baixa') - padrão 'media'.
        deadline: Data limite no formato YYYY-MM-DD (opcional).
        amount: Valor a adicionar ao progresso (obrigatório para update).
    """
    log_tool_action("MANAGE_GOALS", f"{action} Meta: {name}")
    uid = get_current_user_id()

    try:
        with get_db_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()

            if action == "create":
                if not name or target_amount <= 0:
                    return "❌ Erro: 'name' e 'target_amount' (> 0) são obrigatórios para criar meta."

                if priority.lower() not in ['alta', 'media', 'baixa']:
                    return "❌ Erro: 'priority' deve ser 'alta', 'media' ou 'baixa'."

                cursor.execute(
                    "INSERT INTO financial_goals (user_id, name, target_amount, current_amount, deadline, priority, status) VALUES (?, ?, ?, 0, ?, ?, 'ativo')",
                    (uid, name, target_amount, deadline, priority.lower())
                )
                conn.commit()

                clear_cache(uid)
                deadline_msg = f" até {deadline}" if deadline else ""
                return f"🎯 Meta '{name}' criada com sucesso! Objetivo: CVE {target_amount:,.2f}{deadline_msg} (Prioridade: {priority.lower()})"

            elif action == "update":
                if not name or amount <= 0:
                    return "❌ Erro: 'name' e 'amount' (> 0) são obrigatórios para atualizar progresso."

                # Busca meta ativa
                goal = cursor.execute(
                    "SELECT id, target_amount, current_amount, status FROM financial_goals WHERE user_id = ? AND LOWER(name) = LOWER(?) AND status = 'ativo'",
                    (uid, name)
                ).fetchone()

                if not goal:
                    return f"❌ Meta '{name}' não encontrada ou já concluída/cancelada."

                new_current = goal['current_amount'] + amount
                new_status = 'concluido' if new_current >= goal['target_amount'] else 'ativo'

                cursor.execute(
                    "UPDATE financial_goals SET current_amount = ?, status = ? WHERE id = ?",
                    (new_current, new_status, goal['id'])
                )
                conn.commit()

                clear_cache(uid)
                progress = (new_current / goal['target_amount']) * 100
                if new_status == 'concluido':
                    return f"🎉 PARABÉNS! Meta '{name}' CONCLUÍDA! {new_current:,.2f}/{goal['target_amount']:,.2f} CVE (100%)"
                else:
                    return f"✅ Progresso atualizado para '{name}': {new_current:,.2f}/{goal['target_amount']:,.2f} CVE ({progress:.1f}%)"

            elif action == "delete":
                if not name:
                    return "❌ Erro: 'name' é obrigatório para cancelar meta."

                result = cursor.execute(
                    "UPDATE financial_goals SET status = 'cancelado' WHERE user_id = ? AND LOWER(name) = LOWER(?) AND status = 'ativo'",
                    (uid, name)
                )
                conn.commit()

                if result.rowcount == 0:
                    return f"❌ Meta '{name}' não encontrada ou já concluída/cancelada."

                clear_cache(uid)
                return f"🗑️ Meta '{name}' cancelada com sucesso."

            elif action == "list":
                rows = cursor.execute(
                    "SELECT name, target_amount, current_amount, deadline, priority, status FROM financial_goals WHERE user_id = ? ORDER BY CASE priority WHEN 'alta' THEN 1 WHEN 'media' THEN 2 WHEN 'baixa' THEN 3 END, created_at",
                    (uid,)
                ).fetchall()

                if not rows:
                    return "📋 Nenhuma meta financeira registrada."

                res = "🎯 SUAS METAS FINANCEIRAS:\n" + "="*40 + "\n"
                for r in rows:
                    progress = (r['current_amount'] / r['target_amount']) * 100
                    status_emoji = "✅" if r['status'] == 'concluido' else "🔴" if r['status'] == 'cancelado' else "🔵"
                    priority_emoji = "🔥" if r['priority'] == 'alta' else "⚡" if r['priority'] == 'media' else "💤"
                    deadline_str = f" | Prazo: {r['deadline']}" if r['deadline'] else ""

                    res += f"{status_emoji} {priority_emoji} {r['name']}\n"
                    res += f"   Progresso: {r['current_amount']:,.2f}/{r['target_amount']:,.2f} CVE ({progress:.1f}%){deadline_str}\n"
                    res += f"   Status: {r['status'].capitalize()} | Prioridade: {r['priority'].capitalize()}\n\n"

                return res

            else:
                return "❌ Ação inválida. Use: 'create', 'update', 'delete' ou 'list'."

    except Exception as e:
        return f"❌ Erro ao gerir metas: {str(e)}"
