import os
import time
from utils.driver_factory import create_driver

driver = create_driver()
time.sleep(8)

page = driver.page_source
with open("page_source.xml", "w", encoding="utf-8") as f:
    f.write(page)

print("Page source saved to page_source.xml")
print(f"Size: {len(page)} bytes")

driver.quit()
