"""
Report Generator Service

Renders HTML templates with Jinja2 and converts to PDF using WeasyPrint.
Supports custom templates stored in the templates directory.

Usage:
    from core.reports.generator import ReportGenerator
    generator = ReportGenerator()
    pdf_bytes = generator.generate_pdf(report_data, template='default_report')
"""
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template directory
TEMPLATES_DIR = Path(__file__).parent / 'templates'


class ReportGenerator:
    """
    Generates PDF reports from Jinja2 HTML templates.
    
    Templates are stored in the templates/ subdirectory.
    Users can add custom templates by placing HTML files there.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize generator with template directory.
        
        Args:
            templates_dir: Custom templates directory (default: ./templates)
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def list_templates(self) -> list[str]:
        """List available template names."""
        return [
            p.stem for p in self.templates_dir.glob('*.html')
        ]
    
    def render_html(self, data: dict, template: str = 'default_report') -> str:
        """
        Render template to HTML string.
        
        Args:
            data: Template context dictionary
            template: Template name (without .html extension)
            
        Returns:
            Rendered HTML string
        """
        tpl = self.env.get_template(f'{template}.html')
        return tpl.render(**data)
    
    def generate_pdf(
        self, 
        data: dict, 
        template: str = 'default_report',
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF from template.
        
        Args:
            data: Report data dictionary
            template: Template name
            output_path: Optional path to save PDF file
            
        Returns:
            PDF as bytes
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint"
            )
        
        html_content = self.render_html(data, template)
        
        # Generate PDF
        html = HTML(string=html_content, base_url=str(self.templates_dir))
        pdf_bytes = html.write_pdf()
        
        # Save if path provided
        if output_path:
            Path(output_path).write_bytes(pdf_bytes)
        
        return pdf_bytes
    
    def generate_html_file(
        self,
        data: dict,
        template: str = 'default_report',
        output_path: str = 'report.html'
    ) -> str:
        """
        Generate HTML file (for preview without WeasyPrint).
        
        Args:
            data: Report data dictionary
            template: Template name
            output_path: Path to save HTML file
            
        Returns:
            Path to generated file
        """
        html_content = self.render_html(data, template)
        Path(output_path).write_text(html_content, encoding='utf-8')
        return output_path


def generate_sample_report(output_path: str = 'sample_report.html') -> str:
    """
    Generate sample report using default data.
    
    Returns:
        Path to generated HTML file
    """
    from core.reports import create_sample_report
    
    report_data = create_sample_report()
    generator = ReportGenerator()
    
    return generator.generate_html_file(
        data=report_data.to_dict(),
        template='default_report',
        output_path=output_path
    )
