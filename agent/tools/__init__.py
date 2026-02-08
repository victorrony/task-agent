"""
AGENT TOOLS - Agregação de Ferramentas Modularizadas
"""

from .finance_tools import (
    get_account_balance, 
    add_transaction, 
    manage_portfolio, 
    suggest_investments,
    set_user_preference, 
    get_user_profile,
    set_user_id
)
from .integrations import (
    get_stock_quote, 
    get_crypto_price, 
    get_exchange_rate
)
from .core_tools import (
    calculate, 
    web_search, 
    get_now
)

# Exporta set_user_id para o TaskAgent
__all__ = ["ALL_TOOLS", "set_user_id"]

ALL_TOOLS = [
    # Finance & Portfolio
    get_account_balance, 
    add_transaction, 
    manage_portfolio, 
    suggest_investments,
    set_user_preference, 
    get_user_profile,
    
    # Integrations (External APIs)
    get_stock_quote, 
    get_crypto_price, 
    get_exchange_rate,
    
    # Core Utilities
    calculate, 
    web_search, 
    get_now
]
