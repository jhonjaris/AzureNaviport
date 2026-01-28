#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script final para corregir las capturas 02 y 03 con las credenciales correctas
"""

import asyncio
from playwright.async_api import async_playwright

async def corregir_dashboard_y_formulario_final():
    """Corrige específicamente el dashboard solicitante y el formulario nueva solicitud"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("=== Corrigiendo Dashboard Solicitante y Nueva Solicitud (FINAL) ===")
            
            # Login como solicitante con credenciales correctas
            print("1. Haciendo login como solicitante...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            # Usar credenciales correctas
            await page.fill('input[name="username"]', 'logistica_caribe') 
            await page.fill('input[name="password"]', 'demo123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)
            
            # Verificar que el login fue exitoso
            current_url = page.url
            print(f"   URL después del login: {current_url}")
            
            # CAPTURA 02: Dashboard Solicitante
            print("2. Capturando Dashboard Solicitante...")
            
            # Si no estamos en el dashboard, navegar a él explícitamente
            if 'login' in current_url:
                print("   Login falló, verificando...")
                await page.screenshot(path='docs/capturas/debug_login.png')
                return
            
            if 'solicitudes/dashboard' not in current_url:
                await page.goto(f"{base_url}/solicitudes/dashboard/")
                await page.wait_for_timeout(3000)
            
            await page.screenshot(path='docs/capturas/02_dashboard_solicitante.png', full_page=True)
            print("   Dashboard Solicitante capturado exitosamente")
            
            # CAPTURA 03: Formulario Nueva Solicitud
            print("3. Navegando a Nueva Solicitud...")
            
            # Ir directamente por URL para asegurar que llegamos
            await page.goto(f"{base_url}/solicitudes/nueva/")
            await page.wait_for_timeout(4000)
            
            # Verificar que estamos en la página correcta
            current_url = page.url
            print(f"   URL del formulario: {current_url}")
            
            if 'login' in current_url:
                print("   Sesión expiró, relogueando...")
                await page.fill('input[name="username"]', 'logistica_caribe')
                await page.fill('input[name="password"]', 'demo123')
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(3000)
                await page.goto(f"{base_url}/solicitudes/nueva/")
                await page.wait_for_timeout(3000)
            
            # Scroll hacia arriba para asegurar que se vea todo el formulario
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            await page.screenshot(path='docs/capturas/03_nueva_solicitud.png', full_page=True)
            print("   Formulario Nueva Solicitud capturado exitosamente")
            
            print("\n=== CAPTURAS 02 Y 03 CORREGIDAS DEFINITIVAMENTE ===")
            
        except Exception as e:
            print(f"Error durante la corrección: {e}")
            # Capturar pantalla de debug
            try:
                await page.screenshot(path='docs/capturas/debug_error.png')
            except:
                pass
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(corregir_dashboard_y_formulario_final())