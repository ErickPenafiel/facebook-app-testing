import os
import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from pages.base_page import BasePage


class LoginPage(BasePage):
    EMAIL_INPUT_DESC = "Celular o correo electrónico"
    PASSWORD_INPUT_DESC = "Contraseña"
    LOGIN_BUTTON_DESC = "Iniciar sesión"
    FORGOT_PASSWORD_DESC = "¿Olvidaste tu contraseña?"
    CREATE_ACCOUNT_BUTTON_DESC = "Crear cuenta nueva"

    def login(self, email=None, password=None):
        """
        Login principal.
        Primero intenta escribir usando los localizadores correctos.
        Si Facebook no expone bien los inputs, usa fallback por índice.
        """

        if email is None:
            email = os.getenv("FB_EMAIL")

        if password is None:
            password = os.getenv("FB_PASSWORD")

        if not email:
            raise ValueError("No se recibió email y tampoco existe la variable FB_EMAIL.")

        if not password:
            raise ValueError("No se recibió password y tampoco existe la variable FB_PASSWORD.")
        self._save_page_source("DEBUG_login_start")
        self.take_screenshot("DEBUG_login_start")

        self._dismiss_gm_popup_if_present()
        try:
            email_elem = self.wait_for_element(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().className("android.widget.EditText").instance(0)'),
                timeout=10
            )
            email_elem.click()
            time.sleep(1.0)
            self._dismiss_gm_popup_if_present()
            email_elem = self.wait_for_element(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().className("android.widget.EditText").instance(0)'),
                timeout=10
            )
            email_elem.send_keys(email)
            print("login: email escrito")
        except Exception as e:
            print(f"login: email por index(0) falló ({e}), reintentando tras dismiss")
            self._dismiss_gm_popup_if_present()
            time.sleep(0.5)
            self.type_by_edittext_index(0, email)
            print("login: email escrito (fallback)")

        time.sleep(1)
        self._save_page_source("DEBUG_login_after_email")
        self.take_screenshot("DEBUG_login_after_email")

        # --- CONTRASEÑA ---
        # type_by_edittext_index puede sufrir StaleElementReferenceException porque
        # el autofill picker refresca el árbol de vistas de FB tras el click().
        # Solución: click → dismiss picker → re-encontrar el elemento → send_keys.
        self._dismiss_gm_popup_if_present()
        try:
            pwd_elem = self.wait_for_element(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().className("android.widget.EditText").instance(1)'),
                timeout=5
            )
            pwd_elem.click()
            time.sleep(1.5)
            self._dismiss_gm_popup_if_present()
            # Re-encontrar para evitar StaleElementReferenceException
            pwd_elem = self.wait_for_element(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().className("android.widget.EditText").instance(1)'),
                timeout=5
            )
            pwd_elem.send_keys(password)
            print("login: contraseña escrita")
        except Exception as e:
            print(f"login: contraseña por index(1) falló ({e}), reintentando index(1) tras dismiss")
            self._dismiss_gm_popup_if_present()
            time.sleep(0.5)
            try:
                pwd_retry = self.wait_for_element(
                    (AppiumBy.ANDROID_UIAUTOMATOR,
                     'new UiSelector().className("android.widget.EditText").instance(1)'),
                    timeout=5
                )
                pwd_retry.send_keys(password)
                print("login: contraseña escrita en retry index(1)")
            except Exception as e2:
                print(f"login: retry index(1) falló ({e2}), usando type_by_edittext_index(1)")
                self.type_by_edittext_index(1, password)

        # Descartar GM que pudo aparecer al enfocar el campo contraseña
        time.sleep(1.5)
        self._dismiss_gm_popup_if_present()
        # Cerrar teclado con hide_keyboard() solamente — NO usar driver.back() porque
        # si el formulario fue apilado sobre el selector de cuentas, BACK lo descarta.
        try:
            self.driver.hide_keyboard()
            time.sleep(0.8)
        except Exception:
            pass
        # Descartar GM una vez más tras cerrar el teclado; luego diagnosticar
        time.sleep(1.5)
        self._dismiss_gm_popup_if_present()

        self._save_page_source("DEBUG_pre_tap_login")
        self.take_screenshot("DEBUG_pre_tap_login")

        self._try_tap_login()

    def _dismiss_gm_popup_if_present(self):
        """
        Cierra el Google Password Manager en cualquiera de sus dos variantes:
        - Bottom sheet completo: texto 'Administrador de contraseñas de Google'
        - Autofill dropdown inline: resource-id 'android:id/autofill_dataset_picker'
          (este picker oculta los EditText de FB para UiAutomator2; se cierra con BACK)
        """
        # Variante 1: bottom sheet completo
        if self.is_text_visible("Administrador de contraseñas de Google", timeout=2):
            print("login: GM bottom sheet detectado, cerrando con 'Cerrar'...")
            try:
                self.tap_by_exact_description("Cerrar")
                time.sleep(1)
                print("login: GM bottom sheet cerrado")
            except Exception:
                pass
            return

        # Variante 2: autofill dataset picker (dropdown inline)
        # NO usar BACK: navega hacia atrás en el historial de FB y abandona el form.
        # Usar tap fuera del picker (área del logo de FB, y≈600) para descartarlo.
        try:
            self.wait_for_element(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().resourceId("android:id/autofill_dataset_picker")'),
                timeout=2
            )
            print("login: autofill picker detectado, cerrando con tap neutro...")
            self.driver.tap([(540, 200)])  # cabecera de FB, fuera del picker y lejos de los campos
            time.sleep(0.8)
            print("login: autofill picker cerrado")
        except Exception:
            pass

    def login_empty_fields(self):
        self.dismiss_keyboard()
        time.sleep(1)
        self._try_tap_login()

    # ==========================================================
    # BOTÓN INICIAR SESIÓN
    # ==========================================================

    def _try_tap_login(self):
        """
        Intenta presionar el botón de Iniciar sesión usando varias estrategias.
        Según page_source.xml, el botón es android.widget.Button con
        content-desc="Iniciar sesión" (text está vacío).
        """

        # Prioridad: content-desc exacto → contains → text como fallback
        locators = [
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.Button")'
                f'.description("{self.LOGIN_BUTTON_DESC}")'
            ),
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.Button")'
                f'.descriptionContains("{self.LOGIN_BUTTON_DESC}")'
            ),
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().descriptionContains("{self.LOGIN_BUTTON_DESC}")'
            ),
            (
                AppiumBy.XPATH,
                f'//android.widget.Button[@content-desc="{self.LOGIN_BUTTON_DESC}"]'
            ),
            (
                AppiumBy.XPATH,
                f'//android.widget.Button[contains(@content-desc, "{self.LOGIN_BUTTON_DESC}")]'
            ),
            (
                AppiumBy.XPATH,
                f'//*[@clickable="true" and @content-desc="{self.LOGIN_BUTTON_DESC}"]'
            ),
            (
                AppiumBy.XPATH,
                f'//*[@clickable="true" and contains(@content-desc, "{self.LOGIN_BUTTON_DESC}")]'
            ),
            # Fallback por texto (por si una versión futura lo expone)
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{self.LOGIN_BUTTON_DESC}")'
            ),
            (
                AppiumBy.XPATH,
                f'//*[contains(@text, "{self.LOGIN_BUTTON_DESC}")]'
            ),
        ]

        last_error = None

        for locator in locators:
            try:
                element = self.wait_for_clickable(locator, timeout=5)

                if element.is_displayed() and element.is_enabled():
                    element.click()
                    return True

            except Exception as error:
                last_error = error

        print("\nNo se pudo presionar el botón con los localizadores normales.")
        self.print_button_candidates("Iniciar")

        raise Exception(
            f"No se pudo encontrar o presionar el botón '{self.LOGIN_BUTTON_DESC}'. "
            f"Último error: {last_error}"
        )

    # ==========================================================
    # RECUPERACIÓN DE CONTRASEÑA
    # ==========================================================

    def go_to_recovery(self):
        """
        Navega a la pantalla de recuperación de contraseña.
        Intenta múltiples variantes del texto/descripción y hace scroll si es necesario.
        """
        candidates = [
            lambda: self.tap_by_exact_description(self.FORGOT_PASSWORD_DESC),
            lambda: self.tap_by_description_contains("Olvidaste tu contraseña"),
            lambda: self.tap_by_text("Olvidaste tu contraseña"),
            lambda: self.tap_by_text("olvidaste"),
            lambda: self.tap_by_text("contraseña"),
        ]

        for attempt in candidates:
            try:
                attempt()
                return
            except Exception:
                continue

        # Intentar scroll hacia abajo y buscar de nuevo
        try:
            self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector().scrollable(true)).scrollForward()'
            )
            time.sleep(1)
        except Exception:
            pass

        for attempt in candidates:
            try:
                attempt()
                return
            except Exception:
                continue

        raise Exception("No se pudo navegar a la recuperación de contraseña")

    def tap_create_account(self):
        """
        Presiona el botón 'Crear cuenta nueva'.
        Según page_source.xml: android.widget.Button con
        content-desc="Crear cuenta nueva"
        """
        try:
            self.tap_by_exact_description(self.CREATE_ACCOUNT_BUTTON_DESC)
        except Exception:
            self.tap_by_description_contains("Crear cuenta")

    # ==========================================================
    # LOGOUT
    # ==========================================================

    def logout(self):
        # Paso 0: asegurar que Facebook está en primer plano
        fb_pkg = "com.facebook.katana"
        try:
            current_pkg = self.driver.current_package or ""
            if fb_pkg not in current_pkg:
                self.driver.activate_app(fb_pkg)
                time.sleep(2)
        except Exception:
            pass

        # Paso 1: abrir el menú de navegación (≡ en barra inferior o pestaña Perfil)
        # En versiones recientes de FB, la pestaña ≡ del bottom nav lleva directo
        # al menú donde se puede acceder a "Cerrar sesión". Intentamos primero esta
        # vía, y si no funciona, usamos el flujo clásico vía Perfil.
        menu_open = False

        # Intento A: tap en la pestaña Menú del bottom nav (≡)
        for desc in ("Menú, pestaña", "Menú"):
            try:
                self.tap_by_description_contains(desc, timeout=4)
                time.sleep(2)
                if (self.is_text_visible("Cerrar sesión", timeout=3)
                        or self.is_text_visible("Configuración y privacidad", timeout=3)
                        or self.is_text_visible("Configuración", timeout=2)):
                    menu_open = True
                    break
            except Exception:
                continue

        if not menu_open:
            # Intento B: ir a Perfil → buscar botón Menú en esa pantalla
            try:
                self.tap_by_description_contains("Perfil, pestaña", timeout=5)
                time.sleep(2)
            except Exception:
                try:
                    self.tap_by_description_contains("Ir al perfil", timeout=3)
                    time.sleep(2)
                except Exception:
                    pass

            # Scroll hacia arriba para revelar botones de la cabecera
            try:
                self.driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiScrollable(new UiSelector().scrollable(true)).scrollBackward()'
                )
                time.sleep(0.5)
            except Exception:
                pass

            # Tocar el botón de menú en la página de perfil (≡ o ⋮)
            for tap_fn, args in [
                (self.tap_by_exact_description, ("Menú",)),
                (self.tap_by_description_contains, ("Menú",)),
                (self.tap_by_description_contains, ("Más opciones",)),
                (self.tap_by_description_contains, ("opciones",)),
            ]:
                try:
                    tap_fn(*args, timeout=5)
                    menu_open = True
                    break
                except Exception:
                    continue

            if not menu_open:
                raise Exception(
                    "No se pudo abrir el menú de navegación para hacer logout. "
                    "Verifica que la pestaña Menú (≡) o el botón Menú del perfil existen."
                )

        time.sleep(1.5)

        # Paso 2: scroll a "Cerrar sesión" y tocarlo
        self.scroll_to_text("Cerrar sesión")
        time.sleep(0.5)
        self.tap_by_text("Cerrar sesión")

        # Paso 3: manejar la secuencia de diálogos post-logout
        # FB muestra primero "¿Guardar tu información?" y después "¿Salir de tu cuenta?"
        time.sleep(2)

        # Fase A: "¿Guardar tu información de inicio de sesión?" → AHORA NO
        for _ in range(12):
            if self.is_text_visible("Guardar tu informaci", timeout=1):
                for locator in [
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("AHORA NO")'),
                    (AppiumBy.XPATH, '//*[@text="AHORA NO"]'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Ahora no")'),
                    (AppiumBy.XPATH, '//*[@text="Ahora no"]'),
                ]:
                    try:
                        btn = self.wait_for_element(locator, timeout=3)
                        btn.click()
                        time.sleep(1.5)
                        break
                    except Exception:
                        continue
                break
            if self.is_text_visible("Salir de tu cuenta", timeout=1):
                break
            time.sleep(1)

        time.sleep(1)

        # Fase B: "¿Salir de tu cuenta?" → SALIR
        salir_done = False
        for _ in range(15):
            if self.is_text_visible("Salir de tu cuenta", timeout=1):
                for locator in [
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("SALIR")'),
                    (AppiumBy.XPATH, '//*[@text="SALIR"]'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("SALIR")'),
                ]:
                    try:
                        btn = self.wait_for_element(locator, timeout=3)
                        btn.click()
                        time.sleep(2)
                        if not self.is_text_visible("Salir de tu cuenta", timeout=2):
                            salir_done = True
                            break
                    except Exception:
                        continue
                if salir_done:
                    break
                time.sleep(1)
            else:
                time.sleep(1)

        return True

    # ==========================================================
    # VALIDACIÓN DE LOGIN
    # ==========================================================

    def is_logged_in(self):
        # Usar is_text_visible (basado en @text) que es seguro frente a Chrome y otras apps.
        # Evitar is_description_visible("Menú") porque descriptionContains("Menú")
        # hace falso positivo con el botón "Menú principal" de Chrome.

        # Indicadores de pantalla principal (feed) — texto visible en la barra inferior
        if (self.is_text_visible("Inicio")
                or self.is_text_visible("Historias")
                or self.is_description_visible("Inicio")
                or self.is_description_visible("Historias")):
            return True
        # Indicadores de Messenger / bandeja de chats
        if (self.is_text_visible("Chats")
                or self.is_text_visible("Bandeja de entrada")
                or self.is_description_visible("Mensajería")
                or self.is_description_visible("Chats")):
            return True
        # Indicadores dentro de una conversación abierta
        if (self.is_text_visible("Aa")
                or self.is_description_visible("Aa")
                or self.is_text_visible("Mensaje...")
                or self.is_description_visible("Mensaje...")):
            return True
        # Indicadores visibles en Reels fullscreen (texto "Reels" en la cabecera)
        # o en el feed (botón "Ir al perfil" en el área de creación de publicaciones)
        if (self.is_text_visible("Reels")
                or self.is_description_visible("Ir al perfil")
                or self.is_description_visible("Perfil, pestaña")
                or self.is_description_visible("Reels, pestaña")):
            return True
        return False

    # ==========================================================
    # DEBUG ESPECÍFICO DEL LOGIN
    # ==========================================================

    def debug_login_screen(self):
        self.print_input_candidates()
        self.print_button_candidates("Iniciar")
        self.print_button_candidates("Olvidaste")
        self.print_button_candidates("Crear")