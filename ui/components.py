"""
UI Components & Styles for FinanceAgent Pro
"""

import gradio as gr

# CSS Moderno e Responsivo
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

.gradio-container {
    font-family: 'Inter', sans-serif !important;
}

.stat-card {
    padding: 24px !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    border: 1px solid #e5e7eb !important;
    background-color: white !important;
    text-align: center !important;
    transition: transform 0.2s ease-in-out !important;
}

.stat-card:hover {
    transform: translateY(-2px) !important;
}

.stat-card .label {
    font-size: 0.875rem !important;
    color: #6b7280 !important;
    font-weight: 600 !important;
    margin-bottom: 4px !important;
}

.stat-card .value {
    font-size: 1.5rem !important;
    color: #111827 !important;
    font-weight: 700 !important;
}

.chart-container {
    background: white !important;
    border-radius: 16px !important;
    padding: 16px !important;
    border: 1px solid #e5e7eb !important;
}

.footer-text {
    font-size: 0.8rem !important;
    color: #9ca3af !important;
    margin-top: 40px !important;
    text-align: center !important;
}
"""

def create_stat_card(label, value, color=None):
    """Gera o HTML para um card de estatística."""
    style = f"style='color: {color}'" if color else ""
    return f"<div class='stat-card'><div class='label'>{label}</div><div class='value' {style}>{value}</div></div>"
