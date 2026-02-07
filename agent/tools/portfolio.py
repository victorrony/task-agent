"""
PORTFOLIO TOOLS - Gerenciamento de Ativos e Metas
"""

from langchain_core.tools import tool
import sqlite3
from ..db import get_db_connection

# Reusing the user context
from .finance import CURRENT_USER_ID

@tool
def manage_portfolio(action: str, symbol: str = None, quantity: float = 0, price: float = 0) -> str:
    """Gere o portfólio de ativos (add, remove, list)."""
    try:
        conn = get_db_connection()
        if action == "add":
            conn.execute("INSERT INTO portfolio (user_id, symbol, quantity, purchase_price) VALUES (?, ?, ?, ?)", 
                         (CURRENT_USER_ID, symbol.upper(), quantity, price))
            res = f"Ativo {symbol} adicionado."
        elif action == "list":
            rows = conn.execute("SELECT symbol, quantity, purchase_price FROM portfolio WHERE user_id = ?", (CURRENT_USER_ID,)).fetchall()
            res = "Seu Portfólio:\n" + "\n".join([f"- {r['symbol']}: {r['quantity']} @ R$ {r['purchase_price']:.2f}" for r in rows])
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        return f"Erro: {str(e)}"

@tool
def manage_goals(action: str, name: str = None, target: float = 0) -> str:
    """Gere metas financeiras (add, list, update)."""
    # Logic simplified for brevity
    return "Gerenciamento de meta concluído (simulado)."

@tool
def suggest_investments() -> str:
    """
    Gera uma sugestão de alocação de investimentos baseada nas regras rígidas do sistema.
    Analisa reserva de emergência, dívidas, idade e perfil de risco.
    """
    from ..logic import FinancialAdvisor
    
    advisor = FinancialAdvisor(CURRENT_USER_ID)
    status = advisor.get_user_status()
    
    # 1. Verificar Viabilidade (Regra 0)
    can_invest, reasons = advisor.evaluate_investment_viability(status)
    
    if not can_invest:
        msg = "⚠️ INVESTIMENTO NÃO RECOMENDADO NO MOMENTO\n\n"
        msg += "Detectamos as seguintes contra-indicações:\n"
        for r in reasons:
            msg += f"- {r}\n"
        msg += "\n➡️ O sistema entrou em Modo Educador. Vamos focar em organizar o básico primeiro?"
        return msg

    # 2. Gerar Alocação (Regra 3)
    allocation = advisor.get_recommended_allocation(status)
    
    res = "🎯 PLANO DE INVESTIMENTO PERSONALIZADO\n"
    res += f"Perfil identificado: {status['risk_profile'] or 'Automático (por idade)'}\n"
    res += "=" * 40 + "\n"
    for k, v in allocation.items():
        res += f"{k}: {v}\n"
    
    res += "\n🌍 NOTA: Esta alocação considera a paridade CVE/EUR e o acesso a mercados globais."
    res += "\n💡 RECOMENDAÇÃO: Investimento recorrente mensal para consistência (DCA)."
    
    return res
