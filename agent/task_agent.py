"""
TASK AGENT - O Cérebro do Agente (Com Memória)
==============================================

Este agente agora possui MEMÓRIA, permitindo conversas fluidas.
"""

import os
from typing import List, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from .memory import MemoryManager
from .tools import set_user_id, ALL_TOOLS
from .logic import FinancialAdvisor

# Carrega variáveis de ambiente (.env)
load_dotenv()


def _normalize_content(content: Any) -> str:
    """
    Normaliza response.content do Gemini 2.5 para string.

    O Gemini 2.5 pode retornar:
    - String simples: "texto"
    - Lista de objetos: [{type: "text", text: "...", extras: ...}, ...]

    Esta função sempre retorna uma string.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        # Extrai o texto de cada objeto e concatena
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Tenta extrair do campo 'text' primeiro
                if 'text' in item:
                    text_parts.append(str(item['text']))
                # Fallback: pega qualquer campo de texto
                elif 'content' in item:
                    text_parts.append(str(item['content']))
                else:
                    # Se não encontrou campo de texto, converte o dict inteiro
                    text_parts.append(str(item))
            else:
                text_parts.append(str(item))
        return ''.join(text_parts)

    # Fallback: converte para string
    return str(content) if content else ""


class TaskAgent:
    """
    Agente executor de tarefas com memória persistente camadada e lógica proativa.
    """
    
    def __init__(self, user_id: int = 1, session_id: str = "default", model: str = None, mode: str = "assistant", verbose: bool = True, auditor_mode: bool = False):
        self.verbose = verbose
        self.user_id = user_id
        self.session_id = session_id
        self.auditor_mode = auditor_mode
        self.mode = mode.lower()
        
        # Cache para Contexto Camadado (L2/L3) - Expira em 5 minutos
        self._context_cache = None
        self._context_cache_time = None
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 1: LLM (O Cérebro)
        # ═══════════════════════════════════════════════════════════
        model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 2: MEMÓRIA PERSISTENTE
        # ═══════════════════════════════════════════════════════════
        self.memory = MemoryManager(user_id=user_id, session_id=session_id)
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 3: PROMPT DE SISTEMA
        # ═══════════════════════════════════════════════════════════
        try:
            prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
            with open(os.path.join(prompt_dir, "system.md"), "r", encoding="utf-8") as f:
                core_prompt = f.read()
            
            mode_prompt = ""
            if self.mode != "assistant":
                mode_file = f"{self.mode}.md"
                mode_path = os.path.join(prompt_dir, mode_file)
                if os.path.exists(mode_path):
                    with open(mode_path, "r", encoding="utf-8") as f:
                        mode_prompt = f"\n\n--- \n\n{f.read()}"
            
            self.base_system_prompt = core_prompt + mode_prompt
        except Exception as e:
            self.base_system_prompt = "Tu és o FinanceAgent Pro, um Assistente Financeiro especializado em Cabo Verde."
            if self.verbose: print(f"⚠️ Erro ao carregar prompts: {e}")
        
        # ═══════════════════════════════════════════════════════════
        # PEÇA 4: TOOLS
        # ═══════════════════════════════════════════════════════════
        self.tools = ALL_TOOLS
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_map = {tool.name: tool for tool in self.tools}

    def _get_layered_context(self) -> str:
        """Coleta dados para as camadas L2 (Perfil) e L3 (Factos) com Cache."""
        from datetime import datetime, timedelta
        
        # Verifica Cache (5 min)
        if self._context_cache and self._context_cache_time:
            if datetime.now() - self._context_cache_time < timedelta(minutes=5):
                return self._context_cache

        advisor = FinancialAdvisor(self.user_id)
        status = advisor.get_user_status()
        
        context = "\n\n### [MEMÓRIA CAMADADA (L2/L3)]\n"
        context += "#### L2: PERFIL DO UTILIZADOR\n"
        context += f"- Idade: {status['age']} | Perfil: {status['risk_profile'] or 'Automático'}\n"
        
        context += "\n#### L3: FACTOS FINANCEIROS\n"
        context += f"- Saldo: CVE {status['balance']:,.2f} | Poupança: {status['savings_rate']*100:.1f}%\n"
        context += f"- Reserva: {status['reserve_months']:.1f} meses | Dívidas: {'Sim' if status['has_debt'] else 'Não'}\n"
        
        if status['reserve_months'] < 6:
            context += "\n⚠️ CRÍTICO: Reserva insuficiente. Priorizar REGRA 0.\n"
            
        self._context_cache = context
        self._context_cache_time = datetime.now()
        return context

    def _classify_intent(self, task: str, history: List[BaseMessage]) -> dict:
        """Classifica a intenção, nível de risco e necessidade de ferramentas."""
        system_msg = SystemMessage(content="""Tu és o Classificador de Intenções do FinanceAgent Pro.
Analisa o pedido do utilizador e responde EXCLUSIVAMENTE com um JSON:
{
  "intent": "ANALISE" | "REGISTO" | "SIMULACAO" | "EDUCACAO" | "OUTRO",
  "requires_tools": boolean,
  "risk_level": "BAIXO" | "MEDIO" | "ALTO",
  "reasoning": "porque?"
}""")
        recent_history = history[-3:] if history else []
        messages = [system_msg] + recent_history + [HumanMessage(content=f"Tarefa: {task}")]

        try:
            response = self.llm.invoke(messages)
            import json
            # Normaliza content para string (corrige Gemini 2.5)
            content = _normalize_content(response.content)
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception:
            return {"intent": "OUTRO", "requires_tools": True, "risk_level": "MEDIO", "reasoning": "Erro na classificação."}

    def _generate_plan(self, intent_data: dict, task: str) -> str:
        """Gera um plano de execução de alto nível."""
        plan_prompt = f"Cria um plano de 1-3 passos para resolver: '{task}'. Intenção: {intent_data['intent']}. Responde em 1 linha."
        response = self.llm.invoke([SystemMessage(content="Tu és um planeador de tarefas financeiras."), HumanMessage(content=plan_prompt)])
        # Normaliza content para string (corrige Gemini 2.5)
        return _normalize_content(response.content)

    def run(self, task: str) -> str:
        """Executa a tarefa com Ciclo de Vida Industrial e Auditoria L4 Detalhada."""
        set_user_id(self.user_id)
        tools_used = []
        reasoning_path = []
        
        try:
            # 1. Preparação & Contexto
            history = self.memory.get_history(limit=10)
            layered_context = self._get_layered_context()
            
            # 2. Intenção & Planeamento
            intent_data = self._classify_intent(task, history)
            plan = self._generate_plan(intent_data, task)
            
            # Audit L4: Registo de Início e Intenção
            reasoning_path.append(f"INÍCIO: Tarefa '{task}'")
            reasoning_path.append(f"INTENT: {intent_data['intent']} (Risco: {intent_data['risk_level']})")
            reasoning_path.append(f"PLANO: {plan}")

            # 3. Execução (Loop de Raciocínio)
            full_system_prompt = self.base_system_prompt + layered_context
            full_system_prompt += f"\n\n### PLANO DE EXECUÇÃO\n{plan}"
            
            if self.auditor_mode:
                full_system_prompt += "\n\n### MODO AUDITOR ATIVO\nJustifique cada decisão tecnicamente no final."

            # Montagem e Sanitização de Mensagens
            system_content = full_system_prompt.strip() or "System ready."
            messages = [SystemMessage(content=system_content)]
            
            # Filtra histórico inválido e garante string
            for msg in history:
                if msg.content is not None:
                    # Força string e remove vazios
                    s_content = str(msg.content).strip()
                    if s_content:
                        msg.content = s_content
                        messages.append(msg)
            
            # Adiciona mensagem atual
            if not task or not task.strip():
                return "❌ Erro: Mensagem vazia."
            
            user_msg = HumanMessage(content=str(task).strip())
            messages.append(user_msg)
            self.memory.save_message(user_msg)
            
            iteration = 0
            while iteration < 5:
                # DEBUG: Imprimir estrutura para identificar falhas
                if self.verbose:
                    print(f"--- Iteration {iteration} Messages ---")
                    for m in messages:
                        print(f"[{m.type}] {str(m.content)[:50]}...")
                
                try:
                    response = self.llm_with_tools.invoke(messages)
                except Exception as invoke_err:
                    print(f"❌ ERRO INVOKE: {invoke_err}")
                    return f"❌ Erro na API do Modelo: {str(invoke_err)}"

                messages.append(response)
                self.memory.save_message(response)
                
                if not response.tool_calls:
                    # Finalização com sucesso
                    reasoning_path.append("FIM: Tarefa concluída sem mais chamadas.")
                    self.memory.save_audit_log(task, "\n".join(reasoning_path), tools_used)
                    # Normaliza content para string (corrige Gemini 2.5)
                    return _normalize_content(response.content)
                
                # Execução de Ferramentas com Validação e Log L4
                for tool_call in response.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    tools_used.append(t_name)
                    
                    if t_name in self.tool_map:
                        result = self.tool_map[t_name].invoke(t_args)
                        
                        # Validação de Segurança/Erro
                        status_trace = "SUCESSO"
                        if isinstance(result, dict) and "error" in result:
                            status_trace = f"ERRO: {result['error']}"
                        
                        reasoning_path.append(f"STEP {iteration+1}: Chamada {t_name}({t_args}) -> {status_trace}")
                        
                        tool_msg = ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                        messages.append(tool_msg)
                        self.memory.save_message(tool_msg)
                
                iteration += 1
                
            # Fallback de Limite
            alert_msg = "❌ LIMITE ATINGIDO: O agente não conseguiu resolver a tarefa em 5 iterações."
            reasoning_path.append(alert_msg)
            self.memory.save_audit_log(task, "\n".join(reasoning_path), tools_used)
            return alert_msg
                
        except Exception as e:
            error_trace = f"❌ ERRO CRÍTICO: {str(e)}"
            reasoning_path.append(error_trace)
            self.memory.save_audit_log(task, "\n".join(reasoning_path), tools_used)
            return error_trace
    
    def clear_memory(self):
        """Limpa o histórico da conversa no banco."""
        self.memory.clear_history()
    
    def list_tools(self) -> list:
        return [tool.name for tool in self.tools]
