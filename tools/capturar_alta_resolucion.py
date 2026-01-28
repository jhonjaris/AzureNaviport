#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar pantallas en alta resolución para el PDF
"""

import asyncio
from playwright.async_api import async_playwright

async def capturar_alta_resolucion():
    """Captura todas las pantallas en alta resolución"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1200},  # Resolución más alta
            device_scale_factor=2  # Factor de escala para mejor calidad
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("=== Capturando pantallas en ALTA RESOLUCION ===")
            
            # 1. Login
            print("1. Capturando Login en alta resolución...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(3000)
            await page.screenshot(
                path='docs/capturas/01_login.png', 
                full_page=True,
                type='png'    # PNG para mejor calidad que JPEG
            )
            print("   Login HD capturado")
            
            # Login como solicitante
            print("2. Login como solicitante...")
            await page.fill('input[name="username"]', 'navieros_unidos')
            await page.fill('input[name="password"]', 'demo123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)
            
            # 2. Dashboard Solicitante
            print("3. Capturando Dashboard Solicitante HD...")
            await page.goto(f"{base_url}/solicitudes/dashboard/")
            await page.wait_for_timeout(4000)
            await page.screenshot(
                path='docs/capturas/02_dashboard_solicitante.png', 
                full_page=True,
                type='png'
            )
            print("   Dashboard Solicitante HD capturado")
            
            # 3. Nueva Solicitud
            print("4. Capturando Nueva Solicitud HD...")
            await page.goto(f"{base_url}/solicitudes/nueva/")
            await page.wait_for_timeout(4000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            await page.screenshot(
                path='docs/capturas/03_nueva_solicitud.png', 
                full_page=True,
                type='png'
            )
            print("   Nueva Solicitud HD capturada")
            
            # Logout y login como evaluador
            print("5. Cambiando a evaluador...")
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_timeout(2000)
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'maria.gonzalez.eval')
            await page.fill('input[name="password"]', 'eval123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)
            
            # 4. Dashboard Evaluador
            print("6. Capturando Dashboard Evaluador HD...")
            await page.screenshot(
                path='docs/capturas/04_dashboard_evaluador.png', 
                full_page=True,
                type='png'
            )
            print("   Dashboard Evaluador HD capturado")
            
            # 5. Evaluar Solicitud
            print("7. Capturando Evaluar Solicitud HD...")
            try:
                await page.goto(f"{base_url}/evaluacion/evaluar/1/")
                await page.wait_for_timeout(4000)
                page_content = await page.content()
                if "404" in page_content or "Error" in page_content:
                    raise Exception("No hay solicitudes")
            except:
                # Si no hay solicitudes específicas, mantener dashboard
                await page.goto(f"{base_url}/evaluacion/dashboard/")
                await page.wait_for_timeout(3000)
            
            await page.screenshot(
                path='docs/capturas/05_evaluar_solicitud.png', 
                full_page=True,
                type='png'
            )
            print("   Evaluar Solicitud HD capturada")
            
            # Logout y login como oficial de acceso
            print("8. Cambiando a oficial de acceso...")
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_timeout(2000)
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'juan.rodriguez')
            await page.fill('input[name="password"]', 'acceso123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)
            
            # 6. Dashboard Control de Acceso
            print("9. Capturando Dashboard Control de Acceso HD...")
            await page.screenshot(
                path='docs/capturas/06_dashboard_control_acceso.png', 
                full_page=True,
                type='png'
            )
            print("   Dashboard Control de Acceso HD capturado")
            
            # Logout y login como supervisor
            print("10. Cambiando a supervisor...")
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_timeout(2000)
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'roberto.silva')
            await page.fill('input[name="password"]', 'super123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)
            
            # 7. Dashboard Supervisor
            print("11. Capturando Dashboard Supervisor HD...")
            await page.screenshot(
                path='docs/capturas/07_dashboard_supervisor.png', 
                full_page=True,
                type='png'
            )
            print("   Dashboard Supervisor HD capturado")
            
            print("\n=== TODAS LAS CAPTURAS EN ALTA RESOLUCION COMPLETADAS ===")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capturar_alta_resolucion())