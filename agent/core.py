"""
CORE AGENT - O Cérebro do FinanceAgent Pro
==========================================
"""

import os
from pathlib import Path
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage
from .tools import ALL_TOOLS, set_user_id
from .memory import MemoryManager
from .db import init_db

class TaskAgent:
    def __init__(self, mode: str = "analista", user_id: int = 1, session_id: str = "default"):
        init_db()  # Garante que as tabelas existem
        self.user_id = user_id
        self.mode = mode.lower()
        self.memory = MemoryManager(user_id, session_id)
        
        # 1. Configurar LLM
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1)
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self.tool_map = {tool.name: tool for tool in ALL_TOOLS}
        
        # 2. Carregar Prompts
        self.system_prompt = self._load_prompt("system")
        self.mode_prompt = self._load_prompt(self.mode)

    def _load_prompt(self, name: str) -> str:
        """Carrega um arquivo de prompt do diretório agent/prompts/."""
        path = Path(__file__).parent / "prompts" / f"{name}.md"
        if not path.exists():
            return f"Prompt {name} não encontrado."
        return path.read_text(encoding="utf-8")

    def run(self, user_input: str) -> str:
        """Executa o ciclo de raciocínio do agente."""
        set_user_id(self.user_id)
        
        # Preparar Mensagens
        history = self.memory.get_history()
        # Injetar Prompts de Sistema se o histórico estiver vazio ou sempre prefixar
        messages = [
            SystemMessage(content=self.system_prompt),
            SystemMessage(content=self.mode_prompt)
        ] + history
        
        messages.append(HumanMessage(content=user_input))
        self.memory.save_message(messages[-1])

        try:
            # Loop de Raciocínio (máximo 5 iterações de ferramentas)
            for _ in range(5):
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)
                
                if not response.tool_calls:
                    break
                    
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    if tool_name in self.tool_map:
                        result = self.tool_map[tool_name].invoke(tool_args)
                        tool_msg = ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                        messages.append(tool_msg)
            
            final_response = messages[-1].content
            self.memory.save_message(messages[-1])
            return final_response

        except Exception as e:
            return f"❌ Erro operacional: {str(e)}"

    def change_mode(self, new_mode: str):
        """Altera o modo de operação do agente."""
        self.mode = new_mode.lower()
        self.mode_prompt = self._load_prompt(self.mode)
