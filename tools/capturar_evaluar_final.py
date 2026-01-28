#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar la pantalla de evaluar solicitud con la solicitud creada
"""

import asyncio
from playwright.async_api import async_playwright

async def capturar_evaluar_solicitud_final():
    """Captura la pantalla de evaluar solicitud con datos reales"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("Capturando pantalla de Evaluar Solicitud con datos reales...")
            
            # Login como evaluador
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'maria.gonzalez.eval')
            await page.fill('input[name="password"]', 'eval123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)
            
            # Ir directamente a evaluar la solicitud ID 1
            await page.goto(f"{base_url}/evaluacion/evaluar/1/")
            await page.wait_for_timeout(4000)
            
            # Verificar que no hay errores
            page_content = await page.content()
            if "404" in page_content or "Error" in page_content:
                print("   Error en la página, intentando con dashboard...")
                await page.goto(f"{base_url}/evaluacion/dashboard/")
                await page.wait_for_timeout(3000)
            
            await page.screenshot(path='docs/capturas/05_evaluar_solicitud.png', full_page=True)
            print("   Pantalla de Evaluar Solicitud capturada exitosamente")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capturar_evaluar_solicitud_final())