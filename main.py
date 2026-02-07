#!/usr/bin/env python3
"""
FinanceAgent Pro - Interface de Terminal
=========================================

Assistente financeiro inteligente via linha de comando.

Uso:
    python main.py
"""

from agent import TaskAgent


def print_header():
    """Exibe o cabecalho do programa."""
    print()
    print("=" * 60)
    print("  FinanceAgent Pro - Assistente Financeiro Inteligente")
    print("=" * 60)
    print()


def print_help():
    """Exibe comandos disponiveis."""
    print("-" * 60)
    print("COMANDOS RAPIDOS:")
    print("-" * 60)
    print()
    print("  GESTAO DE CONTA:")
    print("    'saldo'      - Ver saldo atual")
    print("    'transacoes' - Listar transacoes recentes")
    print("    'analise'    - Analise financeira do mes")
    print()
    print("  MERCADO:")
    print("    'bitcoin'    - Preco do Bitcoin")
    print("    'dolar'      - Cotacao USD/BRL")
    print("    'selic'      - Taxa Selic atual")
    print()
    print("  INVESTIMENTOS:")
    print("    'portfolio'  - Ver portfolio")
    print("    'metas'      - Ver metas financeiras")
    print("    'sugestao'   - Sugestao de investimentos")
    print()
    print("  SISTEMA:")
    print("    'ajuda'      - Mostrar esta ajuda")
    print("    'limpar'     - Limpar memoria da conversa")
    print("    'sair'       - Encerrar o programa")
    print()
    print("-" * 60)


def print_examples():
    """Exibe exemplos de uso."""
    print()
    print("EXEMPLOS DE USO:")
    print("-" * 60)
    print()
    print("  Definir saldo:")
    print("    'Meu saldo atual e R$ 5000'")
    print()
    print("  Registrar transacao:")
    print("    'Recebi R$ 3500 de salario'")
    print("    'Gastei R$ 200 em supermercado'")
    print()
    print("  Investimentos:")
    print("    'Tenho R$ 10000 para investir, sou moderado'")
    print("    'Adicione 100 PETR4 a R$ 35 no portfolio'")
    print()
    print("  Metas:")
    print("    'Crie uma meta de R$ 50000 para emergencia'")
    print()
    print("  Cotacoes:")
    print("    'Qual o preco do Bitcoin?'")
    print("    'Cotacao da PETR4'")
    print("    'Converta 100 dolares para reais'")
    print()


# Mapeamento de comandos rapidos
QUICK_COMMANDS = {
    "saldo": "Qual meu saldo atual?",
    "transacoes": "Liste minhas ultimas 10 transacoes",
    "analise": "Analise minhas financas dos ultimos 30 dias",
    "bitcoin": "Qual o preco do Bitcoin agora?",
    "btc": "Qual o preco do Bitcoin agora?",
    "dolar": "Qual a cotacao do dolar hoje?",
    "usd": "Qual a cotacao do dolar hoje?",
    "euro": "Qual a cotacao do euro hoje?",
    "eur": "Qual a cotacao do euro hoje?",
    "selic": "Qual a taxa Selic atual?",
    "portfolio": "Mostre meu portfolio de investimentos",
    "carteira": "Mostre meu portfolio de investimentos",
    "metas": "Liste minhas metas financeiras",
    "sugestao": "Sugira investimentos para R$ 5000 com perfil moderado",
    "preferencias": "Quais minhas preferencias salvas?",
    "indicadores": "Mostre os indicadores economicos atuais",
}


def main():
    print_header()

    # Inicializa o agente
    print("Inicializando agente...")
    try:
        agent = TaskAgent(verbose=True)
    except Exception as e:
        print(f"Erro ao inicializar: {e}")
        print("Verifique sua GOOGLE_API_KEY no arquivo .env")
        return

    print("Agente pronto!")
    print(f"Tools disponiveis: {len(agent.list_tools())}")

    print_help()
    print_examples()

    print("Digite 'ajuda' para ver comandos ou 'sair' para encerrar.")
    print()

    # Loop interativo
    while True:
        try:
            user_input = input("Voce: ").strip()

            if not user_input:
                continue

            # Comandos do sistema
            lower_input = user_input.lower()

            if lower_input in ["sair", "exit", "quit", "q"]:
                print("\nAte logo! Bons investimentos!")
                break

            if lower_input in ["ajuda", "help", "?"]:
                print_help()
                continue

            if lower_input in ["exemplos", "examples"]:
                print_examples()
                continue

            if lower_input in ["limpar", "clear", "reset"]:
                agent.clear_memory()
                print("Memoria limpa!")
                print()
                continue

            if lower_input in ["tools", "ferramentas"]:
                print("\nFerramentas disponiveis:")
                for tool in agent.list_tools():
                    print(f"  - {tool}")
                print()
                continue

            # Verificar comandos rapidos
            if lower_input in QUICK_COMMANDS:
                user_input = QUICK_COMMANDS[lower_input]
                print(f"-> {user_input}")

            # Processar com o agente
            print()
            print("Processando...")
            print("-" * 40)

            response = agent.run(user_input)

            print("-" * 40)
            print()
            print(f"Agente: {response}")
            print()

        except KeyboardInterrupt:
            print("\n\nAte logo! Bons investimentos!")
            break
        except Exception as e:
            print(f"\nErro: {e}")
            print("Tente novamente.\n")


if __name__ == "__main__":
    main()
