"""
Dashboard Tab for FinanceAgent Pro
"""

import gradio as gr
from .components import create_stat_card
from agent.data_service import get_quick_stats, get_expense_chart, get_balance_history_chart, get_transactions_df, get_goals_progress

def create_dashboard_tab():
    with gr.Tab("📊 Dashboard", id="dash") as tab:
        with gr.Row():
            balance_card = gr.HTML(value="")
            profit_card = gr.HTML(value="")
            goals_card = gr.HTML(value="")
            alerts_card = gr.HTML(value="")

        with gr.Row():
            with gr.Column(scale=1, elem_classes="chart-container"):
                expense_pie = gr.Plot(value=None, label="Distribuição de Gastos")
            with gr.Column(scale=1, elem_classes="chart-container"):
                balance_line = gr.Plot(value=None, label="Evolução do Saldo")

        gr.Markdown("### ⚡ Ações Rápidas")
        with gr.Row():
            btn_ana = gr.Button("🔍 Analisar Gastos", size="sm")
            btn_inv = gr.Button("📈 Sugerir Investimentos", size="sm")
            btn_por = gr.Button("💼 Ver Portfolio", size="sm")
            btn_met = gr.Button("🎯 Ver Metas", size="sm")

        gr.Markdown("### 🎯 Progresso das Metas")
        goals_progress_box = gr.HTML(value="<p style='color: #666;'>Nenhuma meta ativa no momento.</p>")
            
    return tab, [balance_card, profit_card, goals_card, alerts_card, expense_pie, balance_line, [btn_ana, btn_inv, btn_por, btn_met], goals_progress_box]

def update_dashboard(user_id=1):
    """Atualiza os componentes do dashboard para um usuário."""
    stats = get_quick_stats(user_id)
    
    # Formatação HTML para os cards
    b_html = create_stat_card("Saldo Total", stats['balance'])
    
    p = stats['profit']
    p_color = "#10b981" if "Erro" not in p and "-" not in p else "#ef4444"
    p_html = create_stat_card("Resultado Mensal", p, color=p_color)
    
    g_html = create_stat_card("Metas Ativas", stats['goals'])
    
    a = stats['status']
    a_color = "#ef4444" if a == "🚨 Dívida" else "#f59e0b" if a == "⚠️ Reserva" else "#10b981"
    a_html = create_stat_card("Status de Saúde", a, color=a_color)

    pie = get_expense_chart(user_id)
    line = get_balance_history_chart(user_id)
    
    # Gerar HTML para as metas
    goals = get_goals_progress(user_id)
    goals_html = ""
    if not goals:
        goals_html = "<p style='color: #666;'>Nenhuma meta ativa no momento.</p>"
    else:
        for g in goals:
            color = "#10b981" if g['priority'] == 'alta' else "#3b82f6" if g['priority'] == 'media' else "#6b7280"
            goals_html += f"""
            <div style="margin-bottom: 12px; background: white; padding: 12px; border-radius: 8px; border: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 600; color: #374151;">{g['name']}</span>
                    <span style="font-size: 0.875rem; color: #6b7280;">R$ {g['current']:,.2f} / R$ {g['target']:,.2f}</span>
                </div>
                <div style="width: 100%; background-color: #f3f4f6; border-radius: 9999px; height: 10px;">
                    <div style="background-color: {color}; height: 10px; border-radius: 9999px; width: {g['percent']}%"></div>
                </div>
            </div>
            """
    
    return b_html, p_html, g_html, a_html, pie, line, goals_html
