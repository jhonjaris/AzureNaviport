#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir las capturas específicas que salieron mal
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def corregir_capturas_especificas():
    """Corrige las capturas que salieron mal"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("=== Corrigiendo capturas específicas ===")
            
            # CORREGIR 02: Dashboard Solicitante
            print("1. Corrigiendo Dashboard Solicitante...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'logistica_caribe')
            await page.fill('input[name="password"]', 'demo123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)  # Más tiempo para cargar
            
            # Asegurar que estamos en el dashboard correcto
            await page.goto(f"{base_url}/solicitudes/dashboard/")
            await page.wait_for_timeout(3000)
            await page.screenshot(path='docs/capturas/02_dashboard_solicitante.png', full_page=True)
            print("   Dashboard Solicitante corregido")
            
            # CORREGIR 03: Nueva Solicitud - formulario completo
            print("2. Corrigiendo Nueva Solicitud...")
            await page.goto(f"{base_url}/solicitudes/nueva/")
            await page.wait_for_timeout(4000)  # Esperar a que cargue completamente
            
            # Scroll para asegurar que se vea todo el formulario
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            await page.screenshot(path='docs/capturas/03_nueva_solicitud.png', full_page=True)
            print("   Nueva Solicitud corregida")
            
            # Logout y cambiar a evaluador
            await page.goto(f"{base_url}/accounts/logout/")
            await page.wait_for_timeout(2000)
            
            # CORREGIR 05: Evaluar Solicitud sin errores
            print("3. Corrigiendo Evaluar Solicitud...")
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'maria.gonzalez.eval')
            await page.fill('input[name="password"]', 'eval123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)
            
            # Ir al dashboard de evaluador primero
            await page.goto(f"{base_url}/evaluacion/dashboard/")
            await page.wait_for_timeout(3000)
            
            # Intentar diferentes URLs para evaluar solicitud
            urls_a_probar = [
                f"{base_url}/evaluacion/evaluar/1/",
                f"{base_url}/evaluacion/evaluar/2/",
                f"{base_url}/evaluacion/evaluar/3/"
            ]
            
            captura_exitosa = False
            for url in urls_a_probar:
                try:
                    await page.goto(url)
                    await page.wait_for_timeout(3000)
                    
                    # Verificar si hay error 404 o similar
                    page_content = await page.content()
                    if "404" not in page_content and "Error" not in page_content and "not found" not in page_content.lower():
                        await page.screenshot(path='docs/capturas/05_evaluar_solicitud.png', full_page=True)
                        print(f"   Evaluar Solicitud corregida (URL: {url})")
                        captura_exitosa = True
                        break
                except:
                    continue
            
            if not captura_exitosa:
                # Si no hay solicitudes, crear una vista de formulario de evaluación vacío
                print("   No hay solicitudes disponibles, manteniendo dashboard de evaluador")
                await page.goto(f"{base_url}/evaluacion/dashboard/") 
                await page.wait_for_timeout(3000)
                await page.screenshot(path='docs/capturas/05_evaluar_solicitud.png', full_page=True)
                print("   Dashboard de evaluador capturado como alternativa")
            
            print("\n=== CAPTURAS CORREGIDAS EXITOSAMENTE ===")
            
        except Exception as e:
            print(f"Error durante la corrección: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(corregir_capturas_especificas())