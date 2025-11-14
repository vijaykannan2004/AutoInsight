import pandas as pd
import numpy as np
import json
import io
import base64
from typing import Dict, List, Any, Optional, Union
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image as RLImage
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import tempfile
import os

class DataExporter:
    """Handle data and visualization export functionality"""

    def __init__(self):
        self.supported_formats = {
            "data": ["csv", "excel", "json", "parquet"],
            "charts": ["png", "svg", "html", "pdf"],
            "reports": ["pdf", "html"]
        }

    def export_data(self, df: pd.DataFrame, format: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Export dataset to various formats"""
        if format not in self.supported_formats["data"]:
            return {"error": f"Unsupported data format: {format}"}

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dataset_{timestamp}"

        try:
            if format == "csv":
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                content = buffer.getvalue()
                content_type = "text/csv"
                file_extension = ".csv"

            elif format == "excel":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Data', index=False)
                    # Add summary sheet
                    summary_data = self._generate_data_summary(df)
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                content = buffer.getvalue()
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_extension = ".xlsx"

            elif format == "json":
                content = df.to_json(orient='records', indent=2)
                content_type = "application/json"
                file_extension = ".json"

            elif format == "parquet":
                buffer = io.BytesIO()
                df.to_parquet(buffer, index=False)
                content = buffer.getvalue()
                content_type = "application/octet-stream"
                file_extension = ".parquet"

            # Encode for JSON response
            if isinstance(content, str):
                content_encoded = base64.b64encode(content.encode()).decode()
            else:
                content_encoded = base64.b64encode(content).decode()

            return {
                "success": True,
                "filename": f"{filename}{file_extension}",
                "content_type": content_type,
                "content": content_encoded,
                "size": len(content),
                "format": format,
                "rows": len(df),
                "columns": len(df.columns)
            }

        except Exception as e:
            return {"error": f"Failed to export data as {format}: {str(e)}"}

    def export_chart(self, chart_config: Dict[str, Any], format: str,
                    width: int = 1200, height: int = 600) -> Dict[str, Any]:
        """Export chart to various formats"""
        if format not in self.supported_formats["charts"]:
            return {"error": f"Unsupported chart format: {format}"}

        try:
            if format == "png":
                # For PNG, we'll need to generate from Plotly config
                # This is a placeholder - actual implementation would use Plotly's image export
                fig = go.Figure(json.loads(chart_config["config"]))
                img_bytes = pio.to_image(fig, format="png", width=width, height=height)
                content_encoded = base64.b64encode(img_bytes).decode()
                content_type = "image/png"
                file_extension = ".png"

            elif format == "svg":
                fig = go.Figure(json.loads(chart_config["config"]))
                img_bytes = pio.to_image(fig, format="svg", width=width, height=height)
                content_encoded = base64.b64encode(img_bytes).decode()
                content_type = "image/svg+xml"
                file_extension = ".svg"

            elif format == "html":
                # Create standalone HTML
                fig = go.Figure(json.loads(chart_config["config"]))
                html_content = pio.to_html(fig, include_plotlyjs=True, div_id=chart_config["id"])
                content_encoded = base64.b64encode(html_content.encode()).decode()
                content_type = "text/html"
                file_extension = ".html"

            elif format == "pdf":
                # For PDF, we'd need additional processing
                # This is a simplified version
                fig = go.Figure(json.loads(chart_config["config"]))
                img_bytes = pio.to_image(fig, format="png", width=width, height=height)
                content_encoded = base64.b64encode(img_bytes).decode()
                content_type = "application/pdf"  # Note: This would need PDF conversion
                file_extension = ".pdf"

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in chart_config["title"] if c.isalnum() or c in (' ', '-', '_')).rstrip()

            return {
                "success": True,
                "filename": f"{safe_title}_{timestamp}{file_extension}",
                "content_type": content_type,
                "content": content_encoded,
                "format": format,
                "chart_type": chart_config["type"],
                "title": chart_config["title"]
            }

        except Exception as e:
            return {"error": f"Failed to export chart as {format}: {str(e)}"}

    def generate_analysis_report(self, df: pd.DataFrame, analysis_results: Dict[str, Any],
                                charts: List[Dict[str, Any]], format: str = "pdf") -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        if format not in self.supported_formats["reports"]:
            return {"error": f"Unsupported report format: {format}"}

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format == "pdf":
                report_content = self._create_pdf_report(df, analysis_results, charts)
                content_type = "application/pdf"
                file_extension = ".pdf"

            elif format == "html":
                report_content = self._create_html_report(df, analysis_results, charts)
                content_type = "text/html"
                file_extension = ".html"

            # Encode content
            if isinstance(report_content, str):
                content_encoded = base64.b64encode(report_content.encode()).decode()
            else:
                content_encoded = base64.b64encode(report_content).decode()

            return {
                "success": True,
                "filename": f"analysis_report_{timestamp}{file_extension}",
                "content_type": content_type,
                "content": content_encoded,
                "format": format,
                "size": len(report_content),
                "includes_charts": len(charts)
            }

        except Exception as e:
            return {"error": f"Failed to generate {format} report: {str(e)}"}

    def _generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate data summary for Excel export"""
        summary = {
            "Metric": [
                "Total Rows",
                "Total Columns",
                "Numeric Columns",
                "Categorical Columns",
                "Missing Values",
                "Duplicate Rows",
                "Memory Usage (MB)"
            ],
            "Value": [
                len(df),
                len(df.columns),
                len(df.select_dtypes(include=[np.number]).columns),
                len(df.select_dtypes(include=['object', 'category']).columns),
                df.isnull().sum().sum(),
                df.duplicated().sum(),
                round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
            ]
        }
        return summary

    def _create_pdf_report(self, df: pd.DataFrame, analysis_results: Dict[str, Any],
                          charts: List[Dict[str, Any]]) -> bytes:
        """Create PDF analysis report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.darkblue
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )

        # Title
        story.append(Paragraph("AutoInsight Data Analysis Report", title_style))
        story.append(Spacer(1, 12))

        # Metadata
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(Paragraph(f"<b>Dataset:</b> {analysis_results.get('filename', 'Unknown')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))

        summary_text = self._generate_executive_summary(df, analysis_results)
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))

        # Data Overview
        story.append(Paragraph("Data Overview", heading_style))

        # Create summary table
        summary_data = self._generate_data_summary(df)
        summary_table = Table([list(summary_data.keys()), list(summary_data.values())])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Key Findings
        story.append(Paragraph("Key Findings", heading_style))

        if "ai_insights" in analysis_results:
            insights = analysis_results["ai_insights"]
            if isinstance(insights, str):
                story.append(Paragraph(insights, styles['Normal']))
            elif isinstance(insights, dict) and "key_findings" in insights:
                for finding in insights["key_findings"]:
                    story.append(Paragraph(f"• {finding}", styles['Normal']))

        story.append(Spacer(1, 20))

        # Correlations
        if "cleaning_report" in analysis_results and "highly_correlated_pairs" in analysis_results["cleaning_report"]:
            story.append(Paragraph("Key Correlations", heading_style))
            correlations = analysis_results["cleaning_report"]["highly_correlated_pairs"]
            if correlations:
                for corr in correlations[:5]:  # Top 5 correlations
                    story.append(Paragraph(f"• {corr[0]} & {corr[1]}: {corr[2]:.3f}", styles['Normal']))
            else:
                story.append(Paragraph("No strong correlations found.", styles['Normal']))
            story.append(Spacer(1, 20))

        # Recommendations
        story.append(Paragraph("Recommendations", heading_style))

        recommendations = self._generate_recommendations(df, analysis_results)
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _create_html_report(self, df: pd.DataFrame, analysis_results: Dict[str, Any],
                           charts: List[Dict[str, Any]]) -> str:
        """Create HTML analysis report"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoInsight Analysis Report</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 3px solid #2563eb; padding-bottom: 20px; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
        .summary-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .summary-table th, .summary-table td { border: 1px solid #e5e7eb; padding: 10px; text-align: left; }
        .summary-table th { background-color: #f3f4f6; font-weight: bold; }
        .insights { background-color: #f8fafc; padding: 20px; border-left: 4px solid #2563eb; margin: 20px 0; }
        .correlation-item { background-color: #fef3c7; padding: 10px; margin: 5px 0; border-radius: 5px; }
        .recommendation { background-color: #ecfdf5; padding: 10px; margin: 5px 0; border-radius: 5px; }
        .footer { margin-top: 50px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 AutoInsight Analysis Report</h1>
        <p>Generated on {timestamp}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="insights">
            {executive_summary}
        </div>
    </div>

    <div class="section">
        <h2>Data Overview</h2>
        <table class="summary-table">
            {summary_table}
        </table>
    </div>

    <div class="section">
        <h2>Key Findings</h2>
        <div class="insights">
            {key_findings}
        </div>
    </div>

    <div class="section">
        <h2>Correlations</h2>
        {correlations}
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        {recommendations}
    </div>

    <div class="footer">
        <p>Report generated by AutoInsight - AI-Powered Data Analytics Platform</p>
    </div>
</body>
</html>
        """

        # Generate content
        summary_data = self._generate_data_summary(df)
        summary_rows = ""
        for i, (metric, value) in enumerate(zip(summary_data["Metric"], summary_data["Value"])):
            bg_color = "#f3f4f6" if i % 2 == 0 else "white"
            summary_rows += f"<tr style='background-color: {bg_color}'><td><strong>{metric}</strong></td><td>{value}</td></tr>"

        correlations_html = ""
        if "cleaning_report" in analysis_results and "highly_correlated_pairs" in analysis_results["cleaning_report"]:
            corr_pairs = analysis_results["cleaning_report"]["highly_correlated_pairs"]
            if corr_pairs:
                correlations_html = "".join([f"<div class='correlation-item'>{corr[0]} & {corr[1]}: {corr[2]:.3f}</div>" for corr in corr_pairs[:5]])
            else:
                correlations_html = "<p>No strong correlations found.</p>"

        recommendations = self._generate_recommendations(df, analysis_results)
        recommendations_html = "".join([f"<div class='recommendation'>{rec}</div>" for rec in recommendations])

        # Fill template
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            executive_summary=self._generate_executive_summary(df, analysis_results),
            summary_table=summary_rows,
            key_findings=str(analysis_results.get("ai_insights", "No insights available.")),
            correlations=correlations_html,
            recommendations=recommendations_html
        )

        return html_content

    def _generate_executive_summary(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> str:
        """Generate executive summary text"""
        rows, cols = df.shape
        missing = df.isnull().sum().sum()
        duplicates = df.duplicated().sum()

        summary = f"""
        The dataset contains <strong>{rows:,}</strong> rows and <strong>{cols}</strong> columns.
        Data quality analysis revealed <strong>{missing:,}</strong> missing values
        ({missing/(rows*cols)*100:.1f}% of all cells) and <strong>{duplicates:,}</strong> duplicate rows.
        """

        if "cleaning_report" in analysis_results:
            corr_pairs = analysis_results["cleaning_report"].get("highly_correlated_pairs", [])
            if corr_pairs:
                summary += f" <strong>{len(corr_pairs)}</strong> strong correlations were identified between variables."
            else:
                summary += " No strong correlations were found between variables."

        summary += " The analysis includes AI-generated insights and statistical summaries to support data-driven decision making."

        return summary.strip()

    def _generate_recommendations(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate data analysis recommendations"""
        recommendations = []

        # Data quality recommendations
        if df.isnull().any().any():
            missing_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
            if missing_pct > 10:
                recommendations.append(f"Address missing data ({missing_pct:.1f}% of cells missing) through imputation or data collection")

        if df.duplicated().sum() > 0:
            recommendations.append("Remove duplicate rows to improve data quality")

        # Analysis recommendations
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            recommendations.append("Consider regression analysis to explore relationships between numeric variables")

        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            recommendations.append("Perform group-based analysis to identify patterns across categories")

        # Business recommendations
        recommendations.append("Create a data quality monitoring process for ongoing data collection")
        recommendations.append("Consider automating this analysis pipeline for regular data updates")

        return recommendations

    def create_shareable_link(self, data_id: str, expires_in_hours: int = 24) -> Dict[str, Any]:
        """Create shareable link for analysis (placeholder implementation)"""
        import secrets
        import hashlib

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Create link (in production, this would be stored in database)
        share_link = f"https://autoinsight.ai/shared/{token}"

        # Calculate expiry
        expiry_time = datetime.now().timestamp() + (expires_in_hours * 3600)

        return {
            "success": True,
            "share_link": share_link,
            "token": token,
            "expires_in_hours": expires_in_hours,
            "expires_at": expiry_time,
            "data_id": data_id
        }

if __name__ == "__main__":
    # Test export functionality
    from data_cleaner import DataCleaner
    from visualization import ChartGenerator

    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        "age": np.random.randint(18, 65, 100),
        "salary": np.random.normal(75000, 25000, 100),
        "department": np.random.choice(["IT", "HR", "Finance"], 100),
        "experience": np.random.exponential(5, 100)
    })

    # Add correlations
    df["salary"] = df["salary"] + df["age"] * 1000 + df["experience"] * 5000

    exporter = DataExporter()

    # Test data export
    print("Testing data export...")
    result = exporter.export_data(df, "csv")
    print(f"CSV Export: {result.get('success', False)}")

    # Test chart export (would need actual chart config)
    # chart_config = {"id": "test", "type": "scatter", "title": "Test Chart", "config": "{}"}
    # chart_result = exporter.export_chart(chart_config, "png")
    # print(f"Chart Export: {chart_result.get('success', False)}")

    # Test report generation
    print("Testing report generation...")
    analysis_results = {
        "filename": "test_data.csv",
        "ai_insights": "Sample AI insights for testing purposes.",
        "cleaning_report": {"highly_correlated_pairs": [["age", "salary", 0.85]]}
    }

    report_result = exporter.generate_analysis_report(df, analysis_results, [], "html")
    print(f"HTML Report: {report_result.get('success', False)}")

    print("Export functionality tests completed!")