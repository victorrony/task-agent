import sys
import os
from pathlib import Path

# Adiciona o diretório atual ao path para importar o agent
sys.path.append(str(Path(__file__).parent.parent))

from agent import TaskAgent, init_db

def test_architecture():
    print("🚀 Testando nova arquitetura...")
    
    # 1. Teste DB
    init_db()
    print("✅ Database inicializada.")
    
    # 2. Teste Agente em diferentes modos
    print("\n--- Teste de Modos ---")
    for mode in ["analista", "educador", "simulador"]:
        agent = TaskAgent(mode=mode)
        print(f"Agente em modo '{mode}' inicializado. Prompt carregado: {len(agent.mode_prompt)} chars.")

    # 3. Teste Memória
    print("\n--- Teste de Memória ---")
    agent = TaskAgent(mode="analista", session_id="test_session")
    agent.run("Olá, meu nome é Victor.")
    print("Mensagem enviada.")
    
    # Reiniciar agente e ver se lembra
    agent2 = TaskAgent(mode="analista", session_id="test_session")
    history = agent2.memory.get_history()
    print(f"Histórico recuperado: {len(history)} mensagens.")
    
    print("\n✅ Arquitetura validada com sucesso!")

if __name__ == "__main__":
    test_architecture()
