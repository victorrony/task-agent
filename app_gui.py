"""
FinanceAgent Pro - Modular & Multi-User Version
===============================================
Interface web premium refatorada para suportar múltiplos perfis e melhor manutenção.
"""

import gradio as gr
from agent import TaskAgent, init_db
from agent.data_service import get_users, get_db_connection, clear_cache
from ui.dashboard import create_dashboard_tab, update_dashboard
from ui.chat import create_chat_tab
from ui.history import create_history_tab, update_history
from ui.connect import create_connect_tab, update_connect
from ui.user_mgmt import create_user_mgmt_header, create_user_mgmt_tab, add_user, delete_user, get_users_df
from ui.components import CUSTOM_CSS
from agent.tools import set_user_id
import pandas as pd

# Inicializa o banco de dados
init_db()

# Inicializa o agente global
try:
    agent = TaskAgent(mode="analista", user_id=1)
    print("FinanceAgent Pro inicializado com sucesso!")
except Exception as e:
    print(f"Erro ao inicializar o agente: {e}")
    agent = None

def get_user_id_from_name(name):
    """Auxiliar para obter ID do usuário pelo nome."""
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row[0] if row else 1

KEYBOARD_SHORTCUTS_JS = """
function() {
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key >= '1' && e.key <= '5') {
            const tabs = document.querySelectorAll('button[id^="tab-button-"]');
            if (tabs[e.key - 1]) {
                tabs[e.key - 1].click();
            }
        }
    });
}
"""

with gr.Blocks(title="FinanceAgent Pro") as demo:
    # Estado do Usuário Ativo (ID)
    current_user_id = gr.State(1)
    
    # CABEÇALHO & SELEÇÃO DE USUÁRIO
    user_dropdown, refresh_btn = create_user_mgmt_header()

    with gr.Tabs() as tabs:
        # TABS MODULARES
        tab_dash, dash_comps = create_dashboard_tab()
        # dash_comps: [balance_card, profit_card, goals_card, alerts_card, expense_pie, balance_line, [quick_btns], goals_progress]
        
        tab_chat, chat_comps = create_chat_tab()
        # chat_comps: [chatbot, msg_input, send_btn, clear_btn, mode_selector]
        
        tab_hist, hist_comps = create_history_tab()
        # hist_comps: [trans_table, btn_export_xlsx, btn_export_pdf, export_file]
        
        tab_conn, conn_comps = create_connect_tab()
        # conn_comps: [status_card, sync_card, sync_bank_btn, sync_output]
        
        tab_prof, prof_comps = create_user_mgmt_tab()
        # prof_comps: [new_user_name, add_user_btn, user_list_df, delete_user_input, delete_user_btn, status_msg]

    # --- LÓGICA DE ATUALIZAÇÃO GERAL ---
    
    def refresh_ui(user_id):
        """Atualiza todos os componentes da interface baseado no usuário logado."""
        # 1. Update Dashboard
        dash_data = update_dashboard(user_id)
        # 2. Update History
        hist_data = update_history(user_id)
        # 3. Update Connect
        conn_data = update_connect(user_id)
        
        return list(dash_data) + [hist_data] + list(conn_data)

    # --- EVENTOS ---

    # Troca de Usuário
    def on_user_change(name):
        uid = get_user_id_from_name(name)
        clear_cache(uid) # Garante dados frescos na troca
        set_user_id(uid)
        return uid, *refresh_ui(uid)

    user_dropdown.change(
        on_user_change, 
        user_dropdown, 
        [current_user_id, *dash_comps[:6], dash_comps[7], hist_comps[0], *conn_comps[:2]]
    )

    refresh_btn.click(
        lambda uid: (clear_cache(uid), *refresh_ui(uid))[1:], 
        current_user_id, 
        [*dash_comps[:6], dash_comps[7], hist_comps[0], *conn_comps[:2]],
        show_progress="full"
    )

    # Chat Events
    def bot_response(history, user_id, mode):
        if not agent: return history
        user_msg = history[-1]["content"]
        
        # Atualiza configurações do agente para o contexto atual
        agent.user_id = user_id
        agent.change_mode(mode)
        
        response = agent.run(user_msg)
        history.append({"role": "assistant", "content": response})
        return history

    chat_comps[1].submit( # msg_input
        lambda msg, h: (h + [{"role": "user", "content": msg}], ""), 
        [chat_comps[1], chat_comps[0]], 
        [chat_comps[0], chat_comps[1]]
    ).then(
        bot_response, [chat_comps[0], current_user_id, chat_comps[4]], chat_comps[0] # chat_comps[4] is mode_selector
    ).then(
        refresh_ui, current_user_id, [*dash_comps[:6], dash_comps[7], hist_comps[0], *conn_comps[:2]]
    )

    chat_comps[2].click( # send_btn
        lambda msg, h: (h + [{"role": "user", "content": msg}], ""), 
        [chat_comps[1], chat_comps[0]], 
        [chat_comps[0], chat_comps[1]]
    ).then(
        bot_response, [chat_comps[0], current_user_id, chat_comps[4]], chat_comps[0]
    ).then(
        refresh_ui, current_user_id, [*dash_comps[:6], dash_comps[7], hist_comps[0], *conn_comps[:2]]
    )

    chat_comps[3].click(lambda: ([], ""), None, [chat_comps[0], chat_comps[1]]) # clear_btn

    # Export Events
    def trigger_export(fmt, user_id):
        from agent.export_service import ExportService
        df = update_history(user_id)
        if df.empty: return gr.update(visible=False)
        service = ExportService()
        path = service.export_to_excel(df) if fmt == "excel" else service.export_to_pdf(df)
        return gr.update(value=path, visible=True) if path else gr.update(visible=False)

    hist_comps[1].click(lambda uid: trigger_export("excel", uid), current_user_id, hist_comps[3])
    hist_comps[2].click(lambda uid: trigger_export("pdf", uid), current_user_id, hist_comps[3])

    # User Mgmt Events
    prof_comps[1].click(add_user, prof_comps[0], [prof_comps[5], prof_comps[2], user_dropdown]) # Adicionar
    prof_comps[4].click(delete_user, prof_comps[3], [prof_comps[5], prof_comps[2], user_dropdown]) # Excluir

    # Bank Sync Events
    def bank_sync_handler(user_id):
        from agent.pluggy_service import PluggyService
        gr.Info("Iniciando sincronização com Pluggy...")
        service = PluggyService()
        res = service.sync_data()
        clear_cache(user_id)
        gr.Info("Sincronização concluída!")
        return res, *refresh_ui(user_id)

    conn_comps[2].click( # sync_bank_btn
        bank_sync_handler, 
        current_user_id, 
        [conn_comps[3], *dash_comps[:6], dash_comps[7], hist_comps[0], *conn_comps[:2]],
        show_progress="full"
    )

    # Lazy Loading for Tabs
    tab_dash.select(update_dashboard, current_user_id, dash_comps[:6]+[dash_comps[7]])
    tab_hist.select(update_history, current_user_id, hist_comps[0])
    tab_conn.select(update_connect, current_user_id, conn_comps[:2])

    # Dashboard Quick Actions
    def quick_action(msg, user_id, history):
        set_user_id(user_id)
        resp = agent.run(msg)
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": resp})
        return history, gr.update(selected="chat")

    dash_comps[6][0].click(lambda uid, h: quick_action("Analise minhas finanças dos últimos 30 dias", uid, h), [current_user_id, chat_comps[0]], [chat_comps[0], tabs])
    dash_comps[6][1].click(lambda uid, h: quick_action("Sugira investimentos para meu perfil", uid, h), [current_user_id, chat_comps[0]], [chat_comps[0], tabs])
    dash_comps[6][2].click(lambda uid, h: quick_action("Mostre meu portfolio", uid, h), [current_user_id, chat_comps[0]], [chat_comps[0], tabs])
    dash_comps[6][3].click(lambda uid, h: quick_action("Quais são minhas metas?", uid, h), [current_user_id, chat_comps[0]], [chat_comps[0], tabs])

    # Inicialização
    demo.load(
        lambda: (get_users_df(), *refresh_ui(1)), 
        None, 
        [prof_comps[2], *dash_comps[:6], dash_comps[7], hist_comps[0], *conn_comps[:2]]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860, 
        show_error=True,
        theme=gr.themes.Soft(primary_hue="emerald"),
        css=CUSTOM_CSS,
        js=KEYBOARD_SHORTCUTS_JS
    )
