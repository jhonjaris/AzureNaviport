"""
Script simple para convertir el manual del evaluador a PDF.
"""
import os
from markdown2 import markdown
from weasyprint import HTML

def convert_md_to_pdf():
    # Rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(base_dir, 'docs', 'MANUAL_EVALUADOR.md')
    pdf_path = os.path.join(base_dir, 'docs', 'MANUAL_EVALUADOR.pdf')
    
    # Leer el archivo Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir a HTML
    html_content = markdown(md_content)
    
    # Añadir estilos básicos
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            code {{ background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
            pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            img {{ max-width: 100%; height: auto; display: block; margin: 10px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """.format(content=html_content)
    
    # Generar PDF
    HTML(string=html, base_url=base_dir).write_pdf(pdf_path)
    print(f"PDF generado exitosamente en: {pdf_path}")

if __name__ == "__main__":
    convert_md_to_pdf()
