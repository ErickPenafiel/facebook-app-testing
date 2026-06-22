import os
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class BasePageWeb:
    FB_BASE = "https://m.facebook.com"
    MESSENGER_BASE = "https://m.facebook.com/messages"

    def __init__(self, driver):
        self.driver = driver

    # ------------------------------------------------------------------
    # WAITS
    # ------------------------------------------------------------------

    def wait_for_element(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_clickable(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_for_url_contains(self, fragment, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.url_contains(fragment)
        )

    # ------------------------------------------------------------------
    # VISIBILITY CHECKS
    # ------------------------------------------------------------------

    def is_element_visible(self, locator, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except Exception:
            return False

    def is_text_visible(self, text, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'//*[contains(text(),"{text}")]')
                )
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # INTERACTIONS
    # ------------------------------------------------------------------

    def safe_click(self, locator, timeout=10):
        try:
            el = self.wait_for_clickable(locator, timeout)
            self.driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False

    def type_into(self, locator, value, timeout=10, clear=True):
        el = self.wait_for_clickable(locator, timeout)
        if clear:
            el.clear()
        el.send_keys(value)
        return el

    def _react_trigger(self, element):
        """Fire input+change events so React's controlled-input state updates."""
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            element,
        )

    def react_set_value(self, element, value):
        """
        Set an input value in a way React's controlled-input state reliably picks up.
        Uses the native HTMLInputElement property setter (not the React-overridden one),
        then dispatches an input event — the standard recipe for React 16-19.
        """
        self.driver.execute_script(
            """
            var nativeSet = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            nativeSet.call(arguments[0], arguments[1]);
            arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """,
            element,
            value,
        )

    # ------------------------------------------------------------------
    # SCROLL
    # ------------------------------------------------------------------

    def scroll_down(self, pixels=500):
        self.driver.execute_script(f"window.scrollBy(0, {pixels});")
        time.sleep(0.5)

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    # ------------------------------------------------------------------
    # NETWORK EMULATION (CDP)
    # ------------------------------------------------------------------

    def set_offline(self):
        self.driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": True,
            "latency": 0,
            "downloadThroughput": 0,
            "uploadThroughput": 0,
        })

    def set_online(self):
        self.driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": False,
            "latency": 0,
            "downloadThroughput": -1,
            "uploadThroughput": -1,
        })

    # ------------------------------------------------------------------
    # SCREENSHOT
    # ------------------------------------------------------------------

    @staticmethod
    def _screenshots_dir(name):
        if name.startswith("TC_AUTH_"):
            subdir = os.path.join("reports", "screenshots_web", "auth")
        elif name.startswith("TC_FB_MSG_"):
            subdir = os.path.join("reports", "screenshots_web", "messaging")
        elif name.startswith("TC_FB_NOT_"):
            subdir = os.path.join("reports", "screenshots_web", "notifications")
        else:
            subdir = os.path.join("reports", "screenshots_web")
        os.makedirs(subdir, exist_ok=True)
        return subdir

    def take_screenshot(self, name):
        screenshots_dir = self._screenshots_dir(name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(screenshots_dir, f"{name}_{timestamp}.png")
        try:
            self.driver.save_screenshot(file_path)
            print(f"Screenshot web: {file_path}")
        except Exception as e:
            print(f"Screenshot falló: {e}")
            return None
        return file_path
