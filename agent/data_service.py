"""
Data Service for FinanceAgent Pro
Handles all database queries for the UI with multi-user support.
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from functools import lru_cache

DB_PATH = "agent_data.db"

# Cache para evitar consultas repetitivas
STATS_CACHE = {}

def clear_cache(user_id=None):
    """Limpa o cache do serviço."""
    global STATS_CACHE
    if user_id:
        if user_id in STATS_CACHE:
            del STATS_CACHE[user_id]
    else:
        STATS_CACHE = {}

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_quick_stats(user_id=1):
    """Retorna estatísticas rápidas formatadas para os cartões de um usuário específico. Usa cache."""
    global STATS_CACHE
    if user_id in STATS_CACHE:
        return STATS_CACHE[user_id]
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Saldo Atual
        cursor.execute("SELECT balance, currency FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        balance = row[0] if row else 0
        currency = row[1] if row else "R$"

        # Entradas e Saídas do mês
        cursor.execute("""
            SELECT type, COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE user_id = ? AND date >= date('now', 'start of month')
            GROUP BY type
        """, (user_id,))
        summaries = dict(cursor.fetchall())
        monthly_income = summaries.get('entrada', 0)
        monthly_expenses = summaries.get('saida', 0)

        # Metas ativas
        cursor.execute("SELECT COUNT(*) FROM financial_goals WHERE user_id = ? AND status = 'ativo'", (user_id,))
        goals_count = cursor.fetchone()[0]

        # Alertas de gastos
        cursor.execute("SELECT category, monthly_limit FROM spending_limits WHERE user_id = ?", (user_id,))
        limits = cursor.fetchall()
        alert_msg = "Sist. OK"
        if limits:
            over_limit = False
            warning_limit = False
            for cat, lim in limits:
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM transactions 
                    WHERE user_id = ? AND type = 'saida' AND LOWER(category) = LOWER(?) 
                    AND date >= date('now', 'start of month')
                """, (user_id, cat))
                spent = cursor.fetchone()[0]
                if spent > lim:
                    over_limit = True
                    break
                elif spent > lim * 0.8:
                    warning_limit = True
            
            if over_limit:
                alert_msg = "🚨 Alerta"
            elif warning_limit:
                alert_msg = "⚠️ Limite"

        conn.close()

        balance_val = f"{currency} {balance:,.2f}"
        profit_val = f"{currency} {monthly_income - monthly_expenses:,.2f}"
        
        result = (balance_val, profit_val, str(goals_count), alert_msg)
        STATS_CACHE[user_id] = result
        return result
    except Exception as e:
        print(f"Erro stats: {e}")
        return "Erro", "Erro", "Erro", "Erro"

def get_expense_chart(user_id=1):
    """Gera gráfico de pizza de gastos por categoria para o usuário."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("""
            SELECT category, SUM(amount) as total 
            FROM transactions 
            WHERE user_id = ? AND type = 'saida' 
            GROUP BY category
        """, conn, params=(user_id,))
        conn.close()

        if df.empty:
            return go.Figure().update_layout(title="Sem dados de gastos")

        fig = go.Figure(data=[go.Pie(
            labels=df['category'], 
            values=df['total'], 
            hole=.4,
            marker=dict(colors=['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#6b7280'])
        )])
        fig.update_layout(
            title="Distribuição de Gastos",
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#374151")
        )
        return fig
    except Exception as e:
        print(f"Erro chart pie: {e}")
        return go.Figure()

def get_balance_history_chart(user_id=1):
    """Gera gráfico de linha da evolução do saldo para o usuário."""
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
            return go.Figure().update_layout(title="Sem histórico de saldo")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'], 
            y=df['balance'], 
            mode='lines+markers', 
            name='Saldo',
            line=dict(color='#10b981', width=3),
            marker=dict(size=8, color='#059669'),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        fig.update_layout(
            title="Evolução do Saldo",
            xaxis_title="Data",
            yaxis_title="Saldo (BRL)",
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#374151")
        )
        return fig
    except Exception as e:
        print(f"Erro chart line: {e}")
        return go.Figure()

def get_transactions_df(user_id=1):
    """Retorna o histórico de transações como DataFrame para o usuário."""
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
    except Exception as e:
        print(f"Erro df: {e}")
        return pd.DataFrame()

def get_users():
    """Retorna lista de usuários cadastrados."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT id, name FROM users", conn)
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro get_users: {e}")
        return [{"id": 1, "name": "Usuário Principal"}]

def get_goals_progress(user_id=1):
    """Retorna metas com progresso para barras visuais."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, target_amount, current_amount, priority, status 
            FROM financial_goals 
            WHERE user_id = ? AND status = 'ativo'
            ORDER BY priority DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        goals = []
        for name, target, current, priority, status in rows:
            progress = (current / target * 100) if target > 0 else 0
            goals.append({
                "name": name,
                "target": target,
                "current": current,
                "percent": min(100, progress),
                "priority": priority
            })
        return goals
    except Exception as e:
        print(f"Erro get_goals: {e}")
        return []
