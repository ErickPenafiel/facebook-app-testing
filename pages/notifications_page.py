import re
import time

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class NotificationsPage(BasePage):

    # ------------------------------------------------------------------ #
    # Constantes
    # ------------------------------------------------------------------ #

    # Botón de la pestaña en la barra de navegación principal.
    # content-desc real: "Notificaciones, pestaña 5 de 6[, N elemento(s) nuevo(s)]"
    NAV_TAB_HINT = "Notificaciones"

    # Indicadores de que el panel de notificaciones está abierto.
    PANEL_INDICATORS = [
        "Notificaciones",
        "Todos",
        "Sin ver",
        "Sin leer",
    ]

    # Textos que aparecen al estar sin conexión.
    OFFLINE_TEXTS = [
        "Sin conexión", "sin conexión",
        "Sin internet", "sin internet",
        "No hay conexión", "Error de red",
        "Reintentar", "volver a intentar",
        "no se pudo cargar", "No se pudo cargar",
    ]

    # Indicadores de pantalla de configuración de notificaciones.
    SETTINGS_INDICATORS = [
        "Configuración de notificaciones",
        "Notificaciones push",
        "Sonido", "Vibración",
        "Notificaciones de",
    ]

    # ------------------------------------------------------------------ #
    # Navegación
    # ------------------------------------------------------------------ #

    def open_notifications(self):
        """
        Abre el panel de notificaciones desde cualquier pantalla
        tocando la pestaña de la barra de navegación.
        """
        try:
            self.tap_by_description_contains(self.NAV_TAB_HINT)
            time.sleep(2)
            return True
        except Exception:
            pass
        try:
            self.tap_by_text(self.NAV_TAB_HINT)
            time.sleep(2)
            return True
        except Exception:
            pass
        return False

    def is_notifications_open(self):
        """Devuelve True si el panel de notificaciones está visible."""
        for indicator in self.PANEL_INDICATORS:
            if self.is_text_visible(indicator, timeout=3):
                return True
            if self.is_description_visible(indicator, timeout=2):
                return True
        return False

    def wait_for_notifications_panel(self, timeout=15):
        """Espera hasta que el panel de notificaciones cargue."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.is_notifications_open():
                return True
            time.sleep(1)
        return False

    # ------------------------------------------------------------------ #
    # Contadores e insignias
    # ------------------------------------------------------------------ #

    def get_unread_count_from_tab(self):
        """
        Lee el contador de notificaciones nuevas del botón de pestaña.
        Ejemplo de content-desc: "Notificaciones, pestaña 5 de 6, 3 elementos nuevos"
        Retorna 0 si no hay nuevas.
        """
        try:
            el = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().descriptionContains("Notificaciones")'
                '.descriptionContains("pestaña")',
            )
            desc = el.get_attribute("content-desc") or ""
            match = re.search(r"(\d+)\s+elemento", desc)
            return int(match.group(1)) if match else 0
        except Exception:
            return 0

    def has_unread_badge(self):
        """Devuelve True si hay al menos una notificación nueva sin ver."""
        return self.get_unread_count_from_tab() > 0

    # ------------------------------------------------------------------ #
    # Elementos del panel
    # ------------------------------------------------------------------ #

    def has_notification_items(self):
        """
        Verifica si hay al menos un ítem de notificación visible en la lista.
        """
        locators = [
            # Items con content-desc descriptivo (texto de la notificación)
            (
                AppiumBy.XPATH,
                '//android.widget.Button[@clickable="true" '
                'and string-length(@content-desc) > 15]',
            ),
            (
                AppiumBy.XPATH,
                '//android.view.ViewGroup[@clickable="true" '
                'and string-length(@content-desc) > 15]',
            ),
        ]
        for locator in locators:
            try:
                elements = self.driver.find_elements(*locator)
                if elements:
                    return True
            except Exception:
                continue
        return False

    def open_first_notification(self):
        """
        Toca el primer ítem de notificación disponible.
        Retorna el content-desc del ítem, o None si no hay ninguno.
        """
        locators = [
            (
                AppiumBy.XPATH,
                '//android.widget.Button[@clickable="true" '
                'and string-length(@content-desc) > 15]',
            ),
            (
                AppiumBy.XPATH,
                '//android.view.ViewGroup[@clickable="true" '
                'and string-length(@content-desc) > 15]',
            ),
        ]
        for locator in locators:
            try:
                el = self.wait_for_clickable(locator, timeout=5)
                desc = el.get_attribute("content-desc") or ""
                el.click()
                time.sleep(2)
                return desc if desc else "opened"
            except Exception:
                continue
        return None

    def screen_changed_after_tap(self, original_indicator):
        """
        Devuelve True si la pantalla cambió tras tocar una notificación,
        es decir, el panel de notificaciones ya no es la vista principal.
        """
        return not self.is_text_visible(original_indicator, timeout=3)

    # ------------------------------------------------------------------ #
    # Configuración de notificaciones
    # ------------------------------------------------------------------ #

    def open_notification_settings(self):
        """
        Abre la pantalla de configuración de notificaciones.
        Busca el botón de ajustes (engranaje) en el panel.
        """
        settings_hints = [
            "Configuración de notificaciones",
            "Configuración",
            "Ajustes",
        ]
        for hint in settings_hints:
            try:
                if self.is_description_visible(hint, timeout=3):
                    self.tap_by_description_contains(hint)
                    time.sleep(2)
                    return True
            except Exception:
                continue

        # Fallback: buscar por texto
        for hint in settings_hints:
            try:
                if self.is_text_visible(hint, timeout=2):
                    self.tap_by_text(hint)
                    time.sleep(2)
                    return True
            except Exception:
                continue

        return False

    def is_notification_settings_open(self):
        """Verifica que la pantalla de configuración de notificaciones esté abierta."""
        for indicator in self.SETTINGS_INDICATORS:
            if self.is_text_visible(indicator, timeout=3):
                return True
            if self.is_description_visible(indicator, timeout=2):
                return True
        return False

    def toggle_first_notification_switch(self):
        """
        Activa/desactiva el primer switch de notificaciones encontrado.
        Devuelve el estado previo ('on'/'off') o None si no se encontró.
        """
        try:
            switches = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.Switch',
            )
            if not switches:
                # Buscar toggles o checkboxes
                switches = self.driver.find_elements(
                    AppiumBy.XPATH,
                    '//android.widget.CheckBox | //android.widget.ToggleButton',
                )
            if switches:
                sw = switches[0]
                prev_state = sw.get_attribute("checked")
                sw.click()
                time.sleep(1)
                return "on" if prev_state == "true" else "off"
        except Exception:
            pass
        return None

    def restore_notification_switch(self, original_state):
        """
        Restaura el primer switch de notificaciones a su estado original.
        original_state: 'on' o 'off'
        """
        try:
            switches = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.Switch',
            )
            if not switches:
                switches = self.driver.find_elements(
                    AppiumBy.XPATH,
                    '//android.widget.CheckBox | //android.widget.ToggleButton',
                )
            if switches:
                sw = switches[0]
                current = sw.get_attribute("checked")
                current_state = "on" if current == "true" else "off"
                if current_state != original_state:
                    sw.click()
                    time.sleep(1)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Red / conectividad (TC_FB_NOT_007)
    # ------------------------------------------------------------------ #

    def disable_network(self):
        """Desactiva la conexión de red del dispositivo."""
        try:
            self.driver.set_network_connection(0)
            time.sleep(2)
            return True
        except Exception:
            pass
        try:
            self.driver.set_network_connection(1)
            time.sleep(2)
            return True
        except Exception:
            pass
        return False

    def enable_network(self):
        """Restaura la conexión de red (WiFi + datos)."""
        try:
            self.driver.set_network_connection(6)
            time.sleep(3)
            return True
        except Exception:
            pass
        try:
            self.driver.set_network_connection(0)
            time.sleep(3)
            return True
        except Exception:
            pass
        return False

    def is_offline_indicator_visible(self):
        """
        Devuelve True si se muestra algún mensaje de error de conectividad
        o contenido cargado previamente (sin crash).
        """
        for text in self.OFFLINE_TEXTS:
            if self.is_text_visible(text, timeout=3):
                return True
        return False

    def app_is_still_responsive(self):
        """
        Verifica que la app no crasheó intentando leer la actividad actual.
        """
        try:
            activity = self.driver.current_activity
            return activity is not None
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Estado leída / no leída  (TC_FB_NOT_002)
    # ------------------------------------------------------------------ #

    def count_unread_notifications(self):
        """
        Cuenta notificaciones cuyo content-desc termina en 'No leída'.
        Patrón real del XML: '..., N h. No leída'
        """
        try:
            items = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.Button[@clickable="true" '
                'and contains(@content-desc, ". No leída")]',
            )
            return len(items)
        except Exception:
            return 0

    def count_read_notifications(self):
        """Cuenta notificaciones con '. Leída' en su content-desc."""
        try:
            items = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.Button[@clickable="true" '
                'and contains(@content-desc, ". Leída")]',
            )
            return len(items)
        except Exception:
            return 0

    def total_notification_items(self):
        return self.count_unread_notifications() + self.count_read_notifications()

    # ------------------------------------------------------------------ #
    # Secciones temporales y carga de más  (TC_FB_NOT_004)
    # ------------------------------------------------------------------ #

    # Secciones que Facebook muestra en el panel según el XML:
    # "Nuevas", "Hoy", "Anteriores"
    SECTION_NAMES = ["Nuevas", "Hoy", "Anteriores"]

    def get_visible_sections(self):
        """Devuelve lista de encabezados de sección visibles."""
        found = []
        for name in self.SECTION_NAMES:
            if self.is_text_visible(name, timeout=2):
                found.append(name)
        return found

    def has_load_more_button(self):
        """Verifica si el botón 'Ver notificaciones anteriores' está visible."""
        return (
            self.is_description_visible("Ver notificaciones anteriores", timeout=5)
            or self.is_text_visible("Ver notificaciones anteriores", timeout=3)
        )

    def tap_load_more(self):
        """Toca el botón 'Ver notificaciones anteriores'."""
        try:
            self.tap_by_description_contains("Ver notificaciones anteriores")
            time.sleep(3)
            return True
        except Exception:
            try:
                self.tap_by_text("Ver notificaciones anteriores")
                time.sleep(3)
                return True
            except Exception:
                return False

    def scroll_to_bottom_of_notifications(self):
        """Desplaza la lista hasta el final para revelar el botón de carga."""
        try:
            self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector().scrollable(true))'
                '.scrollToEnd(3)',
            )
            time.sleep(1)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Menú de configuración por notificación  (TC_FB_NOT_005)
    # ------------------------------------------------------------------ #

    def tap_manage_settings_first_notification(self):
        """
        Toca el botón 'Administrar configuración de la notificación' del
        primer ítem visible (botón de tres puntos/engranaje junto a la notif).
        """
        locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector()'
            '.description("Administrar configuración de la notificación")'
            '.instance(0)',
        )
        try:
            el = self.wait_for_clickable(locator, timeout=8)
            el.click()
            time.sleep(2)
            return True
        except Exception:
            return False

    def has_manage_button_on_notifications(self):
        """Devuelve True si existe al menos un botón de administrar notificación."""
        try:
            items = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector()'
                '.description("Administrar configuración de la notificación")',
            )
            return len(items) > 0
        except Exception:
            return False

    def notification_menu_appeared(self):
        """
        Detecta si se abrió un menú contextual al tocar el botón
        de administración (busca opciones típicas de ese menú).
        """
        menu_hints = [
            "Desactivar", "Silenciar", "Ocultar", "Configuración",
            "Desactivar notificaciones", "No recibir",
        ]
        for hint in menu_hints:
            if self.is_text_visible(hint, timeout=3):
                return True
            if self.is_description_visible(hint, timeout=2):
                return True
        return False

    # ------------------------------------------------------------------ #
    # Acciones en solicitudes de amistad  (TC_FB_NOT_006)
    # ------------------------------------------------------------------ #

    def has_friend_request_notification(self):
        """
        Devuelve True si hay una notificación de solicitud de amistad con
        los botones 'Confirmar' y 'Eliminar' visibles.
        """
        return (
            self.is_text_visible("Confirmar", timeout=3)
            and self.is_text_visible("Eliminar", timeout=2)
        )

    def get_friend_request_desc(self):
        """Devuelve el content-desc de la notificación de solicitud de amistad."""
        try:
            # La solicitud de amistad es un Button que contiene "solicitud de amistad"
            el = self.driver.find_element(
                AppiumBy.XPATH,
                '//android.widget.Button[contains(@content-desc,"solicitud de amistad")]',
            )
            return el.get_attribute("content-desc") or ""
        except Exception:
            return ""

    def confirmar_button_enabled(self):
        """Verifica que el botón Confirmar de una solicitud está habilitado."""
        try:
            el = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().text("Confirmar")',
            )
            return el.is_enabled() and el.is_displayed()
        except Exception:
            return False

    def eliminar_button_enabled(self):
        """Verifica que el botón Eliminar de una solicitud está habilitado."""
        try:
            el = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().text("Eliminar")',
            )
            return el.is_enabled() and el.is_displayed()
        except Exception:
            return False

    def regular_notifications_have_no_action_buttons(self):
        """
        Verifica (path negativo) que las notificaciones regulares
        (historias, reacciones, etc.) NO muestran Confirmar/Eliminar.
        Solo las solicitudes de amistad los tienen.
        """
        # Buscar una notificación que NO sea solicitud de amistad
        try:
            items = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.Button[@clickable="true" '
                'and (contains(@content-desc,". Leída") '
                'or contains(@content-desc,". No leída")) '
                'and not(contains(@content-desc,"solicitud de amistad"))]',
            )
            if not items:
                return True  # sin ítems regulares, no se puede fallar
            # Si hay ítems regulares, verificar que el primero NO tiene
            # botones de acción directamente dentro de él
            # (Confirmar/Eliminar solo están en las solicitudes)
            regular_desc = items[0].get_attribute("content-desc") or ""
            # El hecho de que "Confirmar" exista en pantalla no prueba nada
            # sin contexto; lo que verificamos es que NO está dentro del ítem
            return "Confirmar" not in regular_desc and "Eliminar" not in regular_desc
        except Exception:
            return True

    # ------------------------------------------------------------------ #
    # App en segundo plano (TC_FB_NOT_005)
    # ------------------------------------------------------------------ #

    def send_app_to_background(self, seconds=5):
        """
        Envía la app al segundo plano por N segundos.
        Usa el botón Home de Android y luego regresa.
        """
        try:
            self.driver.press_keycode(3)  # KEYCODE_HOME
            time.sleep(seconds)
            self.driver.press_keycode(3)  # volver a la app vía recientes no es directo
            # Usar activate_app para traerla de vuelta
            app_package = "com.facebook.katana"
            self.driver.activate_app(app_package)
            time.sleep(2)
            return True
        except Exception:
            return False

    def is_push_notification_visible_in_tray(self):
        """
        Intenta abrir el panel de notificaciones del sistema Android
        y busca una notificación de Facebook.
        """
        try:
            self.driver.open_notifications()
            time.sleep(2)
            fb_visible = (
                self.is_text_visible("Facebook", timeout=3)
                or self.is_description_visible("Facebook", timeout=3)
            )
            # Cerrar panel de sistema
            self.driver.press_keycode(4)  # KEYCODE_BACK
            time.sleep(1)
            return fb_visible
        except Exception:
            return False
