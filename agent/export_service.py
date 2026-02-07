import os
import pandas as pd
from fpdf import FPDF
from datetime import datetime

class ExportService:
    @staticmethod
    def export_to_excel(df, filename="relatorio_financeiro.xlsx"):
        """Exporta um DataFrame para um arquivo Excel."""
        try:
            # Ensure directory exists
            os.makedirs("exports", exist_ok=True)
            filepath = os.path.join("exports", filename)
            
            # Export to Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            return filepath
        except Exception as e:
            print(f"Erro ao exportar Excel: {e}")
            return None

    @staticmethod
    def export_to_pdf(df, filename="relatorio_financeiro.pdf", title="Relatório Financeiro"):
        """Gera um PDF formatado a partir de um DataFrame de transações."""
        try:
            os.makedirs("exports", exist_ok=True)
            filepath = os.path.join("exports", filename)
            
            pdf = FPDF()
            pdf.add_page()
            
            # Header
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, title, ln=True, align="C")
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align="C")
            pdf.ln(5)
            
            # Summary stats
            total_in = df[df['type'] == 'entrada']['amount'].sum()
            total_out = df[df['type'] == 'saida']['amount'].sum()
            balance = total_in - total_out
            
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 10, "Resumo Financeiro do Período", ln=True)
            pdf.set_font("helvetica", "", 11)
            pdf.cell(60, 8, f"Total Entradas: R$ {total_in:,.2f}", ln=True)
            pdf.cell(60, 8, f"Total Saídas: R$ {total_out:,.2f}", ln=True)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(60, 8, f"Resultado: R$ {balance:,.2f}", ln=True)
            pdf.ln(10)
            
            # Table Header
            pdf.set_font("helvetica", "B", 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(25, 10, "Data", 1, 0, "C", True)
            pdf.cell(80, 10, "Descrição", 1, 0, "C", True)
            pdf.cell(30, 10, "Categoria", 1, 0, "C", True)
            pdf.cell(25, 10, "Tipo", 1, 0, "C", True)
            pdf.cell(30, 10, "Valor", 1, 1, "C", True)
            
            # Table Rows
            pdf.set_font("helvetica", "", 9)
            for _, row in df.iterrows():
                # Handling multi-line descriptions if needed (simple version for now)
                desc = str(row['description'])[:45] 
                cat = str(row['category'])[:15]
                
                pdf.cell(25, 8, str(row['date']), 1, 0, "C")
                pdf.cell(80, 8, desc, 1, 0, "L")
                pdf.cell(30, 8, cat, 1, 0, "C")
                pdf.cell(25, 8, str(row['type']).capitalize(), 1, 0, "C")
                
                # Color based on type
                if row['type'] == 'entrada':
                    pdf.set_text_color(16, 185, 129) # Emerald
                else:
                    pdf.set_text_color(239, 68, 68) # Red
                
                pdf.cell(30, 8, f"R$ {row['amount']:,.2f}", 1, 1, "R")
                pdf.set_text_color(0, 0, 0) # Reset color
                
            pdf.output(filepath)
            return filepath
        except Exception as e:
            print(f"Erro ao exportar PDF: {e}")
            return None
