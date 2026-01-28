#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar pantallas reales del sistema NaviPort RD con Playwright
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def capturar_pantallas_reales():
    """Captura las pantallas reales del sistema con todos los estilos"""
    
    # Crear directorio para capturas
    if not os.path.exists('docs/capturas'):
        os.makedirs('docs/capturas')
    
    async with async_playwright() as p:
        # Lanzar navegador
        browser = await p.chromium.launch(headless=False)  # No headless para ver el proceso
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            # 1. Pantalla de Login
            print("Capturando pantalla de Login...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_load_state('networkidle')
            await page.screenshot(path='docs/capturas/01_login.png', full_page=True)
            
            # Login como solicitante
            print("Entrando como solicitante...")
            await page.fill('input[name="username"]', 'logistica_caribe')
            await page.fill('input[name="password"]', 'demo123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # 2. Dashboard Solicitante
            print("Capturando Dashboard Solicitante...")
            await page.screenshot(path='docs/capturas/02_dashboard_solicitante.png', full_page=True)
            
            # 3. Nueva Solicitud
            print("Navegando a Nueva Solicitud...")
            try:
                # Buscar el enlace de nueva solicitud
                await page.click('a[href*="nueva_solicitud"]')
                await page.wait_for_load_state('networkidle')
                await page.screenshot(path='docs/capturas/03_nueva_solicitud.png', full_page=True)
            except:
                print("No se pudo acceder a Nueva Solicitud, intentando con botón...")
                try:
                    await page.click('text=Nueva Solicitud')
                    await page.wait_for_load_state('networkidle')
                    await page.screenshot(path='docs/capturas/03_nueva_solicitud.png', full_page=True)
                except:
                    print("No se encontró el enlace a Nueva Solicitud")
            
            # Logout
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_load_state('networkidle')
            
            # Login como evaluador
            print("Entrando como evaluador...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_load_state('networkidle')
            await page.fill('input[name="username"]', 'maria.gonzalez.eval')
            await page.fill('input[name="password"]', 'eval123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # 4. Dashboard Evaluador
            print("Capturando Dashboard Evaluador...")
            await page.screenshot(path='docs/capturas/04_dashboard_evaluador.png', full_page=True)
            
            # 5. Intentar acceder a evaluar solicitud
            print("Buscando solicitud para evaluar...")
            try:
                # Buscar botón "Evaluar" en la tabla
                await page.click('a[href*="evaluar_solicitud"], text=Evaluar')
                await page.wait_for_load_state('networkidle')
                await page.screenshot(path='docs/capturas/05_evaluar_solicitud.png', full_page=True)
            except:
                print("No se encontraron solicitudes para evaluar")
            
            # Logout
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_load_state('networkidle')
            
            # Login como oficial de acceso
            print("Entrando como oficial de acceso...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_load_state('networkidle')
            await page.fill('input[name="username"]', 'juan.rodriguez')
            await page.fill('input[name="password"]', 'acceso123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # 6. Dashboard Control de Acceso
            print("Capturando Dashboard Control de Acceso...")
            await page.screenshot(path='docs/capturas/06_dashboard_control_acceso.png', full_page=True)
            
            # Logout
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_load_state('networkidle')
            
            # Login como supervisor
            print("Entrando como supervisor...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_load_state('networkidle')
            await page.fill('input[name="username"]', 'roberto.silva')
            await page.fill('input[name="password"]', 'super123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # 7. Dashboard Supervisor
            print("Capturando Dashboard Supervisor...")
            await page.screenshot(path='docs/capturas/07_dashboard_supervisor.png', full_page=True)
            
            print("Capturas completadas exitosamente!")
            print("Las imagenes reales se guardaron en: docs/capturas/")
            
        except Exception as e:
            print(f"Error durante la captura: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capturar_pantallas_reales())