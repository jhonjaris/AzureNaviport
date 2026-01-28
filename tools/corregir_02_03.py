#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script específico para corregir las capturas 02 y 03
"""

import asyncio
from playwright.async_api import async_playwright

async def corregir_dashboard_y_formulario():
    """Corrige específicamente el dashboard solicitante y el formulario nueva solicitud"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("=== Corrigiendo Dashboard Solicitante y Nueva Solicitud ===")
            
            # Login como solicitante
            print("1. Haciendo login como solicitante...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'juan.perez')
            await page.fill('input[name="password"]', 'demo123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)
            
            # CAPTURA 02: Dashboard Solicitante
            print("2. Capturando Dashboard Solicitante...")
            # Asegurar que estamos en el dashboard correcto del solicitante
            current_url = page.url
            print(f"   URL actual: {current_url}")
            
            # Si no estamos en el dashboard, navegar a él
            if 'solicitudes/dashboard' not in current_url:
                await page.goto(f"{base_url}/solicitudes/dashboard/")
                await page.wait_for_timeout(3000)
            
            await page.screenshot(path='docs/capturas/02_dashboard_solicitante.png', full_page=True)
            print("   Dashboard Solicitante capturado")
            
            # CAPTURA 03: Formulario Nueva Solicitud
            print("3. Navegando a Nueva Solicitud...")
            
            # Hacer clic en el botón/enlace de "Nueva Solicitud"
            try:
                # Buscar diferentes variantes del botón Nueva Solicitud
                nueva_solicitud_selectors = [
                    'a[href*="nueva_solicitud"]',
                    'a[href*="nueva/"]',
                    'text=Nueva Solicitud',
                    'text=+ Crear Solicitud',
                    '.btn:has-text("Nueva Solicitud")',
                    '.btn:has-text("Crear Solicitud")'
                ]
                
                clicked = False
                for selector in nueva_solicitud_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        await page.click(selector)
                        clicked = True
                        print(f"   Clic exitoso con selector: {selector}")
                        break
                    except:
                        continue
                
                if not clicked:
                    # Si no encuentra el botón, ir directamente por URL
                    print("   No se encontró botón, navegando directamente por URL...")
                    await page.goto(f"{base_url}/solicitudes/nueva/")
                
                await page.wait_for_timeout(4000)
                
            except Exception as e:
                print(f"   Error navegando, usando URL directa: {e}")
                await page.goto(f"{base_url}/solicitudes/nueva/")
                await page.wait_for_timeout(4000)
            
            # Verificar que estamos en la página correcta
            current_url = page.url
            print(f"   URL del formulario: {current_url}")
            
            # Scroll hacia arriba para asegurar que se vea todo el formulario
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            await page.screenshot(path='docs/capturas/03_nueva_solicitud.png', full_page=True)
            print("   Formulario Nueva Solicitud capturado")
            
            print("\n=== CAPTURAS 02 Y 03 CORREGIDAS ===")
            
        except Exception as e:
            print(f"Error durante la corrección: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(corregir_dashboard_y_formulario())