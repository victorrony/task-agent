"""
Connect Tab for FinanceAgent Pro
"""

import gradio as gr
from datetime import datetime
from .components import create_stat_card

def create_connect_tab():
    with gr.Tab("🔌 Conectar", id="connect") as tab:
        gr.Markdown("### Conectar sua Conta Bancária")
        gr.Markdown("""
        O FinanceAgent Pro usa o **Open Finance (Pluggy)** para se conectar aos seus bancos de forma segura.
        
        **Como funciona:**
        1. No modo Real, você usará o Connect Widget para autorizar o acesso.
        2. Atualmente em **Modo Sandbox** (Simulação).
        3. O acesso é **somente leitura** (não podemos fazer transferências).
        """)
        
        with gr.Row():
            status_card = gr.HTML(value="")
            sync_card = gr.HTML(value="")

        sync_bank_btn = gr.Button("🔄 Sincronizar Dados Bancários agora", variant="primary", size="lg")
        sync_output = gr.Markdown("")
        
    return tab, [status_card, sync_card, sync_bank_btn, sync_output]

def update_connect(user_id=1):
    """Atualiza os cards da aba conectar."""
    # Placeholder para lógica real de status por usuário
    status_html = create_stat_card("Status da Conexão", "🟢 Conectado (Sandbox)")
    sync_html = create_stat_card("Última Sincronização", datetime.now().strftime("%d/%m %H:%M"))
    return status_html, sync_html
