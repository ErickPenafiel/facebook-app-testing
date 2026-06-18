import os
import time
from utils.driver_factory import create_driver
from pages.base_page import BasePage

driver = create_driver()
time.sleep(8)

page = BasePage(driver)

# Type email
page.type_by_description_contains("Celular o correo electrónico,", "usuario_prueba@test.com")
time.sleep(1)
print("1. Typed email")

# Type password
page.type_by_description_contains("Contraseña,", "PasswordCorrecta123")
time.sleep(1)
print("2. Typed password")

# Dump source BEFORE dismissing keyboard
src = driver.page_source
with open("debug_before_dismiss.xml", "w", encoding="utf-8") as f:
    f.write(src)
print(f"3. Saved before_dismiss ({len(src)} bytes)")

# Try driver.back()
print("4. Trying driver.back()...")
driver.back()
time.sleep(2)

# Dump source AFTER back()
src2 = driver.page_source
with open("debug_after_back.xml", "w", encoding="utf-8") as f:
    f.write(src2)
print(f"5. Saved after_back ({len(src2)} bytes)")

# Try tap at center of screen to dismiss keyboard
driver.tap([(540, 400)])
time.sleep(1)
print("6. Tapped at (540, 400)")

# Try to find login button by various methods
for method, value in [
    ("descriptionContains", "Iniciar sesión"),
    ("description", "Iniciar sesión"),
    ("textContains", "Iniciar sesión"),
    ("text", "Iniciar sesión"),
]:
    try:
        if method == "descriptionContains":
            from appium.webdriver.common.appiumby import AppiumBy
            elems = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{value}")')
            print(f"  UiSelector().descriptionContains('{value}'): {len(elems)} found")
            if elems:
                print(f"    clickable={elems[0].get_attribute('clickable')}, enabled={elems[0].get_attribute('enabled')}")
        elif method == "description":
            elems = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, value)
            print(f"  ACCESSIBILITY_ID '{value}': {len(elems)} found")
        elif method == "textContains":
            elems = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{value}")')
            print(f"  UiSelector().textContains('{value}'): {len(elems)} found")
        elif method == "text":
            elems = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{value}")')
            print(f"  UiSelector().text('{value}'): {len(elems)} found")
    except Exception as e:
        print(f"  {method} error: {e}")

driver.quit()
