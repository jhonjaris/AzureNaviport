#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de PDF con imágenes en alta resolución para el Manual de Pantallas NaviPort RD
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from PIL import Image as PILImage
import os

def crear_pdf_alta_resolucion():
    """Genera el PDF del manual de pantallas con imágenes en alta resolución"""
    
    # Configuración del documento con márgenes optimizados para imágenes grandes
    doc = SimpleDocTemplate(
        "docs/PANTALLAS_SISTEMA_NAVIPORT.pdf",
        pagesize=A4,
        rightMargin=36,  # Márgenes más pequeños para más espacio
        leftMargin=36,
        topMargin=50,
        bottomMargin=36
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para títulos
    titulo_style = ParagraphStyle(
        'TituloPersonalizado',
        parent=styles['Title'],
        fontSize=24,
        textColor=HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    subtitulo_style = ParagraphStyle(
        'SubtituloPersonalizado',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    # Estilo para secciones
    seccion_style = ParagraphStyle(
        'SeccionPersonalizada',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'NormalPersonalizado',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#333333'),
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Contenido del documento
    story = []
    
    # Portada
    story.append(Paragraph("NaviPort RD", titulo_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Manual de Pantallas del Sistema", subtitulo_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("Sistema de Gestión de Accesos Portuarios", normal_style))
    story.append(Paragraph("Autoridad Portuaria Dominicana", normal_style))
    story.append(Paragraph("Versión 1.0 - Enero 2025", normal_style))
    story.append(PageBreak())
    
    # Contenido principal con imágenes en alta resolución
    pantallas = [
        {
            "titulo": "1. PANTALLA DE LOGIN",
            "imagen": "docs/capturas/01_login.png",
            "descripcion": "Pantalla inicial de acceso al sistema donde los usuarios ingresan sus credenciales.",
            "funcionalidades": [
                "Autenticación de usuarios con campo de usuario y contraseña",
                "Checkbox 'Recordarme' para mantener la sesión activa", 
                "Validación de formato para cédula/RNC dominicano",
                "Seguridad con bloqueo automático después de 5 intentos fallidos (30 minutos)",
                "Enlace para recuperación de contraseña",
                "Redirección automática al dashboard según el rol del usuario"
            ],
            "usuarios": "Todos los usuarios del sistema (solicitantes, evaluadores, supervisores, oficiales de acceso, admin TIC, dirección)"
        },
        {
            "titulo": "2. DASHBOARD SOLICITANTE",
            "imagen": "docs/capturas/02_dashboard_solicitante.png",
            "descripcion": "Panel principal para representantes de empresas que solicitan acceso portuario.",
            "funcionalidades": [
                "Botón para crear nueva solicitud de acceso",
                "Lista de solicitudes activas y su estado actual",
                "Estadísticas personales: número de solicitudes del mes y porcentaje de aprobación",
                "Gestión de autorizaciones: ver autorizaciones activas y por vencer",
                "Sistema de notificaciones para alertas de documentos faltantes",
                "Navegación a: Nueva Solicitud, Mis Solicitudes, Autorizaciones, Historial"
            ],
            "usuarios": "Representantes de empresas (solicitantes) y empresas de logística y transporte"
        },
        {
            "titulo": "3. NUEVA SOLICITUD (SOLICITANTE)",
            "imagen": "docs/capturas/03_nueva_solicitud.png",
            "descripcion": "Formulario completo para crear una nueva solicitud de acceso portuario.",
            "funcionalidades": [
                "Información de la Solicitud: puerto de destino, motivo de acceso, fechas y horarios, descripción detallada",
                "Gestión dinámica de vehículos: agregar/eliminar múltiples vehículos con datos completos",
                "Documentos adjuntos: cédula del representante (requerido), RNC de la empresa (requerido), registro de vehículo (opcional)",
                "Validación de archivos con límite de 5MB por archivo",
                "Opciones: Guardar borrador o Enviar solicitud para evaluación"
            ],
            "usuarios": "Representantes de empresas solicitantes"
        },
        {
            "titulo": "4. DASHBOARD EVALUADOR",
            "imagen": "docs/capturas/04_dashboard_evaluador.png",
            "descripcion": "Panel principal para evaluadores portuarios que revisan las solicitudes.",
            "funcionalidades": [
                "Lista de solicitudes pendientes de evaluación",
                "Solicitudes asignadas específicamente al evaluador",
                "Solicitudes críticas: casos VIP o de alta prioridad",
                "Estadísticas de rendimiento: número de evaluaciones y porcentaje de aprobación",
                "Sistema de alertas para solicitudes que vencen hoy",
                "Navegación: Dashboard, Evaluaciones, Reportes, Configuración"
            ],
            "usuarios": "Evaluadores portuarios y personal de control y validación"
        },
        {
            "titulo": "5. EVALUAR SOLICITUD (EVALUADOR)",
            "imagen": "docs/capturas/05_evaluar_solicitud.png",
            "descripcion": "Pantalla detallada para la evaluación individual de cada solicitud.",
            "funcionalidades": [
                "Información completa de la empresa: datos, RNC, historial de solicitudes",
                "Detalles del acceso: puerto, motivo, fechas, horarios, descripción",
                "Visualización de documentos adjuntos con apertura en nueva ventana",
                "Panel de evaluación con acciones: Aprobar, Rechazar, Solicitar documentos, Escalar",
                "Campo obligatorio de comentarios para justificar la decisión",
                "Indicadores de estado, prioridad y tiempos de vencimiento"
            ],
            "usuarios": "Evaluadores portuarios"
        },
        {
            "titulo": "6. DASHBOARD CONTROL DE ACCESO",
            "imagen": "docs/capturas/06_dashboard_control_acceso.png",
            "descripcion": "Panel principal para oficiales que controlan el acceso físico en los puertos.",
            "funcionalidades": [
                "Scanner de códigos QR: interfaz visual, activación de cámara, búsqueda manual",
                "Verificación de autorizaciones: estado (activa, vencida, revocada), información completa",
                "Acciones de acceso: autorizar ingreso o denegar acceso con registro automático",
                "Estadísticas del día: autorizaciones activas, accesos procesados, denegados, discrepancias",
                "Historial de registros recientes con tipo de acceso y estado"
            ],
            "usuarios": "Oficiales de control de acceso y personal de seguridad portuaria"
        },
        {
            "titulo": "7. DASHBOARD SUPERVISOR",
            "imagen": "docs/capturas/07_dashboard_supervisor.png",
            "descripcion": "Panel principal para supervisores que manejan escalamientos y discrepancias.",
            "funcionalidades": [
                "Gestión de escalamientos: casos críticos, priorización, resolución, reasignación",
                "Gestión de discrepancias: problemas de acceso, investigación, resolución",
                "Sistema de alertas automáticas con métricas críticas y análisis de tendencias",
                "Estadísticas y reportes: rendimiento global, tasas de aprobación, tiempos de procesamiento",
                "Panel de acciones rápidas para resolución inmediata"
            ],
            "usuarios": "Supervisores de control de calidad y personal de supervisión general"
        }
    ]
    
    # Agregar cada pantalla con su imagen en alta resolución
    for i, pantalla in enumerate(pantallas):
        story.append(Paragraph(pantalla["titulo"], subtitulo_style))
        story.append(Spacer(1, 10))
        
        # Agregar imagen si existe, con máximo tamaño posible
        if os.path.exists(pantalla["imagen"]):
            try:
                # Obtener dimensiones originales de la imagen
                with PILImage.open(pantalla["imagen"]) as pil_img:
                    original_width, original_height = pil_img.size
                
                # Calcular el ancho máximo disponible (página completa menos márgenes)
                page_width = A4[0] - 72  # A4 width minus margins
                max_width = page_width * 0.95  # 95% del ancho disponible
                
                # Calcular altura proporcional
                aspect_ratio = original_height / original_width
                img_width = max_width
                img_height = max_width * aspect_ratio
                
                # Si la imagen es muy alta, limitarla
                max_height = 6 * inch
                if img_height > max_height:
                    img_height = max_height
                    img_width = max_height / aspect_ratio
                
                # Crear elemento de imagen con máxima resolución
                img = Image(pantalla["imagen"], width=img_width, height=img_height)
                
                # Usar KeepTogether para evitar que la imagen se corte
                story.append(KeepTogether([img]))
                story.append(Spacer(1, 10))
                
            except Exception as e:
                print(f"Error al procesar imagen {pantalla['imagen']}: {e}")
                story.append(Paragraph("(Imagen no disponible)", normal_style))
                story.append(Spacer(1, 10))
        
        story.append(Paragraph("<b>Descripción:</b>", seccion_style))
        story.append(Paragraph(pantalla["descripcion"], normal_style))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("<b>Funcionalidades:</b>", seccion_style))
        for func in pantalla["funcionalidades"]:
            story.append(Paragraph(f"• {func}", normal_style))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("<b>Usuarios que la utilizan:</b>", seccion_style))
        story.append(Paragraph(pantalla["usuarios"], normal_style))
        story.append(Spacer(1, 20))
        
        # Salto de página después de cada pantalla (excepto la última)
        if i < len(pantallas) - 1:
            story.append(PageBreak())
    
    # Flujo de navegación
    story.append(PageBreak())
    story.append(Paragraph("FLUJO DE NAVEGACIÓN DEL SISTEMA", subtitulo_style))
    
    story.append(Paragraph("<b>Proceso Principal:</b>", seccion_style))
    flujo_pasos = [
        "1. Login → Redirección automática según rol de usuario",
        "2. Solicitante: Dashboard → Nueva Solicitud → Envío para evaluación",
        "3. Evaluador: Dashboard → Evaluar Solicitud → Decisión (Aprobar/Rechazar/Escalar)",
        "4. Sistema: Generación automática de autorización con código QR",
        "5. Control de Acceso: Scanner QR → Verificación → Autorización de ingreso",
        "6. Supervisor: Monitoreo de escalamientos y resolución de discrepancias"
    ]
    for paso in flujo_pasos:
        story.append(Paragraph(paso, normal_style))
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Estados de Solicitud:</b>", seccion_style))
    estados = [
        "Borrador: Guardada pero no enviada",
        "Pendiente: Enviada, esperando evaluación",
        "En Revisión: Asignada a evaluador específico",
        "Aprobada: Genera autorización automáticamente",
        "Rechazada: Finalizada negativamente",
        "Documentos Solicitados: Requiere información adicional",
        "Escalada: Enviada a supervisor para resolución"
    ]
    for estado in estados:
        story.append(Paragraph(f"• {estado}", normal_style))
    
    # Construir el PDF
    doc.build(story)
    print("PDF con imágenes en ALTA RESOLUCION generado exitosamente: docs/PANTALLAS_SISTEMA_NAVIPORT.pdf")

if __name__ == "__main__":
    crear_pdf_alta_resolucion()