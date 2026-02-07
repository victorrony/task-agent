"""
USER TOOLS - Gestão de Perfil e Preferências
"""

from langchain_core.tools import tool
import sqlite3
from ..db import get_db_connection

# Reusing the user context
from .finance import CURRENT_USER_ID

@tool
def set_user_preference(key: str, value: str) -> str:
    """
    Define uma preferência ou dado de perfil para o utilizador.
    Exemplos de chaves: 'idade', 'perfil_risco', 'objetivo_principal'.
    
    Args:
        key: A chave da preferência (ex: 'perfil_risco')
        value: O valor a guardar (ex: 'arrojado', '30')
    """
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT OR REPLACE INTO user_preferences (user_id, key, value) VALUES (?, ?, ?)",
            (CURRENT_USER_ID, key.lower(), value.lower())
        )
        conn.commit()
        conn.close()
        return f"✅ Preferência '{key}' definida como '{value}'."
    except Exception as e:
        return f"Erro ao definir preferência: {str(e)}"

@tool
def get_user_profile() -> str:
    """Consulta o perfil e preferências atuais do utilizador."""
    try:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT key, value FROM user_preferences WHERE user_id = ?",
            (CURRENT_USER_ID,)
        ).fetchall()
        conn.close()
        
        if not rows: return "Nenhuma preferência definida ainda."
        
        res = "📋 PERFIL DO UTILIZADOR:\n"
        for r in rows:
            res += f"- {r['key'].capitalize()}: {r['value']}\n"
        return res
    except Exception as e:
        return f"Erro ao consultar perfil: {str(e)}"
