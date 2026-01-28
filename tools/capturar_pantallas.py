#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar pantallas del sistema NaviPort RD
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def setup_driver():
    """Configura el driver de Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error al inicializar Chrome: {e}")
        print("Asegúrate de tener Chrome y ChromeDriver instalados")
        return None

def capturar_pantallas():
    """Captura las pantallas principales del sistema"""
    
    # Crear directorio para capturas
    if not os.path.exists('docs/capturas'):
        os.makedirs('docs/capturas')
    
    driver = setup_driver()
    if not driver:
        return
    
    try:
        base_url = "http://127.0.0.1:8002"
        wait = WebDriverWait(driver, 10)
        
        # 1. Pantalla de Login
        print("Capturando pantalla de Login...")
        driver.get(f"{base_url}/login/")
        time.sleep(2)
        driver.save_screenshot('docs/capturas/01_login.png')
        
        # Login como solicitante
        print("Entrando como solicitante...")
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("logistica_caribe")
        password_field.send_keys("demo123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(3)
        
        # 2. Dashboard Solicitante
        print("Capturando Dashboard Solicitante...")
        driver.save_screenshot('docs/capturas/02_dashboard_solicitante.png')
        
        # 3. Nueva Solicitud
        print("Navegando a Nueva Solicitud...")
        try:
            nueva_solicitud_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'nueva_solicitud')]")))
            nueva_solicitud_link.click()
            time.sleep(3)
            driver.save_screenshot('docs/capturas/03_nueva_solicitud.png')
        except:
            print("No se pudo acceder a Nueva Solicitud")
        
        # Logout
        driver.get(f"{base_url}/accounts/logout/")
        time.sleep(2)
        
        # Login como evaluador
        print("Entrando como evaluador...")
        driver.get(f"{base_url}/login/")
        time.sleep(2)
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("maria.gonzalez.eval")
        password_field.send_keys("eval123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(3)
        
        # 4. Dashboard Evaluador
        print("Capturando Dashboard Evaluador...")
        driver.save_screenshot('docs/capturas/04_dashboard_evaluador.png')
        
        # Logout
        driver.get(f"{base_url}/accounts/logout/")
        time.sleep(2)
        
        # Login como oficial de acceso
        print("Entrando como oficial de acceso...")
        driver.get(f"{base_url}/login/")
        time.sleep(2)
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("juan.rodriguez")
        password_field.send_keys("acceso123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(3)
        
        # 5. Dashboard Control de Acceso
        print("Capturando Dashboard Control de Acceso...")
        driver.save_screenshot('docs/capturas/05_dashboard_control_acceso.png')
        
        # Logout
        driver.get(f"{base_url}/accounts/logout/")
        time.sleep(2)
        
        # Login como supervisor
        print("Entrando como supervisor...")
        driver.get(f"{base_url}/login/")
        time.sleep(2)
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("roberto.silva")
        password_field.send_keys("super123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(3)
        
        # 6. Dashboard Supervisor
        print("Capturando Dashboard Supervisor...")
        driver.save_screenshot('docs/capturas/06_dashboard_supervisor.png')
        
        print("Capturas completadas exitosamente!")
        print("Las imagenes se guardaron en: docs/capturas/")
        
    except Exception as e:
        print(f"Error durante la captura: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    capturar_pantallas()