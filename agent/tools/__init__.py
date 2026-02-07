from .finance import get_account_balance, add_transaction, analyze_finances, set_user_id
from .market import get_stock_quote, get_crypto_price, get_exchange_rate
from .portfolio import manage_portfolio, manage_goals, suggest_investments
from .user_tools import set_user_preference, get_user_profile
from .utility import calculate, web_search, get_now

ALL_TOOLS = [
    get_account_balance, add_transaction, analyze_finances,
    get_stock_quote, get_crypto_price, get_exchange_rate,
    manage_portfolio, manage_goals, suggest_investments,
    set_user_preference, get_user_profile,
    calculate, web_search, get_now
]
