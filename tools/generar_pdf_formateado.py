#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de PDF con formato mejorado y distribución óptima de contenido
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, KeepTogether, NextPageTemplate, PageTemplate, Frame
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from PIL import Image as PILImage
import os

def crear_pdf_bien_formateado():
    """Genera el PDF del manual con formato mejorado y distribución óptima"""
    
    # Configuración del documento
    doc = SimpleDocTemplate(
        "docs/PANTALLAS_SISTEMA_NAVIPORT.pdf",
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )
    
    # Estilos mejorados
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    titulo_principal_style = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Title'],
        fontSize=28,
        textColor=HexColor('#2c3e50'),
        spaceAfter=24,
        spaceBefore=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulo principal
    subtitulo_principal_style = ParagraphStyle(
        'SubtituloPrincipal',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=HexColor('#3498db'),
        spaceAfter=16,
        spaceBefore=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para títulos de sección (pantallas)
    titulo_seccion_style = ParagraphStyle(
        'TituloSeccion',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=24,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        keepWithNext=True  # Mantiene el título con el contenido siguiente
    )
    
    # Estilo para subsecciones
    subseccion_style = ParagraphStyle(
        'Subseccion',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=HexColor('#34495e'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        keepWithNext=True
    )
    
    # Estilo para texto normal optimizado
    normal_style = ParagraphStyle(
        'NormalOptimizado',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#333333'),
        spaceAfter=4,
        spaceBefore=2,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leading=12
    )
    
    # Estilo para listas
    lista_style = ParagraphStyle(
        'Lista',
        parent=normal_style,
        leftIndent=20,
        spaceAfter=3,
        fontSize=10
    )
    
    # Estilo para información general
    info_style = ParagraphStyle(
        'Informacion',
        parent=normal_style,
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    # Contenido del documento
    story = []
    
    # === PORTADA ===
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("NaviPort RD", titulo_principal_style))
    story.append(Paragraph("Manual de Pantallas del Sistema", subtitulo_principal_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Sistema de Gestión de Accesos Portuarios", info_style))
    story.append(Paragraph("Autoridad Portuaria Dominicana", info_style))
    story.append(Paragraph("Versión 1.0 - Enero 2025", info_style))
    story.append(PageBreak())
    
    # === CONTENIDO PRINCIPAL ===
    pantallas = [
        {
            "titulo": "1. PANTALLA DE LOGIN",
            "imagen": "docs/capturas/01_login.png",
            "descripcion": "Pantalla inicial de acceso al sistema donde los usuarios ingresan sus credenciales.",
            "funcionalidades": [
                "Autenticación de usuarios con campo de usuario y contraseña",
                "Checkbox 'Recordarme' para mantener la sesión activa", 
                "Validación de formato para cédula/RNC dominicano",
                "Seguridad con bloqueo automático después de 5 intentos fallidos",
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
                "Estadísticas personales del mes y porcentaje de aprobación",
                "Gestión de autorizaciones activas y por vencer",
                "Sistema de notificaciones para documentos faltantes",
                "Navegación: Nueva Solicitud, Mis Solicitudes, Autorizaciones, Historial"
            ],
            "usuarios": "Representantes de empresas (solicitantes) y empresas de logística y transporte"
        },
        {
            "titulo": "3. NUEVA SOLICITUD",
            "imagen": "docs/capturas/03_nueva_solicitud.png",
            "descripcion": "Formulario completo para crear una nueva solicitud de acceso portuario.",
            "funcionalidades": [
                "Información de la Solicitud: puerto, motivo, fechas, horarios y descripción",
                "Gestión dinámica de vehículos con datos completos",
                "Documentos adjuntos: cédula representante y RNC empresa (requeridos)",
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
                "Estadísticas de rendimiento y porcentaje de aprobación",
                "Sistema de alertas para solicitudes que vencen hoy",
                "Navegación: Dashboard, Evaluaciones, Reportes, Configuración"
            ],
            "usuarios": "Evaluadores portuarios y personal de control y validación"
        },
        {
            "titulo": "5. EVALUAR SOLICITUD",
            "imagen": "docs/capturas/05_evaluar_solicitud.png",
            "descripcion": "Pantalla detallada para la evaluación individual de cada solicitud.",
            "funcionalidades": [
                "Información completa de la empresa: datos, RNC, historial",
                "Detalles del acceso: puerto, motivo, fechas, horarios, descripción",
                "Visualización de documentos adjuntos en nueva ventana",
                "Panel de evaluación: Aprobar, Rechazar, Solicitar documentos, Escalar",
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
                "Scanner de códigos QR: interfaz visual, cámara, búsqueda manual",
                "Verificación de autorizaciones: estado y información completa",
                "Acciones de acceso: autorizar ingreso o denegar con registro automático",
                "Estadísticas del día: accesos procesados, denegados, discrepancias",
                "Historial de registros recientes con tipo de acceso y estado"
            ],
            "usuarios": "Oficiales de control de acceso y personal de seguridad portuaria"
        },
        {
            "titulo": "7. DASHBOARD SUPERVISOR",
            "imagen": "docs/capturas/07_dashboard_supervisor.png",
            "descripcion": "Panel principal para supervisores que manejan escalamientos y discrepancias.",
            "funcionalidades": [
                "Gestión de escalamientos: casos críticos, priorización, resolución",
                "Gestión de discrepancias: problemas de acceso, investigación",
                "Sistema de alertas automáticas con métricas críticas",
                "Estadísticas y reportes: rendimiento global, tasas de aprobación",
                "Panel de acciones rápidas para resolución inmediata"
            ],
            "usuarios": "Supervisores de control de calidad y personal de supervisión general"
        }
    ]
    
    # Agregar cada pantalla con formato optimizado
    for i, pantalla in enumerate(pantallas):
        # Usar KeepTogether para toda la sección de título y descripción
        titulo_seccion = []
        titulo_seccion.append(Paragraph(pantalla["titulo"], titulo_seccion_style))
        titulo_seccion.append(Spacer(1, 6))
        
        # Agregar imagen si existe
        if os.path.exists(pantalla["imagen"]):
            try:
                # Obtener dimensiones y calcular tamaño óptimo
                with PILImage.open(pantalla["imagen"]) as pil_img:
                    original_width, original_height = pil_img.size
                
                # Calcular dimensiones para ocupar casi todo el ancho de la hoja
                page_width = A4[0] - 100  # Ancho disponible (restando márgenes)
                max_width = page_width * 0.98  # 98% del ancho disponible para ligero margen
                
                aspect_ratio = original_height / original_width
                img_width = max_width
                img_height = max_width * aspect_ratio
                
                # Limitar altura para evitar páginas muy largas
                max_height = 4.5 * inch
                if img_height > max_height:
                    img_height = max_height
                    img_width = max_height / aspect_ratio
                
                img = Image(pantalla["imagen"], width=img_width, height=img_height)
                titulo_seccion.append(img)
                titulo_seccion.append(Spacer(1, 12))
                
            except Exception as e:
                print(f"Error al procesar imagen {pantalla['imagen']}: {e}")
                titulo_seccion.append(Paragraph("(Imagen no disponible)", normal_style))
                titulo_seccion.append(Spacer(1, 6))
        
        # Agregar título y imagen como un bloque
        story.append(KeepTogether(titulo_seccion))
        
        # Descripción
        story.append(Paragraph("<b>Descripción:</b>", subseccion_style))
        story.append(Paragraph(pantalla["descripcion"], normal_style))
        story.append(Spacer(1, 8))
        
        # Funcionalidades en formato compacto
        story.append(Paragraph("<b>Funcionalidades Principales:</b>", subseccion_style))
        funcionalidades_texto = []
        for func in pantalla["funcionalidades"]:
            funcionalidades_texto.append(Paragraph(f"• {func}", lista_style))
        
        # Mantener funcionalidades juntas
        story.append(KeepTogether(funcionalidades_texto))
        story.append(Spacer(1, 8))
        
        # Usuarios
        story.append(Paragraph("<b>Usuarios:</b>", subseccion_style))
        story.append(Paragraph(pantalla["usuarios"], normal_style))
        
        # Salto de página después de cada pantalla (excepto la última)
        if i < len(pantallas) - 1:
            story.append(PageBreak())
    
    # === FLUJO DE NAVEGACIÓN ===
    story.append(PageBreak())
    story.append(Paragraph("FLUJO DE NAVEGACIÓN DEL SISTEMA", titulo_seccion_style))
    story.append(Spacer(1, 12))
    
    # Proceso principal en formato compacto
    story.append(Paragraph("<b>Proceso Principal:</b>", subseccion_style))
    flujo_pasos = [
        "1. <b>Login</b> → Redirección automática según rol de usuario",
        "2. <b>Solicitante:</b> Dashboard → Nueva Solicitud → Envío para evaluación",
        "3. <b>Evaluador:</b> Dashboard → Evaluar Solicitud → Decisión",
        "4. <b>Sistema:</b> Generación automática de autorización con código QR",
        "5. <b>Control de Acceso:</b> Scanner QR → Verificación → Autorización",
        "6. <b>Supervisor:</b> Monitoreo de escalamientos y resolución de discrepancias"
    ]
    
    pasos_lista = []
    for paso in flujo_pasos:
        pasos_lista.append(Paragraph(paso, lista_style))
    
    story.append(KeepTogether(pasos_lista))
    story.append(Spacer(1, 12))
    
    # Estados de solicitud
    story.append(Paragraph("<b>Estados de Solicitud:</b>", subseccion_style))
    estados = [
        "<b>Borrador:</b> Guardada pero no enviada",
        "<b>Pendiente:</b> Enviada, esperando evaluación",
        "<b>En Revisión:</b> Asignada a evaluador específico",
        "<b>Aprobada:</b> Genera autorización automáticamente",
        "<b>Rechazada:</b> Finalizada negativamente",
        "<b>Documentos Solicitados:</b> Requiere información adicional",
        "<b>Escalada:</b> Enviada a supervisor para resolución"
    ]
    
    estados_lista = []
    for estado in estados:
        estados_lista.append(Paragraph(f"• {estado}", lista_style))
    
    story.append(KeepTogether(estados_lista))
    
    # Construir el PDF
    doc.build(story)
    print("PDF con formato MEJORADO generado exitosamente: docs/PANTALLAS_SISTEMA_NAVIPORT.pdf")

if __name__ == "__main__":
    crear_pdf_bien_formateado()