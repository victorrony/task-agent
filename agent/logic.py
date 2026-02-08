"""
FINANCIAL LOGIC ENGINE - O Cérebro Financeiro do FinanceAgent Pro
================================================================
Implementa as regras de negócio para alocação e aconselhamento profissional.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from .db import get_db_connection

# ═══════════════════════════════════════════════════════════
# PEÇA 1: CONFIGURAÇÃO CENTRAL DE REGRAS (Guardrails)
# ═══════════════════════════════════════════════════════════
FINANCIAL_CONFIG = {
    "min_reserve_months": 6,
    "ideal_reserve_months": 12,
    "min_savings_rate": 0.10,
    "monthly_expense_fallback": 1500, # CVE (Estimativa base local)
    "risk_limits": {
        "conservador": {"crypto": 0.02, "global": 0.10},
        "moderado": {"crypto": 0.10, "global": 0.30},
        "agressivo": {"crypto": 0.25, "global": 0.50}
    }
}

class FinancialAdvisor:
    """
    Motor de Lógica Financeira Profissional.
    Transforma dados brutos em inteligência estratégica.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id

    def _log_decision(self, task: str, decision_process: str, tools_used: List[str] = None):
        """Regista o processo de decisão para auditoria (L4)."""
        # Nota: Idealmente isto usa o MemoryManager, mas mantemos aqui para lógica pura
        try:
            from .memory import MemoryManager
            mem = MemoryManager(user_id=self.user_id)
            mem.save_audit_log(task, decision_process, tools_used or [])
        except Exception:
            pass # Falha silenciosa para não bloquear lógica

    def get_user_status(self) -> Dict[str, Any]:
        """Coleta dados agregados para avaliar o estado de saúde do utilizador."""
        with get_db_connection() as conn:
            # Garante formato dicionário
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()

            # 1. Datas de Referência
            now = datetime.now()
            thirty_days_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            ninety_days_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d")

            # 2. AGREGAÇÃO DE DADOS (Eficiência: menos queries)
            # Saldo
            row_bal = cursor.execute("SELECT balance, currency FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (self.user_id,)).fetchone()
            current_balance = row_bal['balance'] if row_bal else 0
            
            # Totais Realistas
            trans_sums = cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'saida' AND date >= ? THEN amount ELSE 0 END) as total_90d_exp,
                    SUM(CASE WHEN type = 'entrada' AND date >= ? THEN amount ELSE 0 END) as total_30d_inc,
                    SUM(CASE WHEN type = 'saida' AND date >= ? THEN amount ELSE 0 END) as total_30d_exp,
                    SUM(CASE WHEN category = 'divida' AND type = 'saida' AND date >= ? THEN amount ELSE 0 END) as debt_90d
                FROM transactions WHERE user_id = ?
            """, (ninety_days_ago, thirty_days_ago, thirty_days_ago, ninety_days_ago, self.user_id)).fetchone()

            # 3. Cálculos de Médias
            total_exp_90 = trans_sums['total_90d_exp'] or 0
            monthly_expenses = total_exp_90 / 3 if total_exp_90 > 0 else FINANCIAL_CONFIG["monthly_expense_fallback"]

            # 4. Reserva de Emergência
            row_goal = cursor.execute("SELECT current_amount, target_amount FROM financial_goals WHERE user_id = ? AND name LIKE '%Emergencia%'", (self.user_id,)).fetchone()
            current_reserve = row_goal['current_amount'] if row_goal else current_balance
            
            # 5. Taxa de Poupança
            total_income = trans_sums['total_30d_inc'] or 0
            total_expense = trans_sums['total_30d_exp'] or 0
            savings = total_income - total_expense
            savings_rate = savings / total_income if total_income > 0 else 0

            # 6. Perfil & Preferências
            rows_pref = cursor.execute("SELECT key, value FROM user_preferences WHERE user_id = ?", (self.user_id,)).fetchall()
            prefs = {r['key']: r['value'] for r in rows_pref}

            return {
                "balance": current_balance,
                "monthly_expenses": monthly_expenses,
                "current_reserve": current_reserve,
                "reserve_months": current_reserve / monthly_expenses if monthly_expenses > 0 else 0,
                "has_debt": (trans_sums['debt_90d'] or 0) > 0,
                "savings_rate": savings_rate,
                "age": int(prefs.get("idade", 30)),
                "risk_profile": prefs.get("perfil_risco", None),
                "is_new_user": len(prefs) == 0,
                "has_recent_data": total_income > 0 or total_expense > 0
            }

    def evaluate_investment_viability(self, status: Dict) -> Tuple[bool, List[str]]:
        """Aplica Guardrails para decidir se o investimento é seguro."""
        reasons = []
        min_res = FINANCIAL_CONFIG["min_reserve_months"]
        min_sav = FINANCIAL_CONFIG["min_savings_rate"]

        if status["reserve_months"] < min_res:
            reasons.append(f"Reserva crítica: {status['reserve_months']:.1f}/{min_res} meses necessários.")
        
        if status["has_debt"]:
            reasons.append("Prioridade: Liquidação de dívidas pendentes antes de qualquer investimento.")
        
        if status["savings_rate"] < min_sav:
            reasons.append(f"Fluxo de caixa fraco: Taxa de poupança ({status['savings_rate']*100:.1f}%) abaixo do mínimo de {min_sav*100:.0f}%.")

        is_viable = len(reasons) == 0
        
        # Log de decisão (L4)
        decision_details = f"Viabilidade: {is_viable}. Obstáculos: {', '.join(reasons) if not is_viable else 'Nenhum'}"
        self._log_decision("Invest_Viability_Check", decision_details)
        
        return is_viable, reasons

    def get_recommended_allocation(self, status: Dict) -> Dict[str, str]:
        """Gera alocação estratégica baseada em perfil multi-fatorial."""
        # 1. Determina Perfil (Fallback Inteligente por Idade)
        profile = status["risk_profile"]
        if not profile:
            if status["age"] < 30: profile = "agressivo"
            elif status["age"] <= 45: profile = "moderado"
            else: profile = "conservador"

        # 2. Ajuste por Saúde (Dívida ou Reserva baixa forçam perfil mais conservador)
        actual_profile = profile
        if status["has_debt"] or status["reserve_months"] < 3:
            actual_profile = "conservador"

        allocations = {
            "conservador": {
                "Liquidez/Poupança (CVE)": "70%",
                "Obrigações/Renda Fixa": "25%",
                "Ativos de Risco": "5%"
            },
            "moderado": {
                "Consertador/Reserva (CVE)": "40%",
                "Investimentos Médio Prazo": "30%",
                "ETFs Globais (Ações)": "20%",
                "Cripto/Alternativos": "10%"
            },
            "agressivo": {
                "Reserva Operacional": "20%",
                "Ações Locais/Internacionais": "40%",
                "Criptomoedas": "20%",
                "Capital de Risco/PME": "20%"
            }
        }
        
        return allocations.get(actual_profile, allocations["moderado"])

    def validate_risk_limits(self, portfolio_summary: Dict, profile: str = "moderado") -> List[str]:
        """Aplica Hard Limits baseados no perfil do utilizador."""
        alerts = []
        limits = FINANCIAL_CONFIG["risk_limits"].get(profile.lower(), FINANCIAL_CONFIG["risk_limits"]["moderado"])
        
        crypto_expo = portfolio_summary.get("crypto", 0)
        global_expo = portfolio_summary.get("global", 0)

        if crypto_expo > limits["crypto"]:
            alerts.append(f"⚠️ EXPOSIÇÃO CRIPTO: {crypto_expo*100:.1f}% excede o limite de {limits['crypto']*100:.0f}% para o perfil {profile}.")
        
        if global_expo > limits["global"]:
            alerts.append(f"⚠️ EXPOSIÇÃO GLOBAL: {global_expo*100:.1f}% excede o limite de {limits['global']*100:.0f}% para o perfil {profile}.")

        return alerts
