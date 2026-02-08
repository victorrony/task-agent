"""
Chat Tab for FinanceAgent Pro
"""

import gradio as gr

def create_chat_tab():
    with gr.Tab("💬 Assistente AI", id="chat") as tab:
        with gr.Row():
            with gr.Column(scale=1, min_width=300) as side_col:
                gr.Markdown("### Personalidade do Agente")
                mode_selector = gr.Dropdown(
                    choices=["Analista", "Educador", "Simulador"],
                    value="Analista",
                    label="Modo de Atendimento",
                    interactive=True
                )
                gr.Markdown("---")
                gr.Markdown("### Exemplos de comandos")
                # Examples will be added here after msg_input is defined
                
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    height=550,
                    placeholder="Olá! Sou seu consultor financeiro. O que vamos planejar hoje?",
                    show_label=False
                )
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Digite aqui (ex: 'Analise meu último mês')...",
                        show_label=False,
                        scale=4,
                    )
                    send_btn = gr.Button("Enviar", variant="primary", scale=1)
                    clear_btn = gr.Button("Limpar", variant="secondary", scale=1)
            
            # Now add Examples to the side column using the available msg_input
            with side_col:
                gr.Markdown(
                    "- Qual meu saldo atual?\n"
                    "- Gastei R$ 50 em farmácia hoje\n"
                    "- Sugira investimentos para R$ 2000\n"
                    "- Como está o preço do Bitcoin?\n"
                    "- Crie uma meta de R$ 10.000 para viagem"
                )
                gr.Markdown("---")
    return tab, [chatbot, msg_input, send_btn, clear_btn, mode_selector]
