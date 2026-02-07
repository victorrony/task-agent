"""
User Management Module for FinanceAgent Pro
"""

import gradio as gr
import sqlite3
import pandas as pd
from agent.data_service import get_users, DB_PATH

def create_user_mgmt_header():
    """Cria o cabeçalho com a seleção de usuário."""
    users = get_users()
    user_names = [u['name'] for u in users]
    
    with gr.Row():
        with gr.Column(scale=8):
            gr.Markdown("# 💎 FinanceAgent Pro")
            gr.Markdown("Seu assistente financeiro inteligente com suporte multi-perfil.")
        with gr.Column(scale=2):
            user_dropdown = gr.Dropdown(
                choices=user_names, 
                value=user_names[0] if user_names else None,
                label="Perfil Ativo",
                interactive=True
            )
            refresh_btn = gr.Button("🔄 Atualizar Geral", variant="secondary")
            
    return user_dropdown, refresh_btn

def create_user_mgmt_tab():
    """Aba de gerenciamento de perfis."""
    with gr.Tab("👤 Perfis", id="profiles") as tab:
        gr.Markdown("### Gerenciar Perfis de Usuário")
        
        with gr.Row():
            new_user_name = gr.Textbox(placeholder="Nome do novo perfil...", label="Novo Perfil")
            add_user_btn = gr.Button("➕ Criar Perfil", variant="primary")
            
        user_list_df = gr.DataFrame(headers=["ID", "Nome", "Criado em"], label="Perfis Cadastrados")
        delete_user_input = gr.Number(label="ID do Perfil para excluir", precision=0)
        delete_user_btn = gr.Button("🗑️ Excluir Perfil", variant="stop")
        
        status_msg = gr.Markdown("")
        
    return tab, [new_user_name, add_user_btn, user_list_df, delete_user_input, delete_user_btn, status_msg]

def add_user(name):
    """Adiciona um novo usuário ao banco."""
    if not name or name.strip() == "":
        return "Erro: Nome inválido", gr.update()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name) VALUES (?)", (name.strip(),))
        conn.commit()
        conn.close()
        
        # Obter lista atualizada para o dropdown
        users = get_users()
        names = [u['name'] for u in users]
        
        return f"Perfil '{name}' criado com sucesso!", get_users_df(), gr.update(choices=names)
    except Exception as e:
        return f"Erro: {str(e)}", gr.update(), gr.update()

def delete_user(user_id):
    """Exclui um usuário (exceto o principal)."""
    if user_id == 1:
        return "Erro: Não é possível excluir o perfil principal.", gr.update()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # Obter lista atualizada para o dropdown
        users = get_users()
        names = [u['name'] for u in users]
        
        return f"Perfil {user_id} excluído.", get_users_df(), gr.update(choices=names)
    except Exception as e:
        return f"Erro: {str(e)}", gr.update(), gr.update()

def get_users_df():
    """Retorna DataFrame de usuários para a tabela."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name, created_at FROM users", conn)
    conn.close()
    return df
