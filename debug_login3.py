import os
import time
from utils.driver_factory import create_driver
from pages.base_page import BasePage

driver = create_driver()
time.sleep(8)

page = BasePage(driver)

page.type_by_description_contains("Celular o correo electrónico,", "usuario_prueba@test.com")
time.sleep(1)
page.type_by_description_contains("Contraseña,", "PasswordCorrecta123")
time.sleep(1)

print("Dismissing keyboard with back()...")
driver.back()
time.sleep(1)

from appium.webdriver.common.appiumby import AppiumBy

# Try to find login button
for strategy, desc in [
    ("descContains", 'new UiSelector().descriptionContains("Iniciar sesión")'),
    ("textContains", 'new UiSelector().textContains("Iniciar sesión")'),
    ("descExact", 'new UiSelector().description("Iniciar sesión")'),
    ("textExact", 'new UiSelector().text("Iniciar sesión")'),
]:
    try:
        elems = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, desc)
        print(f"  {strategy}: {len(elems)} found")
        for e in elems:
            print(f"    clickable={e.get_attribute('clickable')} enabled={e.get_attribute('enabled')} displayed={e.get_attribute('displayed')} bounds={e.get_attribute('bounds')} class={e.get_attribute('className')}")
    except Exception as ex:
        print(f"  {strategy} error: {ex}")

# Try clicking directly
try:
    btn = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Iniciar sesión")')
    print(f"Found button, clicking...")
    btn.click()
    print("CLICK SUCCEEDED!")
    time.sleep(2)
    # Check if we navigated away
    print(f"Current page source size: {len(driver.page_source)}")
    print(f"Logged in: {page.is_text_visible('Inicio') or page.is_text_visible('Menú')}")
except Exception as ex:
    print(f"Click failed: {ex}")

driver.quit()
