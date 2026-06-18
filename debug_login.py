import os
import time
from utils.driver_factory import create_driver

driver = create_driver()
time.sleep(8)

# Fill email field
from pages.base_page import BasePage
page = BasePage(driver)
page.type_by_description_contains("Celular o correo electrónico,", "test@test.com")
time.sleep(1)

# Dump page source with keyboard visible
page_source = driver.page_source
with open("page_source_keyboard.xml", "w", encoding="utf-8") as f:
    f.write(page_source)
print(f"Page source saved, size: {len(page_source)} bytes")

# Try to hide keyboard
try:
    driver.hide_keyboard()
    print("hide_keyboard() succeeded")
except Exception as e:
    print(f"hide_keyboard() failed: {e}")

time.sleep(1)
page_source2 = driver.page_source
with open("page_source_after_hide.xml", "w", encoding="utf-8") as f:
    f.write(page_source2)
print(f"After hide source saved, size: {len(page_source2)} bytes")

driver.quit()
