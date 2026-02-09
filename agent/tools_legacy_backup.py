"""
TOOLS DO AGENTE - ASSISTENTE FINANCEIRO
========================================
Ferramentas para o agente multiplicador de conta bancaria.

Funcionalidades:
- Analise Financeira de transacoes e saldo
- Pesquisa de Mercado em tempo real
- Sugestoes de Investimento personalizadas
- Integracao com APIs financeiras
- Memoria de longo prazo para preferencias
"""

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from datetime import datetime, timedelta
from typing import Optional
import random
import os

import requests
import sqlite3
import json
from .pluggy_service import PluggyService
from .export_service import ExportService
import pandas as pd

# Inicializa o motor de busca real
ddg_search = DuckDuckGoSearchRun()

# Caminho para a base de dados local
DB_PATH = "agent_data.db"

# API Keys (carregar do .env)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Estado Global do Usuário Ativo
CURRENT_USER_ID = 1

def set_user_id(user_id: int):
    """Define o usuário ativo para as ferramentas do agente."""
    global CURRENT_USER_ID
    CURRENT_USER_ID = user_id

def init_db():
    """Inicializa a base de dados com tabelas para funcionalidades financeiras."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Garantir que existe o usuário padrão
    cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES (1, 'Usuário Principal')")

    # Tabelas originais com user_id
    tables_to_update = [
        "notes", "transactions", "account_balance", "portfolio", 
        "user_preferences", "financial_goals", "spending_limits"
    ]

    for table in tables_to_update:
        # Tabela original de cada um (precisamos garantir user_id)
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [column[1] for column in cursor.fetchall()]
        if 'user_id' not in columns:
            print(f"Migrando tabela {table} para suporte multi-usuário...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER DEFAULT 1 REFERENCES users(id)")

    # Tabela original de notas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            content TEXT,
            category TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de transacoes bancarias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            date DATE NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('entrada', 'saida')) NOT NULL,
            category TEXT,
            balance_after REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de saldo atual
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_balance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            balance REAL NOT NULL,
            currency TEXT DEFAULT 'BRL',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de portfolio de investimentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            asset_type TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date DATE,
            current_price REAL,
            last_update DATETIME,
            notes TEXT
        )
    """)

    # Tabela de preferencias do usuario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'geral',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key)
        )
    """)

    # Tabela de metas financeiras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline DATE,
            priority TEXT CHECK(priority IN ('alta', 'media', 'baixa')) DEFAULT 'media',
            status TEXT CHECK(status IN ('ativo', 'concluido', 'cancelado')) DEFAULT 'ativo',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de cache para APIs financeiras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de limites de gastos por categoria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spending_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1 REFERENCES users(id),
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category)
        )
    """)

    conn.commit()
    conn.close()

# Inicializa o banco ao carregar as tools
init_db()


# ═══════════════════════════════════════════════════════════
# TOOL 1: CLIMA
# ═══════════════════════════════════════════════════════════
@tool
def get_weather(city: str) -> str:
    """
    Obtém o clima atual de uma cidade.
    
    Args:
        city: Nome da cidade (ex: "Lisboa", "Porto")
    """
    temperatures = random.randint(15, 30)
    conditions = random.choice(["ensolarado ☀️", "nublado ☁️", "chuvoso 🌧️", "parcialmente nublado ⛅"])
    return f"Clima em {city}: {temperatures}°C, {conditions}"


# ═══════════════════════════════════════════════════════════
# TOOL 2: CALCULADORA
# ═══════════════════════════════════════════════════════════
@tool
def calculate(expression: str) -> str:
    """
    Faz cálculos matemáticos.
    
    Args:
        expression: Expressão matemática (ex: "25 * 4")
    """
    try:
        allowed_chars = "0123456789+-*/.() "
        clean_expr = "".join(c for c in expression if c in allowed_chars)
        result = eval(clean_expr)
        return f"O resultado de {expression} é: {result}"
    except Exception as e:
        return f"Erro no cálculo: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 3: BUSCA REAL NA INTERNET
# ═══════════════════════════════════════════════════════════
@tool
def search_info(query: str) -> str:
    """
    Pesquisa informações em tempo real na internet sobre qualquer tema.
    
    Args:
        query: O que buscar na internet
    """
    try:
        result = ddg_search.run(query)
        return result
    except Exception as e:
        return f"Erro ao buscar na internet: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 4: DATA E HORA
# ═══════════════════════════════════════════════════════════
@tool
def get_datetime() -> str:
    """Obtém a data e hora atual."""
    now = datetime.now()
    return f"📅 Data: {now.strftime('%d/%m/%Y')} | ⏰ Hora: {now.strftime('%H:%M')}"


# ═══════════════════════════════════════════════════════════
# TOOL 5: REQUISIÇÃO HTTP (APIs REAIS)
# ═══════════════════════════════════════════════════════════
@tool
def make_http_request(url: str, method: str = "GET", data: dict = None) -> str:
    """
    Faz uma requisição HTTP para uma API externa.
    
    Usa esta tool quando o utilizador pedir para:
    - Consultar um endpoint de API
    - Enviar dados para um servidor externo
    - Obter dados em formato JSON de uma URL
    
    Args:
        url: O endereço da API/URL
        method: O método HTTP (GET, POST, PUT, DELETE, etc)
        data: Dados a enviar (opcional, em formato dict)
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return f"Método {method} não suportado."
        
        if response.status_code >= 400:
            return f"Erro na API (Status {response.status_code}): {response.text}"
            
        return f"Resposta da API ({response.status_code}): {response.text[:1000]}"
    except Exception as e:
        return f"Falha na requisição HTTP: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 6: BASE DE DADOS (SQLITE)
# ═══════════════════════════════════════════════════════════
@tool
def manage_db(action: str, content: str = None, category: str = "geral") -> str:
    """
    Gere uma base de dados local de notas/registos.
    
    Ações disponíveis:
    - 'save': Guarda uma nova nota (precisa de 'content')
    - 'list': Lista todas as notas guardadas
    - 'search': Procura notas por uma categoria específica
    
    Args:
        action: Ação a realizar ('save', 'list', 'search')
        content: O texto da nota a guardar
        category: A categoria da nota (ex: 'importante', 'financeiro')
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if action == "save":
            if not content: return "Erro: Conteúdo em falta."
            cursor.execute("INSERT INTO notes (content, category) VALUES (?, ?)", (content, category))
            conn.commit()
            res = "✅ Registo guardado com sucesso na base de dados."
            
        elif action == "list":
            cursor.execute("SELECT id, category, content, created_at FROM notes ORDER BY created_at DESC")
            rows = cursor.fetchall()
            if not rows: res = "Base de dados vazia."
            else:
                res = "📋 Registos na Base de Dados:\n"
                for r in rows:
                    res += f"[{r[0]}] ({r[1]}) {r[2]} - {r[3]}\n"
                    
        elif action == "search":
            cursor.execute("SELECT content FROM notes WHERE category LIKE ?", (f"%{category}%",))
            rows = cursor.fetchall()
            if not rows: res = f"Nenhum registo encontrado para '{category}'."
            else:
                res = f"🔍 Resultados para '{category}':\n"
                for r in rows:
                    res += f"- {r[0]}\n"
        else:
            res = f"Ação '{action}' não reconhecida."
            
        conn.close()
        return res
    except Exception as e:
        return f"Erro na Base de Dados: {str(e)}"


# ═══════════════════════════════════════════════════════════
# FERRAMENTAS FINANCEIRAS
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# TOOL 7: CONSULTAR SALDO DA CONTA (SOMENTE LEITURA)
# ═══════════════════════════════════════════════════════════
@tool
def get_account_balance() -> str:
    """
    Consulta o saldo atual da conta bancaria (somente leitura).
    Retorna o saldo disponivel e a moeda.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT balance, currency, updated_at
            FROM account_balance
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (CURRENT_USER_ID,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return "Nenhum saldo registrado. Use 'set_account_balance' para definir o saldo inicial."

        balance, currency, updated = row
        return f"Saldo atual: {currency} {balance:,.2f} (atualizado em {updated})"
    except Exception as e:
        return f"Erro ao consultar saldo: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 8: DEFINIR/ATUALIZAR SALDO DA CONTA
# ═══════════════════════════════════════════════════════════
@tool
def set_account_balance(balance: float, currency: str = "BRL") -> str:
    """
    Define ou atualiza o saldo atual da conta bancaria.

    Args:
        balance: Valor do saldo atual
        currency: Moeda (BRL, USD, EUR, etc). Padrao: BRL
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO account_balance (balance, currency) VALUES (?, ?)",
            (balance, currency)
        )
        conn.commit()
        conn.close()
        return f"Saldo atualizado: {currency} {balance:,.2f}"
    except Exception as e:
        return f"Erro ao atualizar saldo: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 9: REGISTRAR TRANSACAO
# ═══════════════════════════════════════════════════════════
@tool
def add_transaction(
    amount: float,
    transaction_type: str,
    description: str,
    category: str = "outros",
    date: str = None
) -> str:
    """
    Registra uma nova transacao bancaria.

    Args:
        amount: Valor da transacao (positivo)
        transaction_type: Tipo da transacao ('entrada' ou 'saida')
        description: Descricao da transacao
        category: Categoria (alimentacao, transporte, salario, investimento, etc)
        date: Data da transacao (formato YYYY-MM-DD). Se nao informada, usa data atual.
    """
    try:
        if transaction_type not in ['entrada', 'saida']:
            return "Erro: tipo deve ser 'entrada' ou 'saida'"

        trans_date = date or datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obter saldo atual do usuário
        cursor.execute("SELECT balance FROM account_balance WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (CURRENT_USER_ID,))
        row = cursor.fetchone()
        current_balance = row[0] if row else 0

        # Calcular novo saldo
        if transaction_type == 'entrada':
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount

        # Inserir transacao vinculada ao usuário
        cursor.execute("""
            INSERT INTO transactions (user_id, date, description, amount, type, category, balance_after)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (CURRENT_USER_ID, trans_date, description, amount, transaction_type, category, new_balance))

        # Atualizar saldo do usuário
        cursor.execute("INSERT INTO account_balance (user_id, balance) VALUES (?, ?)", (CURRENT_USER_ID, new_balance))

        # Verificar limites de gastos do usuário
        cursor.execute("SELECT monthly_limit FROM spending_limits WHERE user_id = ? AND LOWER(category) = LOWER(?)", 
                       (CURRENT_USER_ID, category.lower()))
        limit_row = cursor.fetchone()
        warning = ""
        if limit_row:
            monthly_limit = limit_row[0]
            # Calcular total gasto no mês atual para esta categoria (incluindo o que acabamos de inserir)
            first_day = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT SUM(amount) FROM transactions 
                WHERE user_id = ? AND type = 'saida' AND LOWER(category) = LOWER(?) AND date >= ?
            """, (CURRENT_USER_ID, category.lower(), first_day))
            total_spent = cursor.fetchone()[0] or 0
            
            if total_spent > monthly_limit:
                warning = f"\n\n⚠️ ATENÇÃO: Limite de gastos para '{category}' excedido! (Gasto: R$ {total_spent:.2f} / Limite: R$ {monthly_limit:.2f})"
            elif total_spent > monthly_limit * 0.8:
                warning = f"\n\n💡 AVISO: Você atingiu 80% do limite para '{category}'. (Gasto: R$ {total_spent:.2f} / Limite: R$ {monthly_limit:.2f})"

        conn.commit()
        conn.close()
        
        emoji = "+" if transaction_type == 'entrada' else "-"
        return f"Transação registrada: {emoji}R$ {amount:,.2f} ({description}). Novo saldo: R$ {new_balance:,.2f}{warning}"
    except Exception as e:
        return f"Erro ao registrar transacao: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 10: LISTAR TRANSACOES
# ═══════════════════════════════════════════════════════════
@tool
def list_transactions(
    limit: int = 10,
    category: str = None,
    transaction_type: str = None
) -> str:
    """
    Lista as transacoes bancarias com filtros opcionais.

    Args:
        limit: Numero maximo de transacoes a retornar (padrao: 10)
        category: Filtrar por categoria (opcional)
        transaction_type: Filtrar por tipo - 'entrada' ou 'saida' (opcional)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = "SELECT date, description, amount, type, category, balance_after FROM transactions WHERE 1=1"
        params = []

        if category:
            query += " AND category LIKE ?"
            params.append(f"%{category}%")

        if transaction_type:
            query += " AND type = ?"
            params.append(transaction_type)

        query += " ORDER BY date DESC, id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "Nenhuma transacao encontrada com os filtros especificados."

        result = "Transacoes:\n" + "-" * 50 + "\n"
        for date, desc, amount, t_type, cat, balance in rows:
            emoji = "+" if t_type == 'entrada' else "-"
            result += f"{date} | {emoji}R$ {amount:,.2f} | {desc} [{cat}] | Saldo: R$ {balance:,.2f}\n"

        return result
    except Exception as e:
        return f"Erro ao listar transacoes: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 11: ANALISE FINANCEIRA
# ═══════════════════════════════════════════════════════════
@tool
def analyze_finances(period_days: int = 30) -> str:
    """
    Realiza uma analise detalhada das financas dos ultimos dias.
    Inclui: total de entradas, saidas, saldo, e gastos por categoria.

    Args:
        period_days: Periodo em dias para analise (padrao: 30)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

        # Total de entradas
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE type = 'entrada' AND date >= ?
        """, (start_date,))
        total_income = cursor.fetchone()[0]

        # Total de saidas
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE type = 'saida' AND date >= ?
        """, (start_date,))
        total_expenses = cursor.fetchone()[0]

        # Gastos por categoria
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE type = 'saida' AND date >= ?
            GROUP BY category
            ORDER BY total DESC
        """, (start_date,))
        expenses_by_category = cursor.fetchall()

        # Saldo atual
        cursor.execute("SELECT balance FROM account_balance ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        current_balance = row[0] if row else 0

        conn.close()

        # Montar relatorio
        balance_change = total_income - total_expenses
        savings_rate = (balance_change / total_income * 100) if total_income > 0 else 0

        result = f"""
ANALISE FINANCEIRA - Ultimos {period_days} dias
{'=' * 50}
Saldo Atual: R$ {current_balance:,.2f}
Total de Entradas: R$ {total_income:,.2f}
Total de Saidas: R$ {total_expenses:,.2f}
Variacao no Periodo: R$ {balance_change:,.2f}
Taxa de Poupanca: {savings_rate:.1f}%

GASTOS POR CATEGORIA:
{'-' * 30}
"""
        for cat, amount in expenses_by_category:
            percent = (amount / total_expenses * 100) if total_expenses > 0 else 0
            result += f"  {cat}: R$ {amount:,.2f} ({percent:.1f}%)\n"

        # Insights automaticos
        result += f"\nINSIGHTS:\n{'-' * 30}\n"
        if savings_rate >= 20:
            result += "Excelente! Voce esta poupando mais de 20% da sua renda.\n"
        elif savings_rate >= 10:
            result += "Bom! Voce esta poupando entre 10-20%. Tente aumentar para 20%.\n"
        elif savings_rate > 0:
            result += "Atencao! Sua taxa de poupanca esta baixa. Revise seus gastos.\n"
        else:
            result += "ALERTA! Voce esta gastando mais do que ganha. Acao urgente necessaria!\n"

        return result
    except Exception as e:
        return f"Erro na analise financeira: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 12: COTACAO DE ACOES
# ═══════════════════════════════════════════════════════════
@tool
def get_stock_quote(symbol: str) -> str:
    """
    Obtem a cotacao atual de uma acao.
    Suporta acoes brasileiras (ex: PETR4.SA, VALE3.SA) e americanas (ex: AAPL, GOOGL).

    Args:
        symbol: Simbolo da acao (ex: PETR4.SA, AAPL, GOOGL)
    """
    try:
        # Tentar usar Alpha Vantage API
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"

        response = requests.get(url, timeout=10)
        data = response.json()

        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            price = float(quote.get("05. price", 0))
            change = float(quote.get("09. change", 0))
            change_pct = quote.get("10. change percent", "0%")
            volume = quote.get("06. volume", "N/A")

            emoji = "+" if change >= 0 else ""
            return f"""
Cotacao de {symbol}:
  Preco Atual: ${price:,.2f}
  Variacao: {emoji}{change:,.2f} ({change_pct})
  Volume: {volume}
"""
        else:
            # Fallback: buscar na internet
            search_result = ddg_search.run(f"cotacao {symbol} acao hoje")
            return f"Cotacao via busca:\n{search_result[:500]}"

    except Exception as e:
        return f"Erro ao obter cotacao: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 13: COTACAO DE CRIPTOMOEDAS
# ═══════════════════════════════════════════════════════════
@tool
def get_crypto_price(crypto: str) -> str:
    """
    Obtem o preco atual de uma criptomoeda.

    Args:
        crypto: Nome ou simbolo da cripto (bitcoin, ethereum, btc, eth, etc)
    """
    try:
        # Mapear nomes comuns para IDs do CoinGecko
        crypto_map = {
            "btc": "bitcoin", "bitcoin": "bitcoin",
            "eth": "ethereum", "ethereum": "ethereum",
            "bnb": "binancecoin", "binance": "binancecoin",
            "sol": "solana", "solana": "solana",
            "ada": "cardano", "cardano": "cardano",
            "xrp": "ripple", "ripple": "ripple",
            "doge": "dogecoin", "dogecoin": "dogecoin",
            "dot": "polkadot", "polkadot": "polkadot"
        }

        crypto_id = crypto_map.get(crypto.lower(), crypto.lower())

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd,brl&include_24hr_change=true"
        response = requests.get(url, timeout=10)
        data = response.json()

        if crypto_id in data:
            info = data[crypto_id]
            usd_price = info.get("usd", 0)
            brl_price = info.get("brl", 0)
            change_24h = info.get("usd_24h_change", 0)

            emoji = "+" if change_24h >= 0 else ""
            return f"""
Preco de {crypto.upper()}:
  USD: ${usd_price:,.2f}
  BRL: R$ {brl_price:,.2f}
  Variacao 24h: {emoji}{change_24h:.2f}%
"""
        else:
            return f"Criptomoeda '{crypto}' nao encontrada."

    except Exception as e:
        return f"Erro ao obter preco da cripto: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 14: TAXA DE CAMBIO
# ═══════════════════════════════════════════════════════════
@tool
def get_exchange_rate(from_currency: str, to_currency: str, amount: float = 1.0) -> str:
    """
    Obtem a taxa de cambio entre duas moedas e converte um valor.

    Args:
        from_currency: Moeda de origem (USD, EUR, BRL, etc)
        to_currency: Moeda de destino (USD, EUR, BRL, etc)
        amount: Valor a converter (padrao: 1.0)
    """
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "rates" in data:
            rate = data["rates"].get(to_currency.upper())
            if rate:
                converted = amount * rate
                return f"""
Taxa de Cambio:
  1 {from_currency.upper()} = {rate:.4f} {to_currency.upper()}
  {amount:,.2f} {from_currency.upper()} = {converted:,.2f} {to_currency.upper()}
"""
            else:
                return f"Moeda '{to_currency}' nao encontrada."
        else:
            return "Erro ao obter taxas de cambio."

    except Exception as e:
        return f"Erro na conversao: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 15: PESQUISA DE MERCADO FINANCEIRO
# ═══════════════════════════════════════════════════════════
@tool
def search_market_news(query: str) -> str:
    """
    Pesquisa noticias e tendencias do mercado financeiro em tempo real.

    Args:
        query: Termo de busca (ex: "acoes brasileiras", "bitcoin tendencia", "ibovespa")
    """
    try:
        search_query = f"mercado financeiro {query} noticias investimento"
        result = ddg_search.run(search_query)
        return f"Noticias de Mercado sobre '{query}':\n\n{result}"
    except Exception as e:
        return f"Erro na pesquisa de mercado: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 16: SUGESTAO DE INVESTIMENTOS
# ═══════════════════════════════════════════════════════════
@tool
def suggest_investments(
    available_amount: float,
    risk_profile: str = "moderado",
    investment_horizon: str = "medio"
) -> str:
    """
    Sugere opcoes de investimento com base no perfil do usuario.

    Args:
        available_amount: Valor disponivel para investir
        risk_profile: Perfil de risco - 'conservador', 'moderado' ou 'arrojado'
        investment_horizon: Horizonte de investimento - 'curto' (ate 1 ano), 'medio' (1-5 anos), 'longo' (5+ anos)
    """
    try:
        suggestions = {
            "conservador": {
                "curto": [
                    ("Tesouro Selic", 40, "Liquidez diaria, seguranca maxima"),
                    ("CDB de liquidez diaria", 30, "Rentabilidade acima da poupanca"),
                    ("Fundo DI", 20, "Baixo risco, facil resgate"),
                    ("Poupanca", 10, "Reserva de emergencia")
                ],
                "medio": [
                    ("Tesouro IPCA+", 40, "Protecao contra inflacao"),
                    ("CDB de bancos medios", 30, "Maior rentabilidade"),
                    ("LCI/LCA", 20, "Isento de IR"),
                    ("Fundos de Renda Fixa", 10, "Diversificacao")
                ],
                "longo": [
                    ("Tesouro IPCA+ longo prazo", 50, "Aposentadoria"),
                    ("Fundos de Previdencia", 30, "Beneficios fiscais"),
                    ("Debentures incentivadas", 20, "Isento de IR, maior risco")
                ]
            },
            "moderado": {
                "curto": [
                    ("Tesouro Selic", 30, "Liquidez"),
                    ("CDB", 30, "Renda fixa"),
                    ("Fundos Multimercado", 25, "Diversificacao"),
                    ("Acoes de dividendos", 15, "Renda passiva")
                ],
                "medio": [
                    ("Acoes blue chips", 30, "PETR4, VALE3, ITUB4"),
                    ("Fundos Imobiliarios (FIIs)", 25, "Renda mensal"),
                    ("Tesouro IPCA+", 25, "Protecao"),
                    ("ETFs", 20, "Diversificacao passiva")
                ],
                "longo": [
                    ("Acoes de crescimento", 35, "Valorizacao de capital"),
                    ("FIIs", 25, "Renda e valorizacao"),
                    ("ETFs internacionais", 20, "Exposicao global"),
                    ("Criptomoedas", 10, "Alto risco/retorno"),
                    ("Renda Fixa", 10, "Estabilidade")
                ]
            },
            "arrojado": {
                "curto": [
                    ("Acoes", 50, "Trading e swing trade"),
                    ("Opcoes", 20, "Alavancagem"),
                    ("Criptomoedas", 20, "Alta volatilidade"),
                    ("Reserva Tesouro Selic", 10, "Emergencias")
                ],
                "medio": [
                    ("Acoes de crescimento", 40, "Small/Mid caps"),
                    ("Criptomoedas", 25, "BTC, ETH, altcoins"),
                    ("Acoes internacionais", 20, "Tech stocks"),
                    ("FIIs", 15, "Diversificacao")
                ],
                "longo": [
                    ("Acoes de crescimento", 45, "Empresas disruptivas"),
                    ("Criptomoedas", 20, "Posicao de longo prazo"),
                    ("Startups/Equity crowdfunding", 15, "Alto risco"),
                    ("ETFs tematicos", 10, "IA, energia limpa"),
                    ("Renda Fixa", 10, "Estabilidade minima")
                ]
            }
        }

        profile = risk_profile.lower()
        horizon = investment_horizon.lower()

        if profile not in suggestions:
            profile = "moderado"
        if horizon not in suggestions[profile]:
            horizon = "medio"

        portfolio = suggestions[profile][horizon]

        result = f"""
SUGESTAO DE INVESTIMENTOS
{'=' * 50}
Valor Disponivel: R$ {available_amount:,.2f}
Perfil de Risco: {profile.upper()}
Horizonte: {horizon.upper()} prazo

ALOCACAO SUGERIDA:
{'-' * 40}
"""

        for asset, percent, desc in portfolio:
            value = available_amount * (percent / 100)
            result += f"\n  {asset}\n"
            result += f"    Alocacao: {percent}% (R$ {value:,.2f})\n"
            result += f"    Motivo: {desc}\n"

        result += f"""
{'-' * 40}
AVISO IMPORTANTE:
Esta e uma sugestao educacional. Consulte um assessor
de investimentos certificado antes de investir.
Investimentos envolvem riscos. Rentabilidade passada
nao garante rentabilidade futura.
"""

        return result
    except Exception as e:
        return f"Erro ao gerar sugestoes: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 17: GERENCIAR PORTFOLIO
# ═══════════════════════════════════════════════════════════
@tool
def manage_portfolio(
    action: str,
    asset_type: str = None,
    symbol: str = None,
    quantity: float = None,
    price: float = None,
    name: str = None
) -> str:
    """
    Gerencia o portfolio de investimentos.

    Args:
        action: Acao a realizar - 'add' (adicionar), 'remove' (remover), 'list' (listar), 'summary' (resumo)
        asset_type: Tipo do ativo - 'acao', 'fii', 'cripto', 'renda_fixa', 'etf'
        symbol: Simbolo do ativo (ex: PETR4, MXRF11, BTC)
        quantity: Quantidade comprada/vendida
        price: Preco de compra por unidade
        name: Nome descritivo do ativo
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if action == "add":
            if not all([asset_type, symbol, quantity, price]):
                return "Erro: Para adicionar, informe asset_type, symbol, quantity e price"

            cursor.execute("""
                INSERT INTO portfolio (asset_type, symbol, name, quantity, purchase_price, purchase_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (asset_type, symbol.upper(), name or symbol.upper(), quantity, price, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            total = quantity * price
            result = f"Adicionado ao portfolio: {quantity} x {symbol.upper()} a R$ {price:.2f} = R$ {total:,.2f}"

        elif action == "remove":
            if not symbol:
                return "Erro: Informe o symbol do ativo a remover"
            cursor.execute("DELETE FROM portfolio WHERE symbol = ?", (symbol.upper(),))
            conn.commit()
            result = f"Ativo {symbol.upper()} removido do portfolio"

        elif action == "list":
            cursor.execute("""
                SELECT asset_type, symbol, name, quantity, purchase_price, purchase_date
                FROM portfolio ORDER BY asset_type, symbol
            """)
            rows = cursor.fetchall()

            if not rows:
                result = "Portfolio vazio. Use action='add' para adicionar ativos."
            else:
                result = "PORTFOLIO DE INVESTIMENTOS\n" + "=" * 50 + "\n"
                current_type = None
                total_invested = 0

                for a_type, sym, name, qty, price, date in rows:
                    if a_type != current_type:
                        current_type = a_type
                        result += f"\n[{a_type.upper()}]\n"

                    value = qty * price
                    total_invested += value
                    result += f"  {sym}: {qty} unidades @ R$ {price:.2f} = R$ {value:,.2f} ({date})\n"

                result += f"\n{'=' * 50}\nTOTAL INVESTIDO: R$ {total_invested:,.2f}\n"

        elif action == "summary":
            cursor.execute("""
                SELECT asset_type, SUM(quantity * purchase_price) as total
                FROM portfolio GROUP BY asset_type
            """)
            rows = cursor.fetchall()

            if not rows:
                result = "Portfolio vazio."
            else:
                result = "RESUMO DO PORTFOLIO\n" + "=" * 40 + "\n"
                grand_total = 0

                for a_type, total in rows:
                    result += f"  {a_type.upper()}: R$ {total:,.2f}\n"
                    grand_total += total

                result += f"\n{'=' * 40}\n  TOTAL: R$ {grand_total:,.2f}\n"

                # Calcular alocacao percentual
                result += "\n  ALOCACAO:\n"
                for a_type, total in rows:
                    pct = (total / grand_total * 100) if grand_total > 0 else 0
                    result += f"    {a_type}: {pct:.1f}%\n"
        else:
            result = f"Acao '{action}' nao reconhecida. Use: add, remove, list, summary"

        conn.close()
        return result
    except Exception as e:
        return f"Erro no portfolio: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 18: MEMORIA DE LONGO PRAZO (PREFERENCIAS)
# ═══════════════════════════════════════════════════════════
@tool
def manage_preferences(
    action: str,
    key: str = None,
    value: str = None,
    category: str = "financeiro"
) -> str:
    """
    Gerencia as preferencias e informacoes do usuario para memoria de longo prazo.

    Args:
        action: Acao - 'set' (definir), 'get' (obter), 'list' (listar), 'delete' (apagar)
        key: Nome da preferencia (ex: 'perfil_risco', 'meta_mensal', 'moeda_preferida')
        value: Valor da preferencia
        category: Categoria da preferencia (financeiro, pessoal, investimento)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if action == "set":
            if not key or not value:
                return "Erro: Informe key e value para salvar uma preferencia"

            cursor.execute("""
                INSERT INTO user_preferences (key, value, category, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=?, category=?, updated_at=?
            """, (key, value, category, datetime.now(), value, category, datetime.now()))
            conn.commit()
            result = f"Preferencia salva: {key} = {value}"

        elif action == "get":
            if not key:
                return "Erro: Informe a key da preferencia"
            cursor.execute("SELECT value, category, updated_at FROM user_preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                result = f"Preferencia '{key}': {row[0]} (categoria: {row[1]}, atualizado: {row[2]})"
            else:
                result = f"Preferencia '{key}' nao encontrada"

        elif action == "list":
            cursor.execute("SELECT key, value, category FROM user_preferences ORDER BY category, key")
            rows = cursor.fetchall()
            if not rows:
                result = "Nenhuma preferencia salva"
            else:
                result = "PREFERENCIAS DO USUARIO\n" + "=" * 40 + "\n"
                for k, v, c in rows:
                    result += f"  [{c}] {k}: {v}\n"

        elif action == "delete":
            if not key:
                return "Erro: Informe a key para apagar"
            cursor.execute("DELETE FROM user_preferences WHERE key = ?", (key,))
            conn.commit()
            result = f"Preferencia '{key}' apagada"
        else:
            result = f"Acao '{action}' nao reconhecida"

        conn.close()
        return result
    except Exception as e:
        return f"Erro nas preferencias: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 19: METAS FINANCEIRAS
# ═══════════════════════════════════════════════════════════
@tool
def manage_financial_goals(
    action: str,
    name: str = None,
    target_amount: float = None,
    current_amount: float = None,
    deadline: str = None,
    priority: str = "media"
) -> str:
    """
    Gerencia metas financeiras do usuario.

    Args:
        action: Acao - 'add' (criar), 'update' (atualizar progresso), 'list' (listar), 'delete' (apagar)
        name: Nome da meta (ex: 'Reserva de Emergencia', 'Viagem Europa')
        target_amount: Valor alvo da meta
        current_amount: Valor atual acumulado (para update)
        deadline: Data limite (formato YYYY-MM-DD)
        priority: Prioridade - 'alta', 'media', 'baixa'
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if action == "add":
            if not name or not target_amount:
                return "Erro: Informe name e target_amount para criar uma meta"

            cursor.execute("""
                INSERT INTO financial_goals (name, target_amount, deadline, priority)
                VALUES (?, ?, ?, ?)
            """, (name, target_amount, deadline, priority))
            conn.commit()
            result = f"Meta criada: '{name}' - Objetivo: R$ {target_amount:,.2f}"

        elif action == "update":
            if not name:
                return "Erro: Informe o name da meta"

            if current_amount is not None:
                cursor.execute("""
                    UPDATE financial_goals
                    SET current_amount = ?,
                        status = CASE WHEN ? >= target_amount THEN 'concluido' ELSE status END
                    WHERE user_id = ? AND name = ? AND status = 'ativo'
                """, (current_amount, current_amount, CURRENT_USER_ID, name))
                conn.commit()
                result = f"Meta '{name}' atualizada: R$ {current_amount:,.2f} acumulados"
            else:
                return "Erro: Informe current_amount para atualizar"

        elif action == "list":
            cursor.execute("""
                SELECT name, target_amount, current_amount, deadline, priority, status
                FROM financial_goals WHERE user_id = ? ORDER BY priority DESC, deadline
            """, (CURRENT_USER_ID,))
            rows = cursor.fetchall()

            if not rows:
                result = "Nenhuma meta financeira cadastrada"
            else:
                result = "METAS FINANCEIRAS\n" + "=" * 50 + "\n"
                for name, target, current, deadline, priority, status in rows:
                    progress = (current / target * 100) if target > 0 else 0
                    bar_filled = int(progress / 10)
                    bar = "[" + "#" * bar_filled + "-" * (10 - bar_filled) + "]"

                    result += f"\n{name} [{priority.upper()}] - {status.upper()}\n"
                    result += f"  Progresso: R$ {current:,.2f} / R$ {target:,.2f}\n"
                    result += f"  {bar} {progress:.1f}%\n"
                    if deadline:
                        result += f"  Prazo: {deadline}\n"

        elif action == "delete":
            if not name:
                return "Erro: Informe o name da meta"
            cursor.execute("DELETE FROM financial_goals WHERE user_id = ? AND name = ?", (CURRENT_USER_ID, name))
            conn.commit()
            result = f"Meta '{name}' removida"
        else:
            result = f"Acao '{action}' nao reconhecida"

        conn.close()
        return result
    except Exception as e:
        return f"Erro nas metas: {str(e)}"


# ═══════════════════════════════════════════════════════════
# TOOL 20: INDICADORES ECONOMICOS
# ═══════════════════════════════════════════════════════════
@tool
def get_economic_indicators(indicator: str = "all") -> str:
    """
    Busca indicadores economicos atuais do Brasil e mundo.

    Args:
        indicator: Indicador especifico ou 'all' para todos
                  Opcoes: 'selic', 'ipca', 'cdi', 'ibovespa', 'dolar', 'euro', 'all'
    """
    try:
        # Buscar informacoes via web
        if indicator == "all":
            search_query = "taxa selic ipca cdi hoje Brasil indicadores economicos"
        else:
            search_query = f"{indicator} taxa hoje Brasil"

        result = ddg_search.run(search_query)

        header = f"""
INDICADORES ECONOMICOS - {indicator.upper()}
{'=' * 50}
"""
        return header + result
    except Exception as e:
        return f"Erro ao buscar indicadores: {str(e)}"
@tool
def set_spending_limit(category: str, monthly_limit: float) -> str:
    """
    Define um limite de gastos mensal para uma categoria específica.
    Ex: set_spending_limit("Alimentação", 500.0)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO spending_limits (user_id, category, monthly_limit)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
        """, (CURRENT_USER_ID, category.lower(), monthly_limit))
        conn.commit()
        conn.close()
        return f"Limite de R$ {monthly_limit:.2f} definido para a categoria '{category}'."
    except Exception as e:
        return f"Erro ao definir limite: {str(e)}"

@tool
def get_spending_alerts() -> str:
    """
    Verifica se alguma categoria ultrapassou o limite de gastos definido para o mês atual.
    Retorna uma lista de alertas se houver excessos.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT category, monthly_limit FROM spending_limits WHERE user_id = ?", (CURRENT_USER_ID,))
        limits = cursor.fetchall()
        
        if not limits:
            return "Nenhum limite de gastos configurado."
            
        alerts = []
        first_day = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        
        for category, monthly_limit in limits:
            cursor.execute("""
                SELECT SUM(amount) FROM transactions 
                WHERE user_id = ? AND type = 'saida' AND LOWER(category) = LOWER(?) AND date >= ?
            """, (CURRENT_USER_ID, category.lower(), first_day))
            total_spent = cursor.fetchone()[0] or 0
            
            if total_spent > monthly_limit:
                alerts.append(f"❌ {category.capitalize()}: R$ {total_spent:.2f} (Limite: R$ {monthly_limit:.2f}) - EXCEDIDO!")
            elif total_spent > monthly_limit * 0.8:
                alerts.append(f"⚠️ {category.capitalize()}: R$ {total_spent:.2f} (Limite: R$ {monthly_limit:.2f}) - Próximo do limite.")
        
        conn.close()
        
        if not alerts:
            return "Todos os gastos estão dentro dos limites estabelecidos. Bom trabalho!"
            
        return "ALERTAS DE GASTOS:\n" + "\n".join(alerts)
    except Exception as e:
        return f"Erro ao buscar alertas: {str(e)}"

@tool
def generate_financial_report(format: str = "pdf") -> str:
    """
    Gera um relatório financeiro completo com suas transações e saldo.
    Formatos suportados: 'pdf' ou 'excel'.
    Retorna o caminho do arquivo gerado para download.
    """
    try:
        # Obter transações do banco do usuário logado
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("""
            SELECT date, description, amount, type, category 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC
        """, conn, params=(CURRENT_USER_ID,))
        conn.close()
        
        if df.empty:
            return "Nenhuma transação encontrada para gerar relatório."
            
        service = ExportService()
        if format.lower() == "excel":
            filepath = service.export_to_excel(df)
            msg = "Excel"
        else:
            filepath = service.export_to_pdf(df)
            msg = "PDF"
            
        if filepath:
            return f"Relatório financeiro ({msg}) gerado com sucesso! Você pode baixá-lo na aba 'Extrato'."
        return f"Erro ao gerar o arquivo de relatório {msg}."
    except Exception as e:
        return f"Erro ao gerar relatório: {str(e)}"

@tool
def sync_bank_data() -> str:
    """
    Sincroniza automaticamente os dados da sua conta bancária real (ou sandbox) via Pluggy.
    Importa novas transações e atualiza o saldo atual.
    """
    try:
        service = PluggyService()
        result = service.sync_data()
        return result
    except Exception as e:
        return f"Erro ao sincronizar dados bancários: {str(e)}"


# Lista de todas as tools disponíveis
ALL_TOOLS = [
    # Tools originais
    get_weather,
    calculate,
    search_info,
    get_datetime,
    make_http_request,
    manage_db,
    # Tools financeiras
    get_account_balance,
    set_account_balance,
    add_transaction,
    list_transactions,
    analyze_finances,
    get_stock_quote,
    get_crypto_price,
    get_exchange_rate,
    search_market_news,
    suggest_investments,
    manage_portfolio,
    manage_preferences,
    manage_financial_goals,
    get_economic_indicators,
    sync_bank_data,
    set_spending_limit,
    get_spending_alerts,
    generate_financial_report
]

