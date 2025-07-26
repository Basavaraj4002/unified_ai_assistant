import pandas as pd
from fpdf import FPDF
import os

REPORTS_DIR = "reports"

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'AI Document Assistant - Eligibility Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 6, title, 0, 1, 'L')
        self.ln(4)

    def add_dataframe_to_pdf(self, df: pd.DataFrame, title: str):
        if df.empty: return
        self.chapter_title(title)
        
        num_cols = len(df.columns)
        effective_page_width = self.w - 2 * self.l_margin
        col_width = effective_page_width / num_cols

        self.set_font('Arial', 'B', 8)
        for col in df.columns: self.cell(col_width, 8, str(col), 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 8)
        for _, row in df.iterrows():
            for item in row: self.cell(col_width, 8, str(item), 1, 0, 'C')
            self.ln()
        self.ln(10)

def create_eligibility_report_pdf(analysis_results: dict, assessment_name: str) -> str:
    """Generates a detailed PDF report from the analysis results."""
    if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font('Arial', '', 12)
    pdf.chapter_title(f"Analysis for: {assessment_name}")

    pdf.add_dataframe_to_pdf(pd.DataFrame(analysis_results['top_5_students']), "Top 5 Students")
    pdf.add_dataframe_to_pdf(pd.DataFrame(analysis_results['bottom_5_students']), "Bottom 5 Students")
    pdf.add_dataframe_to_pdf(pd.DataFrame(analysis_results['eligible_students']), "Eligible Students")
    pdf.add_dataframe_to_pdf(pd.DataFrame(analysis_results['non_eligible_students']), "Non-Eligible Students")
    pdf.add_dataframe_to_pdf(pd.DataFrame(analysis_results['full_ranked_list']), "Full Ranked Merit List")
    
    report_filename = f"Eligibility_Report_{assessment_name.replace(' ', '_')}.pdf"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    pdf.output(report_path)
    
    return report_path