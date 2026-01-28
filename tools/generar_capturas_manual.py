"""
Script para generar capturas de pantalla del manual del evaluador.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'docs', 'capturas_manual')

# Crear directorio de capturas si no existe
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Configuración de Selenium
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")
    
    # Ruta al ChromeDriver
    service = Service(ChromeDriverManager().install())
    
    # Iniciar navegador
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def take_screenshot(driver, filename):
    """Toma una captura de pantalla y la guarda en el directorio especificado."""
    # Asegurarse de que el directorio existe
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Tomar captura de pantalla
    driver.save_screenshot(filename)
    print(f"Captura guardada: {filename}")

def login(driver, base_url, username, password):
    """Inicia sesión en la aplicación."""
    print("Iniciando sesión...")
    driver.get(f"{base_url}/accounts/login/")
    
    # Esperar a que el formulario de login esté disponible
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    
    # Ingresar credenciales
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    # Esperar a que se cargue el dashboard
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
    )
    print("Sesión iniciada correctamente")

def capture_screenshots(driver, base_url):
    """Captura las pantallas del manual."""
    # Capturar dashboard
    driver.get(f"{base_url}/evaluacion/dashboard/")
    time.sleep(2)
    take_screenshot(driver, os.path.join(SCREENSHOTS_DIR, "01_dashboard.png"))
    
    # Capturar lista de empresas
    driver.get(f"{base_url}/evaluacion/empresas/")
    time.sleep(2)
    take_screenshot(driver, os.path.join(SCREENSHOTS_DIR, "02_lista_empresas.png"))
    
    # Capturar formulario de nueva empresa
    driver.get(f"{base_url}/evaluacion/empresas/crear/")
    time.sleep(2)
    take_screenshot(driver, os.path.join(SCREENSHOTS_DIR, "03_nueva_empresa.png"))
    
    # Capturar tipos de licencia
    driver.get(f"{base_url}/evaluacion/tipos-licencia/")
    time.sleep(2)
    take_screenshot(driver, os.path.join(SCREENSHOTS_DIR, "04_tipos_licencia.png"))
    
    # Capturar servicios
    driver.get(f"{base_url}/evaluacion/servicios/")
    time.sleep(2)
    take_screenshot(driver, os.path.join(SCREENSHOTS_DIR, "05_servicios.png"))
    
    # Capturar configuración
    driver.get(f"{base_url}/evaluacion/configuracion/")
    time.sleep(2)
    take_screenshot(driver, os.path.join(SCREENSHOTS_DIR, "06_configuracion.png"))

def main():
    # Configuración
    BASE_URL = "http://localhost:8000"  # Ajustar según la URL de tu entorno
    USERNAME = "asanchez"               # Usuario evaluador
    PASSWORD = "eval123"                # Contraseña del evaluador
    
    try:
        # Iniciar navegador
        print("Iniciando navegador...")
        driver = setup_driver()
        
        # Iniciar sesión
        login(driver, BASE_URL, USERNAME, PASSWORD)
        
        # Tomar capturas de pantalla
        print("Tomando capturas de pantalla...")
        capture_screenshots(driver, BASE_URL)
        
        print("Proceso de captura completado exitosamente!")
        
    except Exception as e:
        print(f"Error durante la ejecución: {str(e)}")
    finally:
        # Cerrar navegador
        if 'driver' in locals():
            driver.quit()
            print("Navegador cerrado.")

if __name__ == "__main__":
    main()
