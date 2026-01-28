#!/usr/bin/env python
import os
import re

def add_logout_to_template(file_path):
    """Agrega el dropdown de logout a un template"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el patrón navbar-user sin dropdown
    old_pattern = r'(<div class="navbar-user">\s*<span>.*?</span>\s*<div class="user-avatar">.*?</div>\s*</div>)'
    
    # Verificar si ya tiene dropdown
    if 'user-dropdown' in content:
        print(f"OK {file_path} ya tiene logout")
        return False
    
    # Buscar el patrón y reemplazar
    def replacement(match):
        original = match.group(1)
        # Extraer el contenido antes del cierre del div
        parts = original.rsplit('</div>', 1)
        if len(parts) == 2:
            before_close = parts[0]
            return (before_close + 
                   '\n        <div class="user-dropdown">' +
                   '\n            <a href="{% url \'accounts:logout\' %}" class="logout-link">🚪 Cerrar Sesión</a>' +
                   '\n        </div>' +
                   '\n    </div>')
        return original
    
    new_content = re.sub(old_pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"OK Logout agregado a {file_path}")
        return True
    else:
        print(f"WARN No se pudo procesar {file_path}")
        return False

def main():
    # Lista de archivos que tienen navbar-user
    template_files = [
        'templates/control_acceso/verificar_qr.html',
        'templates/evaluacion/evaluar_solicitud.html', 
        'templates/solicitudes/borrar_solicitud.html',
        'templates/solicitudes/detalle_solicitud.html',
        'templates/solicitudes/editar_solicitud.html',
        'templates/solicitudes/nueva_solicitud.html',
        'templates/supervisor/detalle_discrepancia.html',
        'templates/supervisor/detalle_escalamiento.html'
    ]
    
    print("=== AGREGANDO LOGOUT A TEMPLATES ===")
    
    updated_count = 0
    for template_file in template_files:
        if os.path.exists(template_file):
            if add_logout_to_template(template_file):
                updated_count += 1
        else:
            print(f"ERROR No existe: {template_file}")
    
    print(f"\nOK Proceso completado. {updated_count} archivos actualizados.")

if __name__ == '__main__':
    main()