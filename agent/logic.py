"""
FINANCIAL LOGIC ENGINE - O Cérebro Financeiro do FinanceAgent Pro
================================================================
Implementa as regras de negócio para alocação e aconselhamento.
"""

from datetime import datetime
from .db import get_db_connection

class FinancialAdvisor:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_user_status(self):
        """Coleta dados necessários para avaliar as regras."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Saldo e Reserva
        row_bal = cursor.execute("SELECT balance FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (self.user_id,)).fetchone()
        current_balance = row_bal['balance'] if row_bal else 0

        # 2. Despesas médias (últimos 90 dias) - CÁLCULO REAL
        # Buscamos a data de 90 dias atrás
        from datetime import timedelta
        ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        row_exp = cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'saida' AND date >= ?", 
            (self.user_id, ninety_days_ago)
        ).fetchone()
        total_exp = row_exp[0] or 0
        monthly_expenses = total_exp / 3 if total_exp > 0 else 1000 # Fallback se não houver dados

        # 3. Metas (Reserva de Emergência)
        row_goal = cursor.execute("SELECT current_amount, target_amount FROM financial_goals WHERE user_id = ? AND name LIKE '%Emergencia%'", (self.user_id,)).fetchone()
        reserve_target = row_goal['target_amount'] if row_goal else (monthly_expenses * 6)
        current_reserve = row_goal['current_amount'] if row_goal else current_balance

        # 4. Taxa de Poupança (último mês) - CÁLCULO REAL
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        income_row = cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'entrada' AND date >= ?", (self.user_id, thirty_days_ago)).fetchone()
        expense_row = cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'saida' AND date >= ?", (self.user_id, thirty_days_ago)).fetchone()
        
        total_income = income_row[0] or 0
        total_expense = expense_row[0] or 0
        savings = total_income - total_expense
        savings_rate = savings / total_income if total_income > 0 else 0

        # 5. Dívidas
        row_debt = cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = 'divida' AND type = 'saida' AND date >= ?", 
                                 (self.user_id, ninety_days_ago)).fetchone()
        has_debt = (row_debt[0] or 0) > 0

        # 6. Preferências (Idade, Perfil)
        rows_pref = cursor.execute("SELECT key, value FROM user_preferences WHERE user_id = ?", (self.user_id,)).fetchall()
        prefs = {r['key']: r['value'] for r in rows_pref}
        
        conn.close()
        
        return {
            "balance": current_balance,
            "monthly_expenses": monthly_expenses,
            "current_reserve": current_reserve,
            "reserve_months": current_reserve / monthly_expenses if monthly_expenses > 0 else 0,
            "has_debt": has_debt,
            "savings_rate": savings_rate,
            "age": int(prefs.get("idade", 30)),
            "risk_profile": prefs.get("perfil_risco", None),
            "is_new_user": len(prefs) == 0
        }

    def evaluate_investment_viability(self, status):
        """Regra 0 e 1: Verifica se o utilizador pode investir."""
        reasons = []
        if status["reserve_months"] < 6:
            reasons.append(f"Reserva de emergência insuficiente ({status['reserve_months']:.1f}/6 meses)")
        if status["has_debt"]:
            reasons.append("Existem dívidas ativas que devem ser priorizadas")
        if status["savings_rate"] < 0.10:
            reasons.append(f"Taxa de poupança muito baixa ({status['savings_rate']*100:.1f}% < 10%)")
        
        return len(reasons) == 0, reasons

    def get_recommended_allocation(self, status):
        """Regra 2 e 3: Define a alocação baseada no perfil e idade."""
        # Regra 2: Perfil Automático
        profile = status["risk_profile"]
        if not profile:
            if status["age"] < 35: profile = "moderado"
            elif status["age"] <= 50: profile = "moderado-conservador"
            else: profile = "conservador"

        # Regra 3: Alocação Padrão (Exemplo Moderado)
        if profile == "moderado":
            return {
                "Consertador/Poupança (CVE)": "40%",
                "Investimentos Estáveis (Baixo Risco)": "30%",
                "Investimentos Globais (ETFs/Ações)": "20%",
                "Ativos Alternativos (Cripto/Inovação)": "10%"
            }
        # ... outros perfis omitidos para brevidade ...
        return {"Sugestão": f"Perfil {profile} identificado. Contacte suporte para detalhes."}

    def validate_risk_limits(self, portfolio_summary):
        """Regra 6: Hard Limits."""
        # portfolio_summary ex: {"crypto": 0.12, "single_asset": 0.05}
        alerts = []
        if portfolio_summary.get("crypto", 0) > 0.10:
            alerts.append("ALERTA: Exposição em Cripto acima do limite (10%)")
        return alerts
