import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class MessengerPage(BasePage):
    MESSENGER_TABS = [
        "Mensajería", "Messenger", "Mensajes", "Chats", "Bandeja de entrada",
    ]
    CHAT_LIST_INDICATORS = ["Chats", "Mensajes", "Bandeja de entrada"]
    SEARCH_HINTS = ["Campo de búsqueda", "Buscar", "Search", "Buscar en Messenger", "Buscar personas"]
    MESSAGE_INPUT_HINTS = ["Aa", "Mensaje...", "Escribe un mensaje", "Mensaje"]
    SEND_TEXTS = ["Enviar", "Send"]
    STATUS_TEXTS = [
        "Enviado", "Entregado", "Visto",
        "Delivered", "Seen", "Sent", "Read",
        "No se puede enviar",
    ]
    PENDING_ERROR_TEXTS = [
        "Pendiente", "Error", "No enviado", "Reintentando",
        "Sin conexión", "Reintentar", "Fallido",
    ]
    
    def _dismiss_chat_promo_modal(self):
        """
        Descarta el modal 'Más formas de chatear' que Facebook muestra
        cuando se accede a mensajería desde el feed. Toca 'Chatear en Facebook'.
        """
        if self.is_text_visible("Más formas de chatear", timeout=3):
            try:
                self.tap_by_text("Chatear en Facebook")
                time.sleep(2)
                return True
            except Exception:
                pass
        return False

    def open_messenger(self):
        """
        Abre la sección de Messenger / Mensajes desde cualquier pantalla.
        Una sola query XPATH combinada para reducir la carga sobre UiAutomator2.
        """
        conditions = " or ".join(
            f'@text="{t}" or @content-desc="{t}"' for t in self.MESSENGER_TABS
        )
        xpath = f'//*[{conditions}]'
        try:
            el = self.wait_for_element((AppiumBy.XPATH, xpath), timeout=8)
            rect = el.rect
            self.driver.tap([(rect["x"] + rect["width"] // 2, rect["y"] + rect["height"] // 2)])
            time.sleep(2)
            self._dismiss_chat_promo_modal()
            return True
        except Exception:
            return False

    def is_messenger_open(self):
        """Verifica que la bandeja de mensajes está visible (1 sola query XPATH)."""
        conditions = " or ".join(
            f'@text="{ind}" or @content-desc="{ind}"' for ind in self.CHAT_LIST_INDICATORS
        )
        xpath = f'//*[{conditions}]'
        try:
            self.wait_for_element((AppiumBy.XPATH, xpath), timeout=3)
            return True
        except Exception:
            return False

    def wait_for_chat_list(self, timeout=15):
        """Espera hasta que la bandeja de conversaciones cargue (intervalo 2s)."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.is_messenger_open():
                return True
            time.sleep(2)
        return False

    # ------------------------------------------------------------------ #
    # Búsqueda de conversación
    # ------------------------------------------------------------------ #

    def search_conversation(self, contact_name):
        """
        Abre el buscador de Messenger y escribe el nombre del contacto.
        """
        for hint in self.SEARCH_HINTS:
            try:
                if self.is_text_visible(hint, timeout=3):
                    self.tap_by_text(hint)
                    time.sleep(1)
                    break
            except Exception:
                continue
        else:
            for hint in self.SEARCH_HINTS:
                try:
                    if self.is_description_visible(hint, timeout=2):
                        self.tap_by_description_contains(hint)
                        time.sleep(1)
                        break
                except Exception:
                    continue

        # Escribir en el campo de búsqueda activo
        try:
            active = self.driver.switch_to.active_element
            active.send_keys(contact_name)
            time.sleep(2)
            return True
        except Exception:
            pass

        try:
            el = self.wait_for_element(
                (AppiumBy.XPATH, "//android.widget.EditText"), timeout=5
            )
            el.send_keys(contact_name)
            time.sleep(2)
            return True
        except Exception:
            pass

        return False

    def open_conversation(self, contact_name):
        """
        Abre una conversación tocando el nombre del contacto en resultados de búsqueda.
        Usa tap por coordenadas para evitar el problema de elementos no-clickables
        (en FB los nombres son ViewGroup hijos no-clickables dentro de un Button).
        """
        selectors = [
            # Primero: elemento clickable con descripción que contiene el nombre
            f'new UiSelector().clickable(true).descriptionContains("{contact_name}")',
            # Segundo: elemento clickable con texto que contiene el nombre
            f'new UiSelector().clickable(true).textContains("{contact_name}")',
            # Fallback: cualquier elemento con descripción (puede no ser clickable)
            f'new UiSelector().descriptionContains("{contact_name}")',
            # Fallback: cualquier elemento con texto
            f'new UiSelector().textContains("{contact_name}")',
        ]
        for selector in selectors:
            try:
                el = self.wait_for_element(
                    (AppiumBy.ANDROID_UIAUTOMATOR, selector), timeout=5
                )
                rect = el.rect
                x = rect["x"] + rect["width"] // 2
                y = rect["y"] + rect["height"] // 2
                self.driver.tap([(x, y)])
                time.sleep(2)
                return True
            except Exception:
                continue
        return False

    def open_first_conversation(self):
        """
        Abre la primera conversación visible en la bandeja.
        Útil para tests donde el contacto no importa.
        """
        conv_locators = [
            # Patrón real de messages_fb.xml: Buttons con "Leído" o "No leída" en content-desc
            (
                AppiumBy.XPATH,
                '//android.widget.Button[@clickable="true" and '
                '(contains(@content-desc, ", Leído") or contains(@content-desc, ", No leída"))]'
            ),
            (
                AppiumBy.XPATH,
                '//android.view.ViewGroup[@clickable="true"]'
                '[.//android.widget.ImageView]'
            ),
        ]
        for locator in conv_locators:
            try:
                el = self.wait_for_clickable(locator, timeout=5)
                desc = el.get_attribute("content-desc") or ""
                name = desc.split(",")[0].strip() if desc else None
                el.click()
                time.sleep(2)
                return name
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------ #
    # Envío de mensajes
    # ------------------------------------------------------------------ #

    def type_message(self, message):
        """
        Escribe *message* en el campo de texto de la conversación.
        """
        for hint in self.MESSAGE_INPUT_HINTS:
            try:
                el = self.wait_for_clickable(
                    (
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{hint}")'
                        '.className("android.widget.EditText")'
                    ),
                    timeout=3,
                )
                el.click()
                time.sleep(0.5)
                el.send_keys(message)
                return True
            except Exception:
                continue

        # Fallback: active element o primer EditText
        for locator in [
            None,  # active element
            (AppiumBy.XPATH, "//android.widget.EditText"),
        ]:
            try:
                el = (
                    self.driver.switch_to.active_element
                    if locator is None
                    else self.wait_for_clickable(locator, timeout=5)
                )
                el.send_keys(message)
                return True
            except Exception:
                continue

        return False

    def send_message(self, message):
        """
        Escribe y envía un mensaje.
        Filtra el botón "Enviar" por posición en pantalla (toolbar inferior)
        para no confundirlo con botones "Reintentar" de mensajes fallidos.
        """
        self.type_message(message)
        time.sleep(0.5)

        try:
            candidates = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().descriptionContains("Enviar")'
            )
            # Usar el candidato con mayor y (más cerca del fondo) — es el botón
            # del toolbar de composición. Con teclado visible el toolbar queda por
            # encima del teclado (y < 85% de pantalla), por eso no filtramos por
            # porcentaje fijo sino que elegimos el elemento más bajo de la lista.
            best = None
            best_y = -1
            for e in candidates:
                try:
                    r = e.rect
                    cy = r.get("y", 0) + r.get("height", 0) // 2
                    if cy > best_y:
                        best_y = cy
                        best = (r["x"] + r["width"] // 2, cy)
                except Exception:
                    continue
            if best is not None:
                self.driver.tap([best])
                time.sleep(2)
                return True
        except Exception:
            pass

        # Fallback: texto visible "Enviar"/"Send"
        for text in self.SEND_TEXTS:
            try:
                if self.is_text_visible(text, timeout=2):
                    self.tap_by_text(text)
                    time.sleep(2)
                    return True
            except Exception:
                continue

        return False

    def is_in_conversation(self, timeout=5):
        """
        Devuelve True si hay un campo de entrada visible (estamos en una chat).
        Una sola query XPATH combinada en vez de N checks individuales.
        """
        all_hints = self.MESSAGE_INPUT_HINTS + ["Escribe un mensaje...", "Responder", "Reply"]
        conditions = " or ".join(
            f'@text="{h}" or @content-desc="{h}"' for h in all_hints
        )
        xpath = f'//*[{conditions}]'
        try:
            self.wait_for_element((AppiumBy.XPATH, xpath), timeout=timeout)
            return True
        except Exception:
            return False

    def is_message_visible(self, message_text, timeout=10):
        """Verifica que el texto del mensaje es visible en la conversación."""
        return self.is_text_visible(message_text, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Estado de entrega
    # ------------------------------------------------------------------ #

    def get_message_status(self, timeout=10):
        """
        Espera y devuelve el estado de entrega del último mensaje.
        Una sola query XPATH combinada por iteración (evita las 240 queries
        que generaba el loop original de 8 textos × 2 métodos × N segundos).
        """
        conditions = " or ".join(
            f'contains(@text,"{s}") or contains(@content-desc,"{s}")'
            for s in self.STATUS_TEXTS
        )
        xpath = f'//*[{conditions}]'
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                el = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, xpath))
                )
                text = el.get_attribute("text") or ""
                desc = el.get_attribute("content-desc") or ""
                combined = text + " " + desc
                for status in self.STATUS_TEXTS:
                    if status in combined:
                        return status
                return (text or desc).strip() or "detected"
            except Exception:
                time.sleep(1)
        return None

    def is_status_visible(self, timeout=10):
        """Verifica que se muestra algún estado de entrega."""
        return self.get_message_status(timeout=timeout) is not None

    # ------------------------------------------------------------------ #
    # Estado de error / pendiente (sin conexión)
    # ------------------------------------------------------------------ #

    def is_pending_or_failed_visible(self, timeout=10):
        """
        Verifica que el mensaje muestra estado pendiente o error.
        Una sola query XPATH combinada por iteración.
        """
        conditions = " or ".join(
            f'contains(@text,"{t}") or contains(@content-desc,"{t}")'
            for t in self.PENDING_ERROR_TEXTS
        )
        xpath = f'//*[{conditions}]'
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, xpath))
                )
                return True
            except Exception:
                time.sleep(1)
        return False

    # ------------------------------------------------------------------ #
    # Mensajes recibidos
    # ------------------------------------------------------------------ #

    def has_received_messages_in_inbox(self):
        """
        Verifica si hay conversaciones con mensajes en la bandeja.
        Usado en TC_FB_MSG_003.
        """
        conv_locators = [
            # Patrón real de messages_fb.xml: Buttons con "Leído" o "No leída" en content-desc
            (
                AppiumBy.XPATH,
                '//android.widget.Button[@clickable="true" and '
                '(contains(@content-desc, ", Leído") or contains(@content-desc, ", No leída"))]'
            ),
            (
                AppiumBy.XPATH,
                '//android.view.ViewGroup[@clickable="true"]'
                '[.//android.widget.ImageView]'
            ),
        ]
        for locator in conv_locators:
            try:
                elements = self.driver.find_elements(*locator)
                if len(elements) > 0:
                    return True
            except Exception:
                continue
        return False

    def get_last_received_message_text(self):
        """
        Devuelve el texto del último mensaje visible en la conversación.
        Prueba TextView primero (Android estándar) y luego ViewGroup con
        atributo text (patrón que usa Facebook para burbujas de mensajes).
        """
        xpaths = [
            "//android.widget.TextView[@text!='']",
            "//android.view.ViewGroup[@text!='']",
        ]
        for xpath in xpaths:
            try:
                elements = self.driver.find_elements(AppiumBy.XPATH, xpath)
                for el in elements:
                    text = el.get_attribute("text")
                    if text and len(text) > 3:
                        return text
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------ #
    # Red / conectividad (TC_FB_MSG_005)
    # ------------------------------------------------------------------ #

    def disable_network(self):
        """
        Desactiva la conexión de red del dispositivo.
        Intenta con el API de Appium; si falla, activa modo avión.
        """
        try:
            # 0 = sin conexión (airplane mode off + sin datos)
            self.driver.set_network_connection(0)
            time.sleep(2)
            return True
        except Exception:
            pass

        # Fallback: modo avión = connection type 1
        try:
            self.driver.set_network_connection(1)
            time.sleep(2)
            return True
        except Exception:
            pass

        return False

    def enable_network(self):
        """
        Restaura la conexión de red (Wi-Fi + datos móviles).
        """
        try:
            # 6 = WiFi + datos habilitados
            self.driver.set_network_connection(6)
            time.sleep(3)
            return True
        except Exception:
            pass

        # Fallback: desactivar modo avión
        try:
            self.driver.set_network_connection(0)
            time.sleep(3)
            return True
        except Exception:
            pass

        return False

    # ------------------------------------------------------------------ #
    # Sincronización entre sesiones (TC_FB_MSG_007)
    # ------------------------------------------------------------------ #

    def restart_app(self, app_package):
        """
        Cierra y reabre la aplicación para simular una nueva sesión.
        """
        try:
            self.driver.terminate_app(app_package)
            time.sleep(2)
        except Exception:
            pass

        try:
            self.driver.activate_app(app_package)
            time.sleep(4)
            return True
        except Exception:
            pass

        return False
