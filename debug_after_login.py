import os
import time
from utils.driver_factory import create_driver
from pages.login_page import LoginPage

driver = create_driver()
time.sleep(8)

login = LoginPage(driver)
login.login(os.getenv("FB_EMAIL"), os.getenv("FB_PASSWORD"))
time.sleep(5)

# Dump page source after login attempt
src = driver.page_source
with open("debug_after_login.xml", "w", encoding="utf-8") as f:
    f.write(src)
print(f"Page source saved ({len(src)} bytes)")

# Check what text/descriptions are visible
from appium.webdriver.common.appiumby import AppiumBy
for search in ["celular", "correo", "contraseña", "inicio", "menú", "buscar", "historias", "no encontramos", "incorrecta", "facebook"]:
    text_elems = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{search}")')
    desc_elems = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{search}")')
    if text_elems or desc_elems:
        print(f"  '{search}': text={len(text_elems)}, desc={len(desc_elems)}")

driver.quit()
