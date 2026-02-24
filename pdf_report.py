"""
PDF Report Generator for Log Performance Metrics Dashboard
"""

import io
import tempfile
import os
from datetime import datetime
from fpdf import FPDF


class ReportPDF(FPDF):
    """Custom PDF class with header/footer for reports."""

    def __init__(self, title='Log Performance Report', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = title
        self._setup_fonts()

    def _setup_fonts(self):
        """Setup fonts with Korean support."""
        font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        os.makedirs(font_dir, exist_ok=True)
        # Use built-in Helvetica as fallback
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, self.report_title, align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 8)
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', align='C', new_x='LMARGIN', new_y='NEXT')
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, title, fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(3)

    def add_summary_table(self, headers, rows, col_widths=None):
        """Add a formatted table to the PDF."""
        if col_widths is None:
            available_width = 190
            col_widths = [available_width / len(headers)] * len(headers)

        # Header
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(60, 60, 60)
        self.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, str(header), border=1, fill=True, align='C')
        self.ln()

        # Rows
        self.set_font('Helvetica', '', 9)
        self.set_text_color(0, 0, 0)
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(248, 248, 248)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, str(cell), border=1, fill=True, align='C')
            self.ln()
        self.ln(3)

    def add_chart_image(self, fig, width=180):
        """Add a Plotly chart as image to the PDF."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            fig.write_image(tmp_path, width=1200, height=500, scale=2)
            self.image(tmp_path, x=15, w=width)
            self.ln(5)
        except Exception:
            self.set_font('Helvetica', 'I', 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 8, '(Chart image not available in this environment)', new_x='LMARGIN', new_y='NEXT')
            self.set_text_color(0, 0, 0)
            self.ln(3)

            # Add chart data as table if available
            if hasattr(fig, 'data') and fig.data:
                for trace in fig.data[:3]:
                    if hasattr(trace, 'name') and trace.name:
                        self.set_font('Helvetica', '', 8)
                        self.cell(0, 5, f'  - {trace.name}', new_x='LMARGIN', new_y='NEXT')
                self.ln(2)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def add_key_value(self, key, value):
        """Add a key-value pair line."""
        self.set_font('Helvetica', 'B', 9)
        self.cell(60, 6, str(key), new_x='END')
        self.set_font('Helvetica', '', 9)
        self.cell(0, 6, str(value), new_x='LMARGIN', new_y='NEXT')

    def get_pdf_bytes(self):
        """Return PDF as bytes."""
        return bytes(self.output())


def generate_dns_report(df_filtered, domains, figures, compare_df):
    """Generate DNS performance PDF report.

    Args:
        df_filtered: Filtered DataFrame
        domains: List of domain names
        figures: Dict of plotly figures {name: fig}
        compare_df: Domain comparison DataFrame
    """
    pdf = ReportPDF(title='DNS Performance Report')
    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. Overview
    pdf.section_title('1. Overview')
    pdf.add_key_value('Report Period',
                      f'{df_filtered["timestamp"].min().strftime("%Y-%m-%d %H:%M")} ~ '
                      f'{df_filtered["timestamp"].max().strftime("%Y-%m-%d %H:%M")}')
    pdf.add_key_value('Total Records', f'{len(df_filtered):,}')
    pdf.add_key_value('Domains', f'{len(domains)}')
    for d in domains:
        pdf.add_key_value(f'  - {d}', '')
    pdf.ln(3)

    # 2. Domain Summary
    pdf.section_title('2. Domain Summary')
    headers = ['Domain', 'Avg(ms)', 'P95(ms)', 'P99(ms)', 'Max(ms)', 'Total', 'Fail', 'Fail%']
    rows = []
    for _, row in compare_df.iterrows():
        domain_name = str(row['Domain'])
        if len(domain_name) > 25:
            domain_name = domain_name[:22] + '...'
        rows.append([
            domain_name,
            f'{row["평균 응답(ms)"]:.1f}',
            f'{row["P95 (ms)"]:.1f}',
            f'{row["P99 (ms)"]:.1f}',
            f'{row["최대 응답(ms)"]:.0f}',
            f'{int(row["총 조회수"]):,}',
            f'{int(row["총 실패수"]):,}',
            f'{row["실패율(%)"]:.2f}%',
        ])
    col_widths = [45, 18, 18, 18, 18, 25, 22, 22]
    pdf.add_summary_table(headers, rows, col_widths)

    # 3. Charts
    if 'response_time' in figures:
        pdf.add_page()
        pdf.section_title('3. Response Time Timeline (Avg / P95 / P99)')
        pdf.add_chart_image(figures['response_time'])

    if 'max_response' in figures:
        pdf.add_page()
        pdf.section_title('4. Max Response Time Timeline')
        pdf.add_chart_image(figures['max_response'])

    if 'fail_rate' in figures:
        pdf.add_page()
        pdf.section_title('5. Fail Rate Timeline')
        pdf.add_chart_image(figures['fail_rate'])

    if 'compare_resp' in figures:
        pdf.add_page()
        pdf.section_title('6. Domain Comparison - Response Time')
        pdf.add_chart_image(figures['compare_resp'])

    if 'compare_count' in figures:
        pdf.section_title('7. Domain Comparison - Query Count')
        pdf.add_chart_image(figures['compare_count'])

    return pdf.get_pdf_bytes()


def generate_web_response_report(df_filtered, summary_df, figures):
    """Generate Web Access response time PDF report.

    Args:
        df_filtered: Filtered DataFrame
        summary_df: Summary statistics DataFrame
        figures: Dict of plotly figures {name: fig}
    """
    pdf = ReportPDF(title='Web Access - Response Time Report')
    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. Overview
    pdf.section_title('1. Overview')
    pdf.add_key_value('Report Period',
                      f'{df_filtered["timestamp"].min().strftime("%Y-%m-%d %H:%M")} ~ '
                      f'{df_filtered["timestamp"].max().strftime("%Y-%m-%d %H:%M")}')
    pdf.add_key_value('Total Requests', f'{len(df_filtered):,}')
    if 'status' in df_filtered.columns:
        success_rate = (df_filtered['status'] == 200).sum() / len(df_filtered) * 100
        pdf.add_key_value('Success Rate (200)', f'{success_rate:.1f}%')
    if 'rt' in df_filtered.columns:
        pdf.add_key_value('Avg Response Time', f'{df_filtered["rt"].mean():.3f}s')
    pdf.ln(3)

    # 2. Performance Summary
    pdf.section_title('2. Performance Metrics Summary')
    if not summary_df.empty:
        headers = ['Metric', 'Count', 'Mean', 'Min', 'Max', 'P50', 'P95', 'P99']
        rows = []
        for _, row in summary_df.iterrows():
            rows.append([
                row['Metric'],
                f'{int(row["Count"]):,}',
                f'{row["Mean"]:.3f}',
                f'{row["Min"]:.3f}',
                f'{row["Max"]:.3f}',
                f'{row["P50"]:.3f}',
                f'{row["P95"]:.3f}',
                f'{row["P99"]:.3f}',
            ])
        col_widths = [20, 22, 22, 22, 22, 22, 22, 22]
        pdf.add_summary_table(headers, rows, col_widths)

    # 3. Charts
    if 'timeline' in figures:
        pdf.add_page()
        pdf.section_title('3. Performance Metrics Timeline')
        pdf.add_chart_image(figures['timeline'])

    if 'distributions' in figures:
        for i, fig in enumerate(figures['distributions']):
            if i % 2 == 0:
                pdf.add_page()
            pdf.section_title(f'4-{i+1}. Distribution')
            pdf.add_chart_image(fig)

    return pdf.get_pdf_bytes()


def generate_web_request_report(df_filtered, time_counts, summary_stats_df, figures):
    """Generate Web Access request count PDF report.

    Args:
        df_filtered: Filtered DataFrame
        time_counts: Time series count DataFrame
        summary_stats_df: Summary statistics DataFrame
        figures: Dict of plotly figures {name: fig}
    """
    pdf = ReportPDF(title='Web Access - Request Count Report')
    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. Overview
    pdf.section_title('1. Overview')
    pdf.add_key_value('Report Period',
                      f'{df_filtered["timestamp"].min().strftime("%Y-%m-%d %H:%M")} ~ '
                      f'{df_filtered["timestamp"].max().strftime("%Y-%m-%d %H:%M")}')
    pdf.add_key_value('Total Requests', f'{len(df_filtered):,}')
    pdf.ln(3)

    # 2. Summary
    pdf.section_title('2. Summary Statistics')
    headers = ['Metric', 'Value']
    rows = []
    for _, row in summary_stats_df.iterrows():
        val = row['Value']
        if isinstance(val, float):
            val = f'{val:.2f}'
        else:
            val = f'{int(val):,}' if val == int(val) else f'{val}'
        rows.append([row['Metric'], val])
    col_widths = [95, 95]
    pdf.add_summary_table(headers, rows, col_widths)

    # 3. Charts
    if 'timeline' in figures:
        pdf.add_page()
        pdf.section_title('3. Requests Over Time')
        pdf.add_chart_image(figures['timeline'])

    if 'method' in figures:
        pdf.add_page()
        pdf.section_title('4. HTTP Method Distribution')
        pdf.add_chart_image(figures['method'])

    if 'status' in figures:
        pdf.section_title('5. Status Code Distribution')
        pdf.add_chart_image(figures['status'])

    if 'pattern' in figures:
        pdf.add_page()
        pdf.section_title('6. Traffic Pattern by Hour')
        pdf.add_chart_image(figures['pattern'])

    return pdf.get_pdf_bytes()
