"""
Script para convertir el manual del evaluador de Markdown a PDF.
"""
import os
import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent
MANUAL_MD = os.path.join(BASE_DIR, 'docs', 'MANUAL_EVALUADOR.md')
MANUAL_PDF = os.path.join(BASE_DIR, 'docs', 'MANUAL_EVALUADOR.pdf')
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'docs', 'capturas_manual')

# Estilo CSS para el PDF
STYLES = """
@page {
    size: A4;
    margin: 2cm;
    @top-right {
        content: "Manual del Evaluador - NaviPort RD";
        font-size: 10pt;
        color: #666;
    }
    @bottom-right {
        content: "Página " counter(page) " de " counter(pages);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
}

h1 {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
    page-break-after: avoid;
}

h2 {
    color: #2980b9;
    margin-top: 1.5em;
    page-break-after: avoid;
}

h3 {
    color: #3498db;
    margin-top: 1.2em;
    page-break-after: avoid;
}

h4 {
    color: #555;
    margin-top: 1em;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 20px auto;
    border: 1px solid #ddd;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

pre {
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    overflow-x: auto;
}

code {
    font-family: 'Courier New', monospace;
    background-color: #f5f5f5;
    padding: 2px 5px;
    border-radius: 3px;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #f2f2f2;
}

ul, ol {
    padding-left: 20px;
}

.cover-page {
    text-align: center;
    margin: 100px 0;
}

.cover-page h1 {
    font-size: 28pt;
    border: none;
    margin-bottom: 20px;
}

.cover-page p {
    color: #666;
    font-size: 14pt;
}
"""

def add_screenshots_to_markdown(md_content):
    """Agrega referencias a las capturas de pantalla en el markdown."""
    screenshots = [
        ("01_dashboard.png", "Figura 1: Panel de Control del Evaluador"),
        ("02_lista_empresas.png", "Figura 2: Lista de Empresas"),
        ("03_nueva_empresa.png", "Figura 3: Formulario de Nueva Empresa"),
        ("04_tipos_licencia.png", "Figura 4: Gestión de Tipos de Licencia"),
        ("05_servicios.png", "Figura 5: Gestión de Servicios"),
        ("06_configuracion.png", "Figura 6: Configuración del Sistema")
    ]
    
    # Agregar sección de capturas de pantalla al final del documento
    md_content += "\n\n# Capturas de Pantalla\n\n"
    
    for img_file, caption in screenshots:
        img_path = os.path.join(SCREENSHOTS_DIR, img_file)
        if os.path.exists(img_path):
            md_content += f"## {caption}\n\n"
            md_content += f"![{caption}]({img_path})\n\n"
    
    return md_content

def convert_md_to_pdf():
    """Convierte el archivo Markdown a PDF."""
    print(f"Convirtiendo {MANUAL_MD} a PDF...")
    
    # Leer el contenido del archivo Markdown
    with open(MANUAL_MD, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Agregar capturas de pantalla al contenido
    md_content = add_screenshots_to_markdown(md_content)
    
    # Convertir Markdown a HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'extra',
            'tables',
            'toc',
            'sane_lists',
            'nl2br',
            'md_in_html'
        ],
        output_format='html5'
    )
    
    # Crear el HTML completo
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Manual del Evaluador - NaviPort RD</title>
        <style>{styles}</style>
    </head>
    <body>
        <div class="cover-page">
            <h1>Manual del Evaluador</h1>
            <p>Sistema de Gestión Portuaria</p>
            <p>NaviPort RD</p>
            <p>Agosto 2024</p>
        </div>
        {content}
    </body>
    </html>
    """.format(
        styles=STYLES,
        content=html_content
    )
    
    # Generar PDF
    HTML(string=html, base_url=str(BASE_DIR)).write_pdf(
        MANUAL_PDF,
        stylesheets=[
            CSS(string=STYLES)
        ]
    )
    
    print(f"PDF generado exitosamente en: {MANUAL_PDF}")

if __name__ == "__main__":
    convert_md_to_pdf()
