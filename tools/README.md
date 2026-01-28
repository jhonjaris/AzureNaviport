# Tools - Herramientas de Desarrollo

Esta carpeta contiene scripts de utilidades, herramientas de desarrollo y archivos de prueba utilizados durante el desarrollo del sistema NaviPort RD.

## Scripts de Base de Datos
- `reset_database.py` - Resetea completamente la base de datos
- `fix_database.py` - Repara problemas específicos de BD
- `create_sample_data.py` - Crea datos de ejemplo para empresas y usuarios
- `create_test_solicitudes.py` - Genera solicitudes de prueba

## Scripts de Debug y Verificación
- `debug_admin_view.py` - Debug del panel de administración
- `debug_session.py` - Verificación de sesiones de usuario
- `check_admin.py` - Verifica configuración de admin
- `check_superuser.py` - Verifica estado del superusuario
- `test_login.py` - Pruebas de autenticación
- `verificar_usuarios.py` - Verificación de usuarios del sistema

## Scripts de Captura/Documentación
- `capturar_pantallas.py` - Captura pantallas del sistema
- `capturar_pantallas_reales.py` - Capturas con datos reales
- `capturar_alta_resolucion.py` - Capturas en alta resolución
- `capturar_simple.py` - Capturas básicas
- `capturar_evaluar_solicitud.py` - Captura proceso de evaluación
- `capturar_evaluar_final.py` - Captura estado final de evaluación

## Scripts de Generación de PDFs
- `generar_pdf_manual.py` - Generación manual de PDFs
- `generar_pdf_formateado.py` - PDFs con formato específico
- `generar_pdf_con_imagenes.py` - PDFs incluyendo imágenes
- `generar_pdf_alta_resolucion.py` - PDFs en alta resolución

## Scripts de Corrección
- `corregir_02_03.py` - Corrección específica versión 02-03
- `corregir_02_03_final.py` - Versión final de corrección
- `corregir_capturas.py` - Corrección de capturas
- `corregir_capturas_definitivo.py` - Versión definitiva

## Scripts de Utilidades
- `add_logout_to_templates.py` - Añade logout a templates
- `crear_imagenes_muestra.py` - Crea imágenes de muestra
- `crear_solicitud_ejemplo.py` - Crea solicitud de ejemplo

## Archivos de Prueba
- `test_template.html` - Template de prueba
- `test_formatting.html` - Pruebas de formato
- `juan.perez  juan.perez  ship chande.txt` - Archivo temporal

## Uso
Estos scripts deben ejecutarse desde la raíz del proyecto:

```bash
# Ejemplo: resetear base de datos
python tools/reset_database.py

# Ejemplo: crear datos de prueba
python tools/create_sample_data.py
```

**Nota:** Muchos de estos scripts son específicos para versiones de desarrollo y pueden no ser necesarios en producción.