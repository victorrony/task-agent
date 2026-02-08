"""
CORE TOOLS - Suporte e Utilidades Gerais
"""

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from datetime import datetime

search = DuckDuckGoSearchRun()

@tool
def calculate(expression: str) -> str:
    """Calculadora matemática segura."""
    try:
        allowed = "0123456789+-*/.() "
        clean = "".join(c for c in expression if c in allowed)
        return str(eval(clean))
    except: return "Expressão inválida."

@tool
def web_search(query: str) -> str:
    """Pesquisa na internet para obter informações atualizadas."""
    return search.run(query)

@tool
def get_now() -> str:
    """Retorna a data e hora atual no formato DD/MM/AAAA HH:MM."""
    return datetime.now().strftime("%d/%m/%Y %H:%M")
