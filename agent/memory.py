"""
MEMORY LAYER - Gerenciamento de Histórico de Conversa
====================================================
"""

import json
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage, message_to_dict, messages_from_dict
from .db import get_db_connection

class MemoryManager:
    """Gere a persistência de mensagens do LangChain no SQLite."""
    
    def __init__(self, user_id: int, session_id: str = "default"):
        self.user_id = user_id
        self.session_id = session_id

    def save_message(self, message: BaseMessage):
        """Salva uma mensagem no banco de dados."""
        role = "unknown"
        if isinstance(message, HumanMessage): role = "user"
        elif isinstance(message, AIMessage): role = "assistant"
        elif isinstance(message, SystemMessage): role = "system"
        elif isinstance(message, ToolMessage): role = "tool"
        
        # Serialização completa para preservar metadados (tool_calls, IDs, etc)
        message_json = json.dumps(message_to_dict(message))
        content = message.content
        
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO chat_history (user_id, session_id, role, content, message_json) VALUES (?, ?, ?, ?, ?)",
            (self.user_id, self.session_id, role, content, message_json)
        )
        conn.commit()
        conn.close()

    def get_history(self, limit: int = 20) -> List[BaseMessage]:
        """Recupera o histórico de mensagens formatado para o LangChain."""
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT role, content, message_json FROM chat_history WHERE user_id = ? AND session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (self.user_id, self.session_id, limit)
        ).fetchall()
        conn.close()
        
        # Inverter para ordem cronológica
        rows = reversed(rows)
        messages = []
        
        for row in rows:
            if row['message_json']:
                # Tenta carregar do JSON se disponível (muito mais rico)
                try:
                    msg_dict = json.loads(row['message_json'])
                    messages.append(messages_from_dict([msg_dict])[0])
                    continue
                except Exception:
                    pass
            
            # Fallback para o modo antigo (apenas texto)
            role, content = row['role'], row['content']
            if role == "user": messages.append(HumanMessage(content=content))
            elif role == "assistant": messages.append(AIMessage(content=content))
            elif role == "system": messages.append(SystemMessage(content=content))
            elif role == "tool": messages.append(ToolMessage(content=content, tool_call_id="unknown"))
            
        return messages

    def save_audit_log(self, task: str, decision_process: str, tools_used: List[str]):
        """Regista o processo de decisão do agente para auditoria."""
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO audit_logs (user_id, session_id, task, decision_process, tools_used) VALUES (?, ?, ?, ?, ?)",
            (self.user_id, self.session_id, task, decision_process, json.dumps(tools_used))
        )
        conn.commit()
        conn.close()

    def clear_history(self):
        """Remove o histórico da sessão atual."""
        conn = get_db_connection()
        conn.execute(
            "DELETE FROM chat_history WHERE user_id = ? AND session_id = ?",
            (self.user_id, self.session_id)
        )
        conn.commit()
        conn.close()
