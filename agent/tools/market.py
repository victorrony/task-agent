"""
MARKET TOOLS - Real-time Market Data
"""

from langchain_core.tools import tool
import requests
import os

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")

@tool
def get_stock_quote(symbol: str) -> str:
    """Obtém a cotação atual de uma ação (ex: PETR4.SA, AAPL)."""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        data = requests.get(url).json()
        if "Global Quote" in data and data["Global Quote"]:
            q = data["Global Quote"]
            return f"Cotação {symbol}: ${float(q['05. price']):.2f} (Variação: {q['10. change percent']})"
        return f"Não foi possível obter a cotação de {symbol}."
    except Exception as e:
        return f"Erro: {str(e)}"

@tool
def get_crypto_price(crypto: str) -> str:
    """Preço de criptomoedas (bitcoin, ethereum, etc)."""
    try:
        # Simplificando a busca por ID
        ids = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana"}
        c_id = ids.get(crypto.lower(), crypto.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={c_id}&vs_currencies=usd,brl"
        data = requests.get(url).json()
        if c_id in data:
            return f"{crypto.upper()}: ${data[c_id]['usd']:,.2f} | R$ {data[c_id]['brl']:,.2f}"
        return f"Cripto {crypto} não encontrada."
    except Exception as e:
        return f"Erro: {str(e)}"

@tool
def get_exchange_rate(from_curr: str, to_curr: str) -> str:
    """Taxa de câmbio entre moedas (USD, BRL, EUR)."""
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr.upper()}"
        data = requests.get(url).json()
        rate = data['rates'].get(to_curr.upper())
        if rate: return f"1 {from_curr.upper()} = {rate:.4f} {to_curr.upper()}"
        return "Moeda não encontrada."
    except Exception as e:
        return f"Erro: {str(e)}"
