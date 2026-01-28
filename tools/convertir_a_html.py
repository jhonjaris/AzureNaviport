"""
Script para convertir el manual del evaluador de Markdown a HTML.
"""
import os
import webbrowser
from markdown2 import markdown

def convert_md_to_html():
    # Rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(base_dir, 'docs', 'MANUAL_EVALUADOR.md')
    html_path = os.path.join(base_dir, 'docs', 'MANUAL_EVALUADOR.html')
    
    # Leer el archivo Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir a HTML
    html_content = markdown(md_content)
    
    # Plantilla HTML con estilos
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Manual del Evaluador - NaviPort RD</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                max-width: 1000px;
                margin: 0 auto;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #2c3e50;
                margin-top: 1.5em;
            }
            h1 {
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                text-align: center;
            }
            h2 {
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
            code {
                background: #f5f5f5;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                border-left: 4px solid #3498db;
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
                border: 1px solid #ddd;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #3498db;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
            .note {
                background-color: #e7f4ff;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 4px 4px 0;
            }
            .warning {
                background-color: #fff8e6;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 4px 4px 0;
            }
            .success {
                background-color: #e8f5e9;
                border-left: 4px solid #4caf50;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 4px 4px 0;
            }
            @media print {
                body {
                    padding: 0;
                    font-size: 12pt;
                }
                .no-print {
                    display: none;
                }
                @page {
                    margin: 2cm;
                }
            }
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center; margin: 20px 0;">
            <h1>Manual del Evaluador - NaviPort RD</h1>
            <p>Para guardar como PDF, usa la opción de impresión de tu navegador (Ctrl+P) y selecciona "Guardar como PDF"</p>
            <button onclick="window.print()" style="
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 10px 2px;
                cursor: pointer;
                border-radius: 4px;">
                Guardar como PDF
            </button>
            <hr>
        </div>
        {content}
        <div class="no-print" style="text-align: center; margin: 40px 0 20px; color: #777; font-size: 0.9em;">
            <p>Documento generado automáticamente por NaviPort RD</p>
        </div>
    </body>
    </html>
    """.format(content=html_content)
    
    # Guardar el archivo HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Abrir en el navegador
    webbrowser.open(f'file://{html_path}')
    print(f"HTML generado exitosamente en: {html_path}")
    print("Por favor, usa la opción de impresión de tu navegador (Ctrl+P) para guardar como PDF.")
    print("Selecciona 'Guardar como PDF' en el menú de destino de impresión.")

if __name__ == "__main__":
    convert_md_to_html()
