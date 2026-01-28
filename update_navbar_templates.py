#!/usr/bin/env python
"""
Script para actualizar todos los templates que tienen navbar-user
para mostrar el rol del usuario debajo del nombre
"""
import os
import re
from pathlib import Path

def update_navbar_user_in_file(file_path):
    """Actualiza la sección navbar-user en un archivo específico"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patrón 1: navbar-user con span simple
        pattern1 = r'(<div class="navbar-user">\s*)<span>{{ user\.get_display_name }}</span>(\s*<div class="user-avatar"[^>]*>)'
        replacement1 = r'\1<div style="text-align: right; margin-right: 10px;">\n            <div style="font-weight: 500;">{{ user.get_display_name }}</div>\n            <div style="font-size: 12px; color: #7f8c8d;">{{ user.get_role_display }}</div>\n        </div>\2'
        
        # Patrón 2: navbar-user con span y información adicional (Puerto, etc)
        pattern2 = r'(<div class="navbar-user">\s*)<span>{{ user\.get_display_name }}[^<]*</span>(\s*<div class="user-avatar"[^>]*>)'
        replacement2 = r'\1<div style="text-align: right; margin-right: 10px;">\n            <div style="font-weight: 500;">{{ user.get_display_name }}</div>\n            <div style="font-size: 12px; color: #7f8c8d;">{{ user.get_role_display }}</div>\n        </div>\2'
        
        # Aplicar el primer patrón
        new_content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE | re.DOTALL)
        
        # Si no hubo cambios, probar el segundo patrón
        if new_content == content:
            new_content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE | re.DOTALL)
        
        # Solo escribir si hubo cambios
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error procesando {file_path}: {e}")
        return False

def main():
    """Función principal"""
    templates_dir = Path("templates")
    updated_files = []
    skipped_files = []
    
    # Buscar todos los archivos HTML en templates
    for html_file in templates_dir.rglob("*.html"):
        if html_file.name.endswith('.html'):
            try:
                # Leer el archivo para verificar si tiene navbar-user
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'navbar-user' in content and 'user.get_display_name' in content:
                    # Verificar si ya está actualizado
                    if 'user.get_role_display' in content:
                        skipped_files.append(str(html_file))
                        continue
                    
                    # Intentar actualizar
                    if update_navbar_user_in_file(html_file):
                        updated_files.append(str(html_file))
                        print(f"✓ Actualizado: {html_file}")
                    else:
                        print(f"✗ No se pudo actualizar: {html_file}")
                        
            except Exception as e:
                print(f"Error leyendo {html_file}: {e}")
    
    print(f"\n=== RESUMEN ===")
    print(f"Archivos actualizados: {len(updated_files)}")
    print(f"Archivos ya actualizados: {len(skipped_files)}")
    
    if updated_files:
        print(f"\nArchivos modificados:")
        for file in updated_files:
            print(f"  - {file}")

if __name__ == "__main__":
    main()