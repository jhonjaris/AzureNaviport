#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para capturar pantallas reales del sistema NaviPort RD
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def capturar_pantallas_simplificado():
    """Captura las pantallas principales del sistema"""
    
    # Crear directorio para capturas
    if not os.path.exists('docs/capturas'):
        os.makedirs('docs/capturas')
    
    async with async_playwright() as p:
        # Lanzar navegador en modo headless para estabilidad
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("=== Capturando pantallas del sistema NaviPort RD ===")
            
            # 1. Pantalla de Login
            print("1. Capturando pantalla de Login...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)  # Esperar a que cargue
            await page.screenshot(path='docs/capturas/01_login.png', full_page=True)
            print("   Login capturado")
            
            # Login como solicitante
            print("2. Entrando como solicitante...")
            await page.fill('input[name="username"]', 'logistica_caribe')
            await page.fill('input[name="password"]', 'demo123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # Dashboard Solicitante
            print("3. Capturando Dashboard Solicitante...")
            await page.screenshot(path='docs/capturas/02_dashboard_solicitante.png', full_page=True)
            print("   Dashboard Solicitante capturado")
            
            # Nueva Solicitud - acceso directo por URL
            print("4. Capturando Nueva Solicitud...")
            await page.goto(f"{base_url}/solicitudes/nueva/")
            await page.wait_for_timeout(3000)
            await page.screenshot(path='docs/capturas/03_nueva_solicitud.png', full_page=True)
            print("   Nueva Solicitud capturada")
            
            # Logout y login como evaluador
            print("5. Cambiando a evaluador...")
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_timeout(1000)
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(1000)
            
            await page.fill('input[name="username"]', 'maria.gonzalez.eval')
            await page.fill('input[name="password"]', 'eval123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # Dashboard Evaluador
            print("6. Capturando Dashboard Evaluador...")
            await page.screenshot(path='docs/capturas/04_dashboard_evaluador.png', full_page=True)
            print("   Dashboard Evaluador capturado")
            
            # Logout y login como oficial de acceso
            print("7. Cambiando a oficial de acceso...")
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_timeout(1000)
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(1000)
            
            await page.fill('input[name="username"]', 'juan.rodriguez')
            await page.fill('input[name="password"]', 'acceso123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # Dashboard Control de Acceso
            print("8. Capturando Dashboard Control de Acceso...")
            await page.screenshot(path='docs/capturas/06_dashboard_control_acceso.png', full_page=True)
            print("   Dashboard Control de Acceso capturado")
            
            # Logout y login como supervisor
            print("9. Cambiando a supervisor...")
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_timeout(1000)
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(1000)
            
            await page.fill('input[name="username"]', 'roberto.silva')
            await page.fill('input[name="password"]', 'super123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # Dashboard Supervisor
            print("10. Capturando Dashboard Supervisor...")
            await page.screenshot(path='docs/capturas/07_dashboard_supervisor.png', full_page=True)
            print("   Dashboard Supervisor capturado")
            
            print("\n=== CAPTURAS COMPLETADAS EXITOSAMENTE ===")
            print("Todas las imagenes reales se guardaron en: docs/capturas/")
            
        except Exception as e:
            print(f"Error durante la captura: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capturar_pantallas_simplificado())