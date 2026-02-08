"""
SIMULATIONS - Funções de Cenário para Testes E2E (Multi-tool Orchestration)
========================================================================
Este módulo permite simular fluxos completos de utilizadores sem intervenção manual.
"""

from .finance_tools import set_user_id, add_transaction, get_account_balance, suggest_investments
from .core_tools import get_now

def simulate_new_user_journey(user_id: int):
    """Simula um utilizador novo: onboarding, depósito, despesa e análise."""
    set_user_id(user_id)
    print(f"--- Simulação USER {user_id} (Início) ---")
    
    # 1. Depósito Inicial
    print(add_transaction(50000, "entrada", "Depósito Inicial / Salário", "salario"))
    
    # 2. Despesa de teste
    print(add_transaction(1200, "saida", "Compras Supermercado", "alimentacao"))
    
    # 3. Consulta de Saldo
    print(get_account_balance.invoke({}))
    
    # 4. Tentativa de Investimento (Com pouca reserva)
    print("\n--- Sugestão de Investimento (Reserva Baixa) ---")
    print(suggest_investments.invoke({}))
    
    print(f"--- Simulação USER {user_id} (Fim) ---")

def simulate_stable_user_journey(user_id: int):
    """Simula utilizador com reserva robusta pronto para investir."""
    set_user_id(user_id)
    print(f"--- Simulação USER {user_id} (Estável) ---")
    
    # 1. Depósito Massivo para garantir reserva
    print(add_transaction(500000, "entrada", "Bónus Anual", "bonus"))
    
    # 2. Análise e Sugestão
    print("\n--- Sugestão de Investimento (Reserva OK) ---")
    print(suggest_investments.invoke({}))
    
    print(f"--- Simulação USER {user_id} (Fim) ---")
