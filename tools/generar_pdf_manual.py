#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de PDF para el Manual de Pantallas NaviPort RD
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os

def crear_pdf_manual():
    """Genera el PDF del manual de pantallas"""
    
    # Configuración del documento
    doc = SimpleDocTemplate(
        "docs/PANTALLAS_SISTEMA_NAVIPORT.pdf",
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
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
    
    # Contenido principal
    contenido = [
        {
            "titulo": "1. PANTALLA DE LOGIN",
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
            "descripcion": "Panel principal para supervisores que manejan escalamientos y discrepancias.",
            "funcionalidades": [
                "Gestión de escalamientos: casos críticos, priorización, resolución, reasignación",
                "Gestión de discrepancias: problemas de acceso, investigación, resolución",
                "Sistema de alertas automáticas con métricas críticas y análisis de tendencias",
                "Estadísticas y reportes: rendimiento global, tasas de aprobación, tiempos de procesamiento",
                "Panel de acciones rápidas para resolución inmediata"
            ],
            "usuarios": "Supervisores de control de calidad y personal de supervisión general"
        },
        {
            "titulo": "8. FLUJO DE NAVEGACIÓN DEL SISTEMA",
            "descripcion": "Proceso completo desde el login hasta la autorización de acceso.",
            "funcionalidades": [
                "Flujo principal: Login → Dashboard por rol → Acción específica",
                "Estados de solicitud: Borrador, Pendiente, En Revisión, Aprobada, Rechazada, Escalada",
                "Generación automática de autorización con código QR al aprobar",
                "Control de acceso físico mediante scanner QR",
                "Sistema de permisos por rol con accesos específicos"
            ],
            "usuarios": "Todos los usuarios según su flujo de trabajo"
        }
    ]
    
    # Agregar cada sección
    for seccion in contenido:
        story.append(Paragraph(seccion["titulo"], subtitulo_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("<b>Descripción:</b>", seccion_style))
        story.append(Paragraph(seccion["descripcion"], normal_style))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("<b>Funcionalidades:</b>", seccion_style))
        for func in seccion["funcionalidades"]:
            story.append(Paragraph(f"• {func}", normal_style))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("<b>Usuarios:</b>", seccion_style))
        story.append(Paragraph(seccion["usuarios"], normal_style))
        story.append(Spacer(1, 20))
    
    # Información adicional
    story.append(PageBreak())
    story.append(Paragraph("INFORMACIÓN ADICIONAL", subtitulo_style))
    
    story.append(Paragraph("<b>Características Técnicas:</b>", seccion_style))
    caracteristicas = [
        "Diseño visual con colores corporativos: Azul (#3498db), Verde (#27ae60), Rojo (#e74c3c)",
        "Iconos emoji para mejor identificación visual",
        "Diseño responsive adaptable a diferentes dispositivos",
        "Navegación clara y controles intuitivos para accesibilidad"
    ]
    for carac in caracteristicas:
        story.append(Paragraph(f"• {carac}", normal_style))
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Usuarios de Prueba:</b>", seccion_style))
    usuarios_prueba = [
        "Admin: admin / admin123",
        "Solicitante: logistica_caribe / demo123", 
        "Evaluador: maria.gonzalez.eval / eval123",
        "Supervisor: roberto.silva / super123",
        "Oficial Acceso: juan.rodriguez / acceso123"
    ]
    for usuario in usuarios_prueba:
        story.append(Paragraph(f"• {usuario}", normal_style))
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Próximos Desarrollos:</b>", seccion_style))
    desarrollos = [
        "Reportes avanzados para rol Dirección",
        "Notificaciones push en tiempo real",
        "App móvil para oficiales de acceso",
        "Integración con sistemas de terceros",
        "Dashboard de métricas en tiempo real",
        "Diseño completamente responsive",
        "Temas claro/oscuro y personalización"
    ]
    for desarrollo in desarrollos:
        story.append(Paragraph(f"• {desarrollo}", normal_style))
    
    # Construir el PDF
    doc.build(story)
    print("PDF generado exitosamente: docs/PANTALLAS_SISTEMA_NAVIPORT.pdf")

if __name__ == "__main__":
    crear_pdf_manual()