#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script definitivo para corregir las capturas 02 y 03
"""

import asyncio
from playwright.async_api import async_playwright

async def corregir_capturas_definitivo():
    """Corrige definitivamente las capturas con usuario válido"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("=== CORRECCIÓN DEFINITIVA DE CAPTURAS 02 Y 03 ===")
            
            # Login como solicitante con usuario válido
            print("1. Haciendo login como solicitante...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(3000)
            
            # Usar usuario que sabemos que existe
            await page.fill('input[name="username"]', 'navieros_unidos')
            await page.fill('input[name="password"]', 'demo123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)
            
            # Verificar que el login fue exitoso
            current_url = page.url
            print(f"   URL después del login: {current_url}")
            
            if 'login' in current_url:
                # Intentar con otro usuario
                print("   Intentando con juan.perez...")
                await page.fill('input[name="username"]', 'juan.perez')
                await page.fill('input[name="password"]', 'demo123')
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(5000)
                current_url = page.url
                print(f"   Nueva URL: {current_url}")
            
            # CAPTURA 02: Dashboard Solicitante
            print("2. Capturando Dashboard Solicitante...")
            
            if 'login' not in current_url:
                # Login exitoso, ir al dashboard
                await page.goto(f"{base_url}/solicitudes/dashboard/")
                await page.wait_for_timeout(4000)
                await page.screenshot(path='docs/capturas/02_dashboard_solicitante.png', full_page=True)
                print("   Dashboard Solicitante capturado")
                
                # CAPTURA 03: Formulario Nueva Solicitud
                print("3. Capturando Nueva Solicitud...")
                await page.goto(f"{base_url}/solicitudes/nueva/")
                await page.wait_for_timeout(4000)
                
                # Scroll hacia arriba
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(1000)
                
                await page.screenshot(path='docs/capturas/03_nueva_solicitud.png', full_page=True)
                print("   Nueva Solicitud capturada")
                
                print("\n=== CAPTURAS CORREGIDAS EXITOSAMENTE ===")
            else:
                print("   Error: No se pudo hacer login con ningún usuario")
                await page.screenshot(path='docs/capturas/debug_login_error.png')
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(corregir_capturas_definitivo())