import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    # ==========================================================
    # WAITS BÁSICOS
    # ==========================================================

    def wait_for_element(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_clickable(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    # ==========================================================
    # TAP POR TEXTO / DESCRIPCIÓN
    # ==========================================================

    def tap_by_text(self, text, timeout=10):
        element = self.wait_for_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{text}")'
            ),
            timeout
        )
        element.click()

    def tap_by_text_force(self, text, timeout=10):
        """Tap by text using presence (not clickable) check.
        Needed when element has enabled=false but UiAutomator2 can still tap it."""
        locators = [
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{text}")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{text}")'),
            (AppiumBy.XPATH, f'//*[@text="{text}"]'),
            (AppiumBy.XPATH, f'//*[contains(@text, "{text}")]'),
        ]
        for locator in locators:
            try:
                element = self.wait_for_element(locator, timeout)
                element.click()
                return
            except Exception:
                continue
        raise Exception(f"No se pudo encontrar elemento con texto '{text}'")

    def tap_by_exact_text(self, text, timeout=10):
        element = self.wait_for_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().text("{text}")'
            ),
            timeout
        )
        element.click()

    def tap_by_description_contains(self, description, timeout=10):
        element = self.wait_for_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().descriptionContains("{description}")'
            ),
            timeout
        )
        element.click()

    def tap_by_exact_description(self, description, timeout=10):
        element = self.wait_for_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().description("{description}")'
            ),
            timeout
        )
        element.click()

    # ==========================================================
    # MÉTODO ROBUSTO PARA ESCRIBIR EN INPUTS
    # ==========================================================

    def type_into_edittext_by_hint_or_desc(self, label, value, timeout=10):
        """
        Busca un campo android.widget.EditText real y escribe dentro.
        Evita el error:
        InvalidElementStateException: Cannot set the element...
        """

        if value is None:
            raise ValueError(f"El valor para escribir en '{label}' es None.")

        locators = [
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.EditText").descriptionContains("{label}")'
            ),
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.EditText").textContains("{label}")'
            ),
            (
                AppiumBy.XPATH,
                f'//android.widget.EditText[contains(@content-desc, "{label}")]'
            ),
            (
                AppiumBy.XPATH,
                f'//android.widget.EditText[contains(@text, "{label}")]'
            ),
            (
                AppiumBy.XPATH,
                f'//*[@editable="true" and contains(@content-desc, "{label}")]'
            ),
            (
                AppiumBy.XPATH,
                f'//*[@editable="true" and contains(@text, "{label}")]'
            ),
        ]

        last_error = None

        for locator in locators:
            try:
                element = self.wait_for_clickable(locator, timeout)

                element.click()
                time.sleep(0.5)

                try:
                    element.clear()
                except Exception:
                    pass

                element.send_keys(value)
                return True

            except Exception as error:
                last_error = error

        raise Exception(
            f"No se pudo escribir en el campo '{label}'. "
            f"Último error: {last_error}"
        )

    def type_by_edittext_index(self, index, value, timeout=10):
        """
        Método alternativo para escribir usando el índice del EditText.
        Usa UiSelector().instance() que busca en todos los accessibility windows,
        incluyendo cuando hay popups de sistema (Google Password Manager) activos.
        """
        from selenium.common.exceptions import StaleElementReferenceException

        if value is None:
            raise ValueError(f"El valor para el input #{index} es None.")

        locator = (AppiumBy.ANDROID_UIAUTOMATOR,
                   f'new UiSelector().className("android.widget.EditText").instance({index})')

        element = self.wait_for_element(locator, timeout)
        element.click()
        # El autofill picker de Android refresca el árbol de vistas tras el click,
        # dejando la referencia stale. Re-encontrar antes de send_keys.
        time.sleep(0.8)
        element = self.wait_for_element(locator, timeout)

        try:
            element.clear()
        except Exception:
            pass

        for attempt in range(3):
            try:
                element.send_keys(value)
                return True
            except StaleElementReferenceException:
                if attempt == 2:
                    raise
                time.sleep(0.5)
                element = self.wait_for_element(locator, timeout)

    def type_by_description_contains(self, description, value, timeout=10):
        """
        Versión corregida del método original.
        Ahora obliga a buscar un EditText real.
        """
        return self.type_into_edittext_by_hint_or_desc(
            description,
            value,
            timeout
        )

    # ==========================================================
    # VALIDACIONES
    # ==========================================================

    def is_text_visible(self, text, timeout=1):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{text}")'
                    )
                )
            )
            return True
        except WebDriverException:
            return False
        except Exception:
            return False

    def is_description_visible(self, description, timeout=1):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().descriptionContains("{description}")'
                    )
                )
            )
            return True
        except WebDriverException:
            return False
        except Exception:
            return False

    def is_element_visible(self, locator, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except Exception:
            return False

    # ==========================================================
    # TECLADO
    # ==========================================================

    def dismiss_keyboard(self):
        try:
            self.driver.hide_keyboard()
        except WebDriverException:
            try:
                self.driver.back()
            except WebDriverException:
                pass

        time.sleep(1)

    # ==========================================================
    # SCROLL
    # ==========================================================

    def scroll_to_text(self, text):
        return self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiScrollable(new UiSelector().scrollable(true)).scrollTextIntoView("{text}")'
        )

    # ==========================================================
    # DEBUG
    # ==========================================================

    def print_input_candidates(self):
        print("\n--- INPUTS EN PANTALLA ---")

        elements = self.driver.find_elements(
            AppiumBy.XPATH,
            '//*[@class="android.widget.EditText" or @editable="true"]'
        )

        print(f"Inputs encontrados: {len(elements)}")

        for index, element in enumerate(elements):
            try:
                print(f"\nInput #{index + 1}")
                print("text:", element.get_attribute("text"))
                print("content-desc:", element.get_attribute("content-desc"))
                print("resource-id:", element.get_attribute("resource-id"))
                print("class:", element.get_attribute("class"))
                print("editable:", element.get_attribute("editable"))
                print("enabled:", element.get_attribute("enabled"))
                print("clickable:", element.get_attribute("clickable"))
                print("focused:", element.get_attribute("focused"))
                print("bounds:", element.get_attribute("bounds"))
            except Exception as error:
                print("No se pudo leer input:", error)

    def print_button_candidates(self, text="Iniciar"):
        print(f"\n--- BOTONES O ELEMENTOS CON '{text}' ---")

        elements = self.driver.find_elements(
            AppiumBy.XPATH,
            f'//*[contains(@text, "{text}") or contains(@content-desc, "{text}")]'
        )

        print(f"Elementos encontrados: {len(elements)}")

        for index, element in enumerate(elements):
            try:
                print(f"\nElemento #{index + 1}")
                print("text:", element.get_attribute("text"))
                print("content-desc:", element.get_attribute("content-desc"))
                print("resource-id:", element.get_attribute("resource-id"))
                print("class:", element.get_attribute("class"))
                print("enabled:", element.get_attribute("enabled"))
                print("clickable:", element.get_attribute("clickable"))
                print("displayed:", element.is_displayed())
                print("bounds:", element.get_attribute("bounds"))
            except Exception as error:
                print("No se pudo leer elemento:", error)

    def print_page_source(self):
        print("\n--- PAGE SOURCE ---")
        print(self.driver.page_source)

    @staticmethod
    def _screenshots_dir(name):
        """Devuelve la ruta de carpeta de evidencia según el prefijo del nombre."""
        import os
        if name.startswith("TC_AUTH_") or name.startswith("ensure_"):
            subdir = os.path.join("reports", "screenshots", "auth")
        elif name.startswith("TC_FB_MSG_"):
            subdir = os.path.join("reports", "screenshots", "messaging")
        elif name.startswith("TC_FB_NOT_"):
            subdir = os.path.join("reports", "screenshots", "notifications")
        else:
            subdir = os.path.join("reports", "screenshots")
        os.makedirs(subdir, exist_ok=True)
        return subdir

    def take_screenshot(self, name):
        import os
        from datetime import datetime

        screenshots_dir = self._screenshots_dir(name)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(screenshots_dir, f"{name}_{timestamp}.png")

        try:
            self.driver.save_screenshot(file_path)
            print(f"Screenshot guardado en: {file_path}")
        except Exception as e:
            print(f"Screenshot falló (driver/UiAutomator2 error): {e}")
            return None

        return file_path

    def _save_page_source(self, name):
        import os
        from datetime import datetime

        screenshots_dir = self._screenshots_dir(name)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(screenshots_dir, f"{name}_{timestamp}.xml")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        print(f"Page source guardado en: {file_path}")

        return file_path