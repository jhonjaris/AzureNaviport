"""
Script para crear un archivo HTML simple a partir del manual del evaluador.
"""
import os
import webbrowser

def crear_html():
    # Rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(base_dir, 'docs', 'MANUAL_EVALUADOR.md')
    html_path = os.path.join(base_dir, 'docs', 'MANUAL_EVALUADOR.html')
    
    # Leer el archivo Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Crear HTML básico
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Manual del Evaluador - NaviPort RD</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 20px;
        }}
        h1, h2, h3 {{ 
            color: #2c3e50; 
        }}
        pre {{ 
            background: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px; 
        }}
        code {{ 
            background: #f5f5f5; 
            padding: 2px 5px; 
        }}
        img {{ 
            max-width: 100%; 
            height: auto; 
        }}
        .no-print {{ 
            text-align: center; 
            margin: 20px 0; 
        }}
        @media print {{
            .no-print {{ 
                display: none; 
            }}
            body {{ 
                font-size: 12pt; 
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <h1>Manual del Evaluador - NaviPort RD</h1>
        <p>Para guardar como PDF, presiona Ctrl+P y selecciona "Guardar como PDF"</p>
        <button onclick="window.print()" style="
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        ">
            Guardar como PDF
        </button>
        <hr>
    </div>
    <div id="contenido">
        {contenido}
    </div>
</body>
</html>""".format(contenido=contenido)
    
    # Guardar el archivo HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Abrir en el navegador
    webbrowser.open(f'file://{html_path}')
    print(f"Archivo HTML generado: {html_path}")
    print("Instrucciones para guardar como PDF:")
    print("1. Presiona Ctrl+P")
    print("2. En el menú de impresión, selecciona 'Guardar como PDF'")
    print("3. Haz clic en 'Guardar'")

if __name__ == "__main__":
    crear_html()
