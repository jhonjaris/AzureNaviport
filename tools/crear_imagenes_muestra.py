#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creador de imágenes de muestra para representar las pantallas del sistema
"""

from PIL import Image, ImageDraw, ImageFont
import os

def crear_imagen_pantalla(titulo, subtitulo, elementos, nombre_archivo, width=1200, height=800):
    """Crea una imagen de muestra que representa una pantalla del sistema"""
    
    # Crear imagen con fondo
    img = Image.new('RGB', (width, height), color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    try:
        # Intentar usar una fuente del sistema
        font_title = ImageFont.truetype("arial.ttf", 32)
        font_subtitle = ImageFont.truetype("arial.ttf", 20)
        font_text = ImageFont.truetype("arial.ttf", 16)
    except:
        # Usar fuente por defecto si no se encuentra arial
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # Header del sistema
    draw.rectangle([0, 0, width, 80], fill='#2c3e50')
    draw.text((20, 25), "NaviPort RD - Sistema de Gestión de Accesos Portuarios", 
              fill='white', font=font_subtitle)
    
    # Título de la pantalla
    draw.text((50, 120), titulo, fill='#2c3e50', font=font_title)
    draw.text((50, 160), subtitulo, fill='#7f8c8d', font=font_text)
    
    # Dibujar elementos de la pantalla
    y_pos = 220
    for elemento in elementos:
        # Caja para cada elemento
        draw.rectangle([50, y_pos, width-50, y_pos+60], fill='white', outline='#e9ecef', width=2)
        draw.text((70, y_pos+10), elemento['titulo'], fill='#2c3e50', font=font_text)
        draw.text((70, y_pos+35), elemento['descripcion'], fill='#7f8c8d', font=font_text)
        y_pos += 80
    
    # Guardar imagen
    img.save(f'docs/capturas/{nombre_archivo}')
    print(f"Imagen creada: {nombre_archivo}")

def crear_todas_las_imagenes():
    """Crea todas las imágenes de muestra del sistema"""
    
    # 1. Login
    crear_imagen_pantalla(
        "Iniciar Sesión",
        "Ingrese sus credenciales para acceder al sistema",
        [
            {"titulo": "Campo Usuario", "descripcion": "Ingrese su nombre de usuario o cédula"},
            {"titulo": "Campo Contraseña", "descripcion": "Ingrese su contraseña"},
            {"titulo": "Checkbox 'Recordarme'", "descripcion": "Mantener sesión activa"},
            {"titulo": "Botón 'Iniciar Sesión'", "descripcion": "Acceder al sistema"},
            {"titulo": "Enlace 'Olvidaste tu contraseña'", "descripcion": "Recuperar contraseña"}
        ],
        "01_login.png"
    )
    
    # 2. Dashboard Solicitante
    crear_imagen_pantalla(
        "Dashboard Solicitante",
        "Panel principal para empresas solicitantes",
        [
            {"titulo": "Nueva Solicitud", "descripcion": "Crear solicitud de acceso portuario"},
            {"titulo": "Mis Solicitudes", "descripcion": "5 activas • 3 pendientes"},
            {"titulo": "Autorizaciones", "descripcion": "2 activas • 1 por vencer"},
            {"titulo": "Estadísticas", "descripcion": "Este mes: 8 solicitudes • 85% aprobación"},
            {"titulo": "Tabla de Solicitudes", "descripcion": "Solicitudes recientes con estado"}
        ],
        "02_dashboard_solicitante.png"
    )
    
    # 3. Nueva Solicitud
    crear_imagen_pantalla(
        "Nueva Solicitud de Acceso",
        "Complete todos los campos requeridos para procesar su solicitud",
        [
            {"titulo": "Información de la Solicitud", "descripcion": "Puerto, motivo, fechas y horarios"},
            {"titulo": "Información de Vehículos", "descripcion": "Agregar múltiples vehículos dinámicamente"},
            {"titulo": "Documentos Adjuntos", "descripcion": "Cédula, RNC, registro de vehículo"},
            {"titulo": "Botón 'Guardar Borrador'", "descripcion": "Guardar sin enviar"},
            {"titulo": "Botón 'Enviar Solicitud'", "descripcion": "Enviar para evaluación"}
        ],
        "03_nueva_solicitud.png"
    )
    
    # 4. Dashboard Evaluador
    crear_imagen_pantalla(
        "Panel de Evaluación",
        "Revisión y evaluación de solicitudes de acceso",
        [
            {"titulo": "Pendientes de Revisión", "descripcion": "12 solicitudes nuevas"},
            {"titulo": "Mis Asignadas", "descripcion": "8 en proceso"},
            {"titulo": "Prioridad Crítica", "descripcion": "3 solicitudes VIP"},
            {"titulo": "Rendimiento", "descripcion": "Este mes: 45 evaluadas • 78% aprobación"},
            {"titulo": "Tabla de Evaluación", "descripcion": "Solicitudes pendientes con prioridad"}
        ],
        "04_dashboard_evaluador.png"
    )
    
    # 5. Evaluar Solicitud
    crear_imagen_pantalla(
        "Evaluación de Solicitud",
        "Revisar detalles y tomar decisión sobre la solicitud",
        [
            {"titulo": "Información de la Empresa", "descripcion": "Datos, RNC, representante"},
            {"titulo": "Detalles del Acceso", "descripcion": "Puerto, motivo, fechas, vehículos"},
            {"titulo": "Documentos Adjuntos", "descripcion": "Visualizar documentos enviados"},
            {"titulo": "Panel de Evaluación", "descripcion": "Aprobar, Rechazar, Solicitar docs, Escalar"},
            {"titulo": "Campo de Comentarios", "descripcion": "Justificación obligatoria de la decisión"}
        ],
        "05_evaluar_solicitud.png"
    )
    
    # 6. Dashboard Control de Acceso
    crear_imagen_pantalla(
        "Control de Acceso Físico",
        "Scanner QR y verificación de autorizaciones",
        [
            {"titulo": "Scanner de Códigos QR", "descripcion": "Interfaz visual para escanear códigos"},
            {"titulo": "Autorización Verificada", "descripcion": "Información completa de la autorización"},
            {"titulo": "Estadísticas del Día", "descripcion": "Accesos procesados, denegados, discrepancias"},
            {"titulo": "Botón 'Autorizar Ingreso'", "descripcion": "Conceder acceso al puerto"},
            {"titulo": "Historial de Registros", "descripcion": "Últimos accesos registrados"}
        ],
        "06_dashboard_control_acceso.png"
    )
    
    # 7. Dashboard Supervisor
    crear_imagen_pantalla(
        "Panel de Supervisión",
        "Gestión de escalamientos y discrepancias del sistema",
        [
            {"titulo": "Escalamientos", "descripcion": "4 casos críticos pendientes"},
            {"titulo": "Discrepancias", "descripcion": "7 problemas reportados"},
            {"titulo": "Alertas del Sistema", "descripcion": "5 notificaciones activas"},
            {"titulo": "Estadísticas de Rendimiento", "descripcion": "Este mes: 156 procesadas • 82% aprobación"},
            {"titulo": "Acciones Rápidas", "descripcion": "Resolver críticos, rebalancear carga"}
        ],
        "07_dashboard_supervisor.png"
    )

if __name__ == "__main__":
    # Crear directorio si no existe
    if not os.path.exists('docs/capturas'):
        os.makedirs('docs/capturas')
    
    crear_todas_las_imagenes()
    print("Todas las imágenes de muestra han sido creadas exitosamente!")