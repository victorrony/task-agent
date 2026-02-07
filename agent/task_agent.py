"""
TASK AGENT - O Cérebro do Agente (Com Memória)
==============================================

Este agente agora possui MEMÓRIA, permitindo conversas fluidas.
"""

import os
from typing import List
from .memory import MemoryManager
from .tools.finance import set_user_id
from .logic import FinancialAdvisor

# Carrega variáveis de ambiente (.env)
load_dotenv()


class TaskAgent:
    """
    Agente executor de tarefas com memória persistente camadada e lógica proativa.
    """
    
    def __init__(self, user_id: int = 1, session_id: str = "default", model: str = None, verbose: bool = True, auditor_mode: bool = False):
        self.verbose = verbose
        self.user_id = user_id
        self.session_id = session_id
        self.auditor_mode = auditor_mode
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 1: LLM (O Cérebro)
        # ═══════════════════════════════════════════════════════════
        model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
        )
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 2: MEMÓRIA PERSISTENTE
        # ═══════════════════════════════════════════════════════════
        self.memory = MemoryManager(user_id=user_id, session_id=session_id)
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 3: PROMPT DE SISTEMA - ASSISTENTE FINANCEIRO
        # ═══════════════════════════════════════════════════════════
        self.base_system_prompt = """### IDENTIDADE
Tu és o **FinanceAgent Pro**, um Assistente Financeiro Inteligente especializado em
**gestão financeira pessoal, investimentos e construção de patrimônio**, atuando
tanto na realidade económica de **Cabo Verde (CVE)** quanto em **mercados globais**.

---

## 🏗️ Ciclo de Vida do Raciocínio
1. Analisar Factos e Perfil do utilizador.
2. Identificar riscos imediatos (Regra 0).
3. Selecionar Tools se necessário.
4. Validar contra Hard Limits financeiros.
5. Responder de forma educativa e direta.

---

## 🧠 Arquitetura de Memória Camadada
O teu contexto atual está dividido em camadas para evitar confusão:
- **L2 (Perfil)**: Identidade e preferências do utilizador.
- **L3 (Factos)**: Dados financeiros reais extraídos da base de dados.
- **L1 (Conversação)**: Histórico recente de chat.

---

## 🧭 Lógica de Segurança (Regra 0)
Se a reserva for < 6 meses: PRIORIDADE SEGURANÇA.
Se houver dívidas: PRIORIDADE LIQUIDAÇÃO.

---

## 🎯 Objetivo Final
Capacitar o utilizador a dominar suas finanças em Cabo Verde e alcançar liberdade financeira com disciplina.
"""
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 4: TOOLS
        # ═══════════════════════════════════════════════════════════
        self.tools = ALL_TOOLS
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_map = {tool.name: tool for tool in self.tools}
    
    def _get_layered_context(self) -> str:
        """Coleta dados para as camadas L2 (Perfil) e L3 (Factos)."""
        advisor = FinancialAdvisor(self.user_id)
        status = advisor.get_user_status()
        
        context = "\n\n### [MEMÓRIA CAMADADA]\n"
        
        # L2: Perfil
        context += "#### L2: PERFIL DO UTILIZADOR\n"
        context += f"- Idade: {status['age']}\n"
        context += f"- Perfil de Risco: {status['risk_profile'] or 'Não definido'}\n"
        if status['is_new_user']:
            context += "- Estado: Onboarding pendente.\n"
            
        # L3: Factos
        context += "\n#### L3: FACTOS FINANCEIROS (REAIS)\n"
        context += f"- Saldo Atual: CVE {status['balance']:,.2f}\n"
        context += f"- Média Despesas/Mês: CVE {status['monthly_expenses']:,.2f}\n"
        context += f"- Reserva Atual: {status['reserve_months']:.1f} meses de cobertura.\n"
        context += f"- Taxa de Poupança (30d): {status['savings_rate']*100:.1f}%\n"
        context += f"- Dívidas Ativas: {'Sim' if status['has_debt'] else 'Não'}\n"
        
        if status['reserve_months'] < 6:
            context += "\n⚠️ INSTRUÇÃO CRÍTICA: Reserva insuficiente. Aplique Regra 0.\n"
            
        return context

    def run(self, task: str) -> str:
        """
        Executa uma tarefa usando o histórico persistente e contexto injetado.
        """
        set_user_id(self.user_id)
        tools_used = []
        
        try:
            # 1. Recupera Histórico (L1)
            messages = self.memory.get_history(limit=15)
            
            # 2. Injeta Memória L2 e L3 no System Prompt
            full_system_prompt = self.base_system_prompt + self._get_layered_context()
            
            if self.auditor_mode:
                full_system_prompt += "\n\n### MODO AUDITOR ATIVO\nJustifique as suas decisões no final da resposta."

            if not messages:
                messages = [SystemMessage(content=full_system_prompt)]
            else:
                if isinstance(messages[0], SystemMessage):
                    messages[0] = SystemMessage(content=full_system_prompt)
                else:
                    messages.insert(0, SystemMessage(content=full_system_prompt))

            # 3. Adiciona input e salva
            user_msg = HumanMessage(content=task)
            messages.append(user_msg)
            self.memory.save_message(user_msg)
            
            # 4. Loop de Raciocínio
            iteration = 0
            reasoning_path = []
            
            while iteration < 5:
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)
                self.memory.save_message(response)
                
                if not response.tool_calls:
                    # Finaliza e salva auditoria
                    self.memory.save_audit_log(task, "\n".join(reasoning_path), tools_used)
                    return response.content
                
                # Execução de ferramentas
                for tool_call in response.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    tools_used.append(t_name)
                    reasoning_path.append(f"Chamada de Tool: {t_name} com args {t_args}")
                    
                    if self.verbose: print(f"🔧 Tool: {t_name}({t_args})")
                    
                    if t_name in self.tool_map:
                        result = self.tool_map[t_name].invoke(t_args)
                        tool_msg = ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                        messages.append(tool_msg)
                        self.memory.save_message(tool_msg)
                        reasoning_path.append(f"Resultado de {t_name}: {result}")
                
                iteration += 1
                
            return "❌ Limite de iterações atingido."
                
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return f"❌ Erro Crítico: {str(e)}"
    
    def clear_memory(self):
        """Limpa o histórico da conversa no banco."""
        self.memory.clear_history()
    
    def list_tools(self) -> list:
        return [tool.name for tool in self.tools]
