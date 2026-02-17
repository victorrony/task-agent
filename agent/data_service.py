"""
Data Service for FinanceAgent Pro
Handles all database queries for the UI with multi-user support.
Actively implements Cache with TTL and standardized response formats.
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from .logic import FinancialAdvisor

DB_PATH = "agent_data.db"

# ═══════════════════════════════════════════════════════════
# PEÇA 1: SISTEMA DE CACHE COM TTL
# ═══════════════════════════════════════════════════════════
STATS_CACHE = {}
CACHE_TTL_SECONDS = 30  # Cache curto para garantir fluidez sem dados obsoletos

def _get_from_cache(user_id, key):
    """Recupera dado do cache se não estiver expirado."""
    if user_id in STATS_CACHE and key in STATS_CACHE[user_id]:
        entry = STATS_CACHE[user_id][key]
        if datetime.now() - entry['timestamp'] < timedelta(seconds=CACHE_TTL_SECONDS):
            return entry['data']
    return None

def _save_to_cache(user_id, key, data):
    """Guarda dado no cache com timestamp."""
    if user_id not in STATS_CACHE:
        STATS_CACHE[user_id] = {}
    STATS_CACHE[user_id][key] = {
        "data": data,
        "timestamp": datetime.now()
    }

def clear_cache(user_id=None):
    """Limpa o cache do serviço."""
    global STATS_CACHE
    if user_id:
        STATS_CACHE.pop(user_id, None)
    else:
        STATS_CACHE = {}

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# ═══════════════════════════════════════════════════════════
# PEÇA 2: SERVIÇOS DE LEITURA (DATA FETCHING)
# ═══════════════════════════════════════════════════════════

def get_quick_stats(user_id=1):
    """
    Retorna métricas rápidas. 
    Nota: A decisão de 'Alerta' é delegada ao FinancialAdvisor (logic.py)
    para manter consistência entre UI e Agente.
    """
    cached = _get_from_cache(user_id, "quick_stats")
    if cached: return cached
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Saldo Real
        cursor.execute("SELECT balance, currency FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        balance = row[0] if row else 0
        currency = row[1] if row else "CVE"

        # 2. Fluxo Mensal (Entradas vs Saídas)
        cursor.execute("""
            SELECT type, COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE user_id = ? AND date >= date('now', 'start of month')
            GROUP BY type
        """, (user_id,))
        summaries = dict(cursor.fetchall())
        income = summaries.get('entrada', 0)
        expenses = summaries.get('saida', 0)
        profit = income - expenses

        # 3. Metas Ativas
        cursor.execute("SELECT COUNT(*) FROM financial_goals WHERE user_id = ? AND status = 'ativo'", (user_id,))
        goals_count = cursor.fetchone()[0]

        # 4. Status de Saúde (Delegado à Lógica do Agente)
        advisor = FinancialAdvisor(user_id)
        status_health = advisor.get_user_status()
        
        status_msg = "Sist. OK"
        if status_health['reserve_months'] < 6:
            status_msg = "⚠️ Reserva"
        if status_health['has_debt']:
            status_msg = "🚨 Dívida"

        conn.close()

        # Resposta Padronizada (Dicionário)
        result = {
            "balance": f"{currency} {balance:,.2f}",
            "profit": f"{currency} {profit:,.2f}",
            "reserve": f"{currency} {status_health['current_reserve']:,.2f}",
            "goals": str(goals_count),
            "status": status_msg,
            "raw_balance": balance
        }
        
        _save_to_cache(user_id, "quick_stats", result)
        return result
        
    except Exception as e:
        print(f"❌ Erro DataService (stats): {e}")
        return {"balance": "---", "profit": "---", "goals": "0", "status": "Erro"}

def get_expense_chart(user_id=1):
    """Prepara dados para o gráfico de pizza de categorias."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("""
            SELECT category, SUM(amount) as total 
            FROM transactions 
            WHERE user_id = ? AND type = 'saida' 
            AND date >= date('now', '-90 days')
            GROUP BY category
        """, conn, params=(user_id,))
        conn.close()

        if df.empty:
            return go.Figure().update_layout(title="Sem dados (90d)")

        fig = go.Figure(data=[go.Pie(
            labels=df['category'], 
            values=df['total'], 
            hole=.4,
            marker=dict(colors=['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#6b7280'])
        )])
        fig.update_layout(
            title="Distribuição de Gastos (90d)",
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#374151")
        )
        return fig
    except Exception as e:
        print(f"❌ Erro DataService (pie): {e}")
        return go.Figure()

def get_balance_history_chart(user_id=1):
    """Prepara dados para evolução temporal do saldo."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("""
            SELECT date, balance_after as balance 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date ASC
        """, conn, params=(user_id,))
        conn.close()

        if df.empty:
            return go.Figure().update_layout(title="Sem histórico")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'], 
            y=df['balance'], 
            mode='lines', 
            name='Saldo',
            line=dict(color='#10b981', width=3),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        fig.update_layout(
            title="Evolução do Património",
            xaxis_title="Tempo",
            yaxis_title="CVE",
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#374151")
        )
        return fig
    except Exception as e:
        print(f"❌ Erro DataService (line): {e}")
        return go.Figure()

def get_transactions_df(user_id=1):
    """Fetch puro de transações para a tabela UI."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("""
            SELECT date as Data, description as Descrição, amount as Valor, type as Tipo, category as Categoria 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC
        """, conn, params=(user_id,))
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def get_users():
    """Listagem de utilizadores para o seletor de perfil."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT id, name FROM users", conn)
        conn.close()
        return df.to_dict('records')
    except Exception:
        return [{"id": 1, "name": "Utilizador Base"}]

def get_expense_categories(user_id=1):
    """Retorna distribuição de gastos por categoria (últimos 90 dias)."""
    cached = _get_from_cache(user_id, "expense_categories")
    if cached: return cached

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? AND type = 'saida'
            AND date >= date('now', '-90 days')
            GROUP BY category
            ORDER BY total DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        categories = []
        for name, total in rows:
            categories.append({
                "name": name or "Outros",
                "value": round(total, 2)
            })

        _save_to_cache(user_id, "expense_categories", categories)
        return categories
    except Exception as e:
        print(f"❌ Erro DataService (categories): {e}")
        return []


def get_goals_progress(user_id=1):
    """Calcula progresso de metas (Apenas leitura e formatação)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, target_amount, current_amount, priority 
            FROM financial_goals 
            WHERE user_id = ? AND status = 'ativo'
            ORDER BY priority DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        goals = []
        for name, target, current, priority in rows:
            progress = (current / target * 100) if target > 0 else 0
            goals.append({
                "name": name,
                "target": target,
                "current": current,
                "percent": min(100, progress),
                "priority": priority
            })
        return goals
    except Exception:
        return []
