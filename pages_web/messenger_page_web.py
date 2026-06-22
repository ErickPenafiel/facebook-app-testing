import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages_web.base_page_web import BasePageWeb

MESSAGES_URL = "https://m.facebook.com/messages/"

STATUS_TEXTS = ["Enviado", "Entregado", "Visto", "Sent", "Delivered", "Seen", "Read"]
PENDING_TEXTS = [
    "Pendiente", "Error", "No enviado", "Reintentando",
    "Sin conexión", "Reintentar", "Fallido", "No se pudo enviar",
    "error", "failed", "pending",
]


class MessengerPageWeb(BasePageWeb):

    # ------------------------------------------------------------------
    # NAVEGACIÓN
    # ------------------------------------------------------------------

    def is_messenger_available_on_web(self, timeout=5):
        """
        Returns False when Facebook shows the 'Chats on mobile browsers are
        not available' gate page — meaning Messenger has been disabled for this
        account on the mobile web browser.
        """
        BLOCKED_TEXTS = [
            "not available",
            "no disponible",
            "Go to Messenger",
            "Ir a Messenger",
            "Use Messenger to keep chatting",
            "Usa Messenger para seguir chateando",
        ]
        for text in BLOCKED_TEXTS:
            if self.is_element_visible(
                (By.XPATH, f'//*[contains(text(),"{text}")]'), timeout=timeout // len(BLOCKED_TEXTS) + 1
            ):
                return False
        return True

    def open_messenger(self):
        self.driver.get(MESSAGES_URL)
        time.sleep(3)
        return True

    def is_chat_list_visible(self, timeout=10):
        indicators = [
            (By.XPATH, '//*[contains(text(),"Chats")]'),
            (By.XPATH, '//*[contains(text(),"Mensajes")]'),
            (By.XPATH, '//*[contains(text(),"Bandeja")]'),
            (By.CSS_SELECTOR, 'a[href*="/messages/t/"]'),
            (By.XPATH, '//*[contains(@href,"/messages/t/")]'),
        ]
        for sel in indicators:
            if self.is_element_visible(sel, timeout=timeout // len(indicators) + 1):
                return True
        return "messages" in self.driver.current_url

    def wait_for_chat_list(self, timeout=15):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.is_chat_list_visible(timeout=2):
                return True
            time.sleep(2)
        return False

    # ------------------------------------------------------------------
    # BÚSQUEDA Y APERTURA DE CONVERSACIÓN
    # ------------------------------------------------------------------

    def search_conversation(self, contact_name):
        search_selectors = [
            (By.CSS_SELECTOR, 'input[placeholder*="Buscar"]'),
            (By.CSS_SELECTOR, 'input[placeholder*="Search"]'),
            (By.XPATH, '//input[contains(@placeholder,"Buscar")]'),
            (By.XPATH, '//*[@aria-label="Buscar en Messenger"]'),
            (By.XPATH, '//*[@aria-label="Buscar"]'),
            (By.CSS_SELECTOR, 'input[type="search"]'),
            (By.XPATH, '//input[@type="text"]'),
        ]
        for sel in search_selectors:
            try:
                el = self.wait_for_clickable(sel, timeout=5)
                el.clear()
                el.send_keys(contact_name)
                time.sleep(2)
                return True
            except Exception:
                continue

        # Fallback: search link
        search_link_selectors = [
            (By.XPATH, '//*[contains(text(),"Buscar")]'),
            (By.CSS_SELECTOR, 'a[href*="search"]'),
        ]
        for sel in search_link_selectors:
            if self.safe_click(sel, timeout=3):
                time.sleep(1)
                try:
                    active = self.driver.switch_to.active_element
                    active.send_keys(contact_name)
                    time.sleep(2)
                    return True
                except Exception:
                    pass

        return False

    def open_conversation(self, contact_name):
        selectors = [
            (By.XPATH, f'//a[contains(@href,"/messages/t/") and contains(.,"{contact_name}")]'),
            (By.XPATH, f'//*[contains(text(),"{contact_name}") and contains(@href,"/messages/")]'),
            (By.XPATH, f'//*[contains(text(),"{contact_name}")][@href]'),
            (By.XPATH, f'//*[contains(text(),"{contact_name}")]'),
        ]
        for sel in selectors:
            if self.safe_click(sel, timeout=5):
                time.sleep(2)
                return True
        return False

    def open_first_conversation(self):
        selectors = [
            (By.CSS_SELECTOR, 'a[href*="/messages/t/"]'),
            (By.XPATH, '//a[contains(@href,"/messages/t/")]'),
        ]
        for sel in selectors:
            try:
                items = self.driver.find_elements(*sel)
                if items:
                    name = items[0].text or "conversación"
                    items[0].click()
                    time.sleep(2)
                    return name.split("\n")[0]
            except Exception:
                continue
        return None

    def is_in_conversation(self, timeout=5):
        indicators = [
            (By.CSS_SELECTOR, '[name="body"]'),
            (By.CSS_SELECTOR, 'textarea'),
            (By.CSS_SELECTOR, '[contenteditable="true"]'),
            (By.XPATH, '//*[@placeholder="Aa"]'),
            (By.XPATH, '//*[contains(@placeholder,"mensaje")]'),
            (By.XPATH, '//*[contains(@aria-label,"mensaje")]'),
            (By.XPATH, '//*[contains(@aria-label,"Aa")]'),
        ]
        for sel in indicators:
            if self.is_element_visible(sel, timeout=timeout // len(indicators) + 1):
                return True
        return False

    # ------------------------------------------------------------------
    # ENVÍO DE MENSAJES
    # ------------------------------------------------------------------

    def send_message(self, text):
        composer_selectors = [
            (By.CSS_SELECTOR, '[name="body"]'),
            (By.CSS_SELECTOR, 'textarea'),
            (By.CSS_SELECTOR, '[contenteditable="true"]'),
            (By.XPATH, '//*[contains(@placeholder,"Aa")]'),
            (By.XPATH, '//*[contains(@placeholder,"mensaje")]'),
            (By.XPATH, '//*[@aria-label="Aa"]'),
        ]
        for sel in composer_selectors:
            try:
                el = self.wait_for_clickable(sel, timeout=5)
                el.click()
                time.sleep(0.3)
                el.send_keys(text)
                time.sleep(0.5)
                # Try Enter key first
                el.send_keys(Keys.RETURN)
                time.sleep(2)
                return True
            except Exception:
                continue

        # Fallback: type + click send button
        send_button_selectors = [
            (By.CSS_SELECTOR, '[type="submit"]'),
            (By.XPATH, '//*[contains(text(),"Enviar")][@type="submit"]'),
            (By.XPATH, '//*[@aria-label="Enviar"]'),
            (By.XPATH, '//*[@aria-label="Send"]'),
        ]
        for sel in send_button_selectors:
            if self.safe_click(sel, timeout=3):
                time.sleep(2)
                return True

        return False

    def is_message_visible(self, text, timeout=10):
        return self.is_text_visible(text, timeout=timeout)

    def has_received_messages_in_inbox(self):
        selectors = [
            (By.CSS_SELECTOR, 'a[href*="/messages/t/"]'),
            (By.XPATH, '//a[contains(@href,"/messages/t/")]'),
        ]
        for sel in selectors:
            try:
                items = self.driver.find_elements(*sel)
                if len(items) > 0:
                    return True
            except Exception:
                continue
        return False

    def get_last_received_message_text(self):
        try:
            messages = self.driver.find_elements(
                By.XPATH,
                '//*[contains(@class,"message") or contains(@data-testid,"message")]'
            )
            for el in reversed(messages):
                text = el.text.strip()
                if len(text) > 3:
                    return text
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # ESTADO DE ENTREGA
    # ------------------------------------------------------------------

    def get_message_status(self, timeout=15):
        conditions = " or ".join(
            f'contains(.,"{s}")' for s in STATUS_TEXTS
        )
        xpath = f'//*[{conditions}]'
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                el = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                for status in STATUS_TEXTS:
                    if status in (el.text or ""):
                        return status
                return "detected"
            except Exception:
                time.sleep(1)

        # Fallback: check aria-label for status indicators
        aria_selectors = [
            (By.XPATH, '//*[contains(@aria-label,"Enviado")]'),
            (By.XPATH, '//*[contains(@aria-label,"Entregado")]'),
            (By.XPATH, '//*[contains(@aria-label,"Visto")]'),
            (By.XPATH, '//*[contains(@aria-label,"Sent")]'),
            (By.XPATH, '//*[contains(@aria-label,"Delivered")]'),
            (By.XPATH, '//*[contains(@aria-label,"Seen")]'),
        ]
        for sel in aria_selectors:
            if self.is_element_visible(sel, timeout=2):
                return "detected"
        return None

    def is_pending_or_failed_visible(self, timeout=10):
        conditions = " or ".join(
            f'contains(.,"{t}")' for t in PENDING_TEXTS
        )
        xpath = f'//*[{conditions}]'
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                return True
            except Exception:
                time.sleep(1)
        return False
