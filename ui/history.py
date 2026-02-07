"""
History Tab for FinanceAgent Pro
"""

import gradio as gr
from agent.data_service import get_transactions_df

def create_history_tab():
    with gr.Tab("📄 Extrato", id="history") as tab:
        gr.Markdown("### Histórico Detalhado de Transações")
        
        with gr.Row():
            btn_export_xlsx = gr.Button("📥 Exportar Excel", variant="secondary", size="sm")
            btn_export_pdf = gr.Button("📥 Exportar PDF", variant="secondary", size="sm")
        
        export_file = gr.File(label="Download do Relatório", visible=False)
        
        trans_table = gr.DataFrame(value=None, interactive=False)
        
    return tab, [trans_table, btn_export_xlsx, btn_export_pdf, export_file]

def update_history(user_id=1):
    """Atualiza a tabela de transações."""
    return get_transactions_df(user_id)
