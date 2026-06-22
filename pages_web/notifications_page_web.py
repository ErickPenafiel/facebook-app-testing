import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages_web.base_page_web import BasePageWeb

NOTIFICATIONS_URL = "https://m.facebook.com/notifications/"

SECTION_NAMES = ["Nuevas", "Hoy", "Anteriores", "Ayer", "Esta semana", "Este mes"]


class NotificationsPageWeb(BasePageWeb):

    # ------------------------------------------------------------------
    # NAVEGACIÓN
    # ------------------------------------------------------------------

    def open_notifications(self):
        self.driver.get(NOTIFICATIONS_URL)
        time.sleep(2)
        return True

    def is_panel_visible(self, timeout=10):
        indicators = [
            (By.XPATH, '//h3[contains(text(),"Nuevas") or contains(text(),"Hoy") or contains(text(),"Anteriores")]'),
            (By.XPATH, '//*[@role="heading"]'),
            (By.XPATH, '//*[contains(text(),"notificaci")]'),
            (By.CSS_SELECTOR, '[data-testid="notif_center"]'),
        ]
        for sel in indicators:
            if self.is_element_visible(sel, timeout=timeout // len(indicators) + 1):
                return True
        return "notification" in self.driver.current_url

    def wait_for_notifications_panel(self, timeout=15):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.is_panel_visible(timeout=2):
                return True
            time.sleep(2)
        return False

    # ------------------------------------------------------------------
    # ÍTEMS DE NOTIFICACIÓN
    # ------------------------------------------------------------------

    def _get_notification_links(self):
        selectors = [
            (By.XPATH, '//a[contains(@href,"/notification/")]'),
            (By.XPATH, '//a[contains(@href,"notif_id")]'),
            (By.XPATH, '//a[contains(@data-testid,"story-link")]'),
            (By.CSS_SELECTOR, 'a[data-testid="story-link"]'),
        ]
        for sel in selectors:
            try:
                items = self.driver.find_elements(*sel)
                if items:
                    return items
            except Exception:
                continue
        # Generic fallback: all clickable links in notification area
        try:
            return self.driver.find_elements(
                By.XPATH, '//a[@href and not(contains(@href,"javascript"))]'
            )
        except Exception:
            return []

    def has_notification_items(self):
        return len(self._get_notification_links()) > 0

    def total_notification_items(self):
        return len(self._get_notification_links())

    # ------------------------------------------------------------------
    # ESTADO LEÍDA / NO LEÍDA
    # ------------------------------------------------------------------

    def count_unread_notifications(self):
        selectors = [
            (By.XPATH, '//*[contains(@aria-label,"No leída")]'),
            (By.XPATH, '//*[contains(@class,"unread")]'),
            (By.XPATH, '//*[contains(@data-testid,"unread")]'),
        ]
        for sel in selectors:
            try:
                items = self.driver.find_elements(*sel)
                if items:
                    return len(items)
            except Exception:
                continue
        return 0

    def count_read_notifications(self):
        selectors = [
            (By.XPATH, '//*[contains(@aria-label,"Leída") and not(contains(@aria-label,"No leída"))]'),
            (By.XPATH, '//*[contains(@class,"read") and not(contains(@class,"unread"))]'),
        ]
        for sel in selectors:
            try:
                items = self.driver.find_elements(*sel)
                if items:
                    return len(items)
            except Exception:
                continue
        return 0

    # ------------------------------------------------------------------
    # SECCIONES
    # ------------------------------------------------------------------

    def get_visible_sections(self):
        try:
            headers = self.driver.find_elements(
                By.XPATH, '//h2 | //h3 | //*[@role="heading"]'
            )
            return [h.text.strip() for h in headers if h.text.strip() in SECTION_NAMES]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # CARGAR MÁS
    # ------------------------------------------------------------------

    def scroll_to_bottom_of_notifications(self):
        self.scroll_to_bottom()

    def has_load_more_button(self):
        selectors = [
            (By.XPATH, '//*[contains(text(),"Ver más")]'),
            (By.XPATH, '//*[contains(text(),"Ver notificaciones anteriores")]'),
            (By.XPATH, '//*[contains(text(),"See More")]'),
            (By.XPATH, '//*[contains(text(),"See more")]'),
        ]
        for sel in selectors:
            if self.is_element_visible(sel, timeout=2):
                return True
        return False

    def tap_load_more(self):
        selectors = [
            (By.XPATH, '//*[contains(text(),"Ver más")]'),
            (By.XPATH, '//*[contains(text(),"Ver notificaciones anteriores")]'),
            (By.XPATH, '//*[contains(text(),"See More")]'),
        ]
        for sel in selectors:
            if self.safe_click(sel, timeout=3):
                time.sleep(2)
                return True
        return False

    # ------------------------------------------------------------------
    # DETALLE DE NOTIFICACIÓN
    # ------------------------------------------------------------------

    def open_first_notification(self):
        items = self._get_notification_links()
        if not items:
            return None
        try:
            text = items[0].get_attribute("aria-label") or items[0].text or "notificación"
            self.driver.execute_script("arguments[0].click();", items[0])
            time.sleep(2)
            return text[:80]
        except Exception:
            return None

    def app_is_still_responsive(self):
        try:
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # MENÚ DE CONFIGURACIÓN
    # ------------------------------------------------------------------

    def has_manage_button_on_notifications(self):
        selectors = [
            (By.XPATH, '//*[@aria-label="Administrar configuración de la notificación"]'),
            (By.XPATH, '//*[contains(@aria-label,"configuración de la notificación")]'),
            (By.XPATH, '//*[contains(@aria-label,"notification settings")]'),
            (By.XPATH, '//*[contains(@title,"Administrar")]'),
        ]
        for sel in selectors:
            try:
                items = self.driver.find_elements(*sel)
                if items:
                    return True
            except Exception:
                continue
        return False

    def tap_manage_settings_first_notification(self):
        selectors = [
            (By.XPATH, '(//*[@aria-label="Administrar configuración de la notificación"])[1]'),
            (By.XPATH, '(//*[contains(@aria-label,"configuración de la notificación")])[1]'),
        ]
        for sel in selectors:
            if self.safe_click(sel, timeout=5):
                time.sleep(1)
                return True
        return False

    def notification_menu_appeared(self):
        selectors = [
            (By.XPATH, '//*[contains(text(),"Silenciar")]'),
            (By.XPATH, '//*[contains(text(),"Desactivar")]'),
            (By.XPATH, '//*[contains(text(),"Mute")]'),
            (By.XPATH, '//*[contains(text(),"Turn off")]'),
        ]
        for sel in selectors:
            if self.is_element_visible(sel, timeout=3):
                return True
        return False

    # ------------------------------------------------------------------
    # SOLICITUDES DE AMISTAD
    # ------------------------------------------------------------------

    def has_friend_request_notification(self):
        selectors = [
            (By.XPATH, '//*[contains(text(),"Confirmar")]'),
            (By.XPATH, '//*[contains(@aria-label,"Confirmar")]'),
            (By.XPATH, '//*[contains(text(),"Confirm")]'),
        ]
        for sel in selectors:
            if self.is_element_visible(sel, timeout=3):
                return True
        return False

    def get_friend_request_desc(self):
        try:
            btn = self.driver.find_element(
                By.XPATH, '//*[contains(text(),"Confirmar")]'
            )
            parent = btn.find_element(By.XPATH, '..')
            return parent.text[:60] if parent.text else "solicitud de amistad"
        except Exception:
            return "solicitud de amistad"

    def confirmar_button_enabled(self):
        try:
            btn = self.wait_for_element(
                (By.XPATH, '//*[contains(text(),"Confirmar")]'), timeout=3
            )
            return btn.is_enabled()
        except Exception:
            return False

    def eliminar_button_enabled(self):
        try:
            btn = self.wait_for_element(
                (By.XPATH, '//*[contains(text(),"Eliminar")]'), timeout=3
            )
            return btn.is_enabled()
        except Exception:
            return False

    def regular_notifications_have_no_action_buttons(self):
        confirm_visible = self.is_element_visible(
            (By.XPATH, '//*[contains(text(),"Confirmar")]'), timeout=2
        )
        return not confirm_visible

    # ------------------------------------------------------------------
    # MODO SIN CONEXIÓN
    # ------------------------------------------------------------------

    def is_offline_indicator_visible(self):
        selectors = [
            (By.XPATH, '//*[contains(text(),"sin conexión")]'),
            (By.XPATH, '//*[contains(text(),"offline")]'),
            (By.XPATH, '//*[contains(text(),"Sin conexión")]'),
            (By.XPATH, '//*[contains(text(),"Inténtalo de nuevo")]'),
            (By.XPATH, '//*[contains(text(),"no tienes conexión")]'),
            (By.XPATH, '//*[contains(text(),"conexión a Internet")]'),
        ]
        for sel in selectors:
            if self.is_element_visible(sel, timeout=2):
                return True
        return False
