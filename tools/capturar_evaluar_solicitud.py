#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar la pantalla de evaluar solicitud específicamente
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def capturar_evaluar_solicitud():
    """Captura la pantalla de evaluar solicitud si hay solicitudes disponibles"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            base_url = "http://127.0.0.1:8002"
            
            print("Intentando capturar pantalla de Evaluar Solicitud...")
            
            # Login como evaluador
            await page.goto(f"{base_url}/login/")
            await page.wait_for_timeout(2000)
            
            await page.fill('input[name="username"]', 'maria.gonzalez.eval')
            await page.fill('input[name="password"]', 'eval123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # Buscar y navegar a una solicitud para evaluar
            try:
                # Intentar encontrar solicitudes disponibles
                await page.goto(f"{base_url}/evaluacion/evaluar/1/")
                await page.wait_for_timeout(3000)
                
                # Si llegamos aquí, hay una solicitud
                await page.screenshot(path='docs/capturas/05_evaluar_solicitud.png', full_page=True)
                print("   Pantalla de Evaluar Solicitud capturada")
                
            except Exception:
                print("   No hay solicitudes disponibles para evaluar")
                print("   Creando pantalla de muestra...")
                
                # Si no hay solicitudes, ir al dashboard y capturar eso
                await page.goto(f"{base_url}/evaluacion/dashboard/")
                await page.wait_for_timeout(3000)
                await page.screenshot(path='docs/capturas/05_evaluar_solicitud.png', full_page=True)
                print("   Dashboard de evaluación capturado como alternativa")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capturar_evaluar_solicitud())