import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from pages_web.base_page_web import BasePageWeb

# mbasic.facebook.com = versión HTML pura sin React/JS, ideal para automatización.
# Los cookies generados son válidos en m.facebook.com (mismo dominio .facebook.com).
MBASIC_LOGIN = "https://mbasic.facebook.com/login"
MBASIC_HOME  = "https://mbasic.facebook.com"
M_HOME       = "https://m.facebook.com"


class LoginPageWeb(BasePageWeb):
    EMAIL_INPUT    = (By.CSS_SELECTOR, 'input[name="email"]')
    PASSWORD_INPUT = (By.CSS_SELECTOR, 'input[name="pass"]')

    # Ordered list: try each until one is found and clicked
    SUBMIT_SELECTORS = [
        (By.CSS_SELECTOR, 'button[type="submit"]'),          # modern mbasic / m.fb
        (By.CSS_SELECTOR, 'input[name="login"]'),            # old mbasic
        (By.CSS_SELECTOR, '[data-testid="royal_login_button"]'),
        (By.XPATH, '//button[contains(.,"Iniciar")]'),
        (By.XPATH, '//button[contains(.,"Log In")]'),
        (By.XPATH, '//*[@role="button" and contains(.,"Iniciar")]'),
        (By.XPATH, '//*[@role="button" and contains(.,"Log In")]'),
    ]

    FEED_LOCATORS = [
        (By.XPATH, '//*[contains(text(),"¿Qué estás pensando")]'),
        (By.XPATH, '//*[contains(text(),"Noticias")]'),
        (By.XPATH, '//*[contains(text(),"Inicio")]'),
        (By.XPATH, '//*[contains(@href,"/home.php")]'),
        (By.XPATH, '//*[@aria-label="Inicio"]'),
    ]

    ERROR_LOCATORS_MBASIC = [
        (By.CSS_SELECTOR, "#login_error"),
        (By.CSS_SELECTOR, "#error_box"),
        (By.XPATH, '//*[contains(text(),"incorrecta")]'),
        (By.XPATH, '//*[contains(text(),"no encontramos")]'),
        (By.XPATH, '//*[contains(text(),"No encontramos")]'),
        (By.XPATH, '//*[contains(text(),"incorrecto")]'),
        (By.XPATH, '//*[contains(text(),"Inténtalo de nuevo")]'),
    ]

    # ------------------------------------------------------------------
    # LOGIN (vía mbasic — HTML puro, sin React)
    # ------------------------------------------------------------------

    def login(self, email, password):
        self.driver.get(MBASIC_LOGIN)
        time.sleep(2)

        email_field = self.wait_for_element(self.EMAIL_INPUT, timeout=15)
        self.react_set_value(email_field, email)
        time.sleep(0.8)

        pwd_field = self.wait_for_element(self.PASSWORD_INPUT, timeout=10)
        self.react_set_value(pwd_field, password)
        time.sleep(0.8)

        # Try each submit selector; ActionChains produces a realistic mouse click
        clicked = False
        for sel in self.SUBMIT_SELECTORS:
            try:
                btn = self.wait_for_clickable(sel, timeout=3)
                ActionChains(self.driver).move_to_element(btn).pause(0.3).click().perform()
                clicked = True
                print(f"[login] clicked via {sel}")
                break
            except Exception:
                continue

        if not clicked:
            print("[login] no button found — trying Keys.RETURN")
            pwd_field.send_keys(Keys.RETURN)

        # Wait up to 10s for Facebook to respond (passkey prompt or redirect)
        for _ in range(10):
            time.sleep(1)
            if self.is_on_2fa_screen() or self.is_logged_in():
                break

        # Handle passkey prompt if Facebook raised it
        self._handle_passkey_prompt(password)

        time.sleep(3)
        url = self.driver.current_url
        print(f"[login] URL after full flow: {url}")

        # Navigate to m.facebook.com when authenticated on mbasic
        # (includes post-auth pages like save-device, but not 2FA screens)
        if "mbasic" in url and not self.is_on_2fa_screen() and self.is_logged_in():
            self.driver.get(M_HOME)
            time.sleep(3)

    def _handle_passkey_prompt(self, password):
        """
        Detect the passkey/identity prompt and click 'Usar otro método' to advance
        to the method-selection screen, then STOP. Callers decide what to do next
        (TC_AUTH_001 checks is_on_2fa_screen(); ensure_logged_in waits for approval).
        """
        PASSKEY_TEXTS = [
            "Confirma tu identidad",
            "desbloqueas tu dispositivo",
            "Confirm your identity",
        ]
        detected = False
        for text in PASSKEY_TEXTS:
            if self.is_element_visible(
                (By.XPATH, f'//*[contains(text(),"{text}")]'), timeout=3
            ):
                detected = True
                print(f"[login] passkey screen detected: '{text}'")
                break

        if not detected:
            return False

        self.take_screenshot("LOGIN_passkey_prompt")

        OTHER_METHOD_XPATHS = [
            '//*[contains(text(),"Usar otro método")]',
            '//*[contains(text(),"otro método")]',
            '//*[contains(text(),"Use another method")]',
            '//*[contains(text(),"otra forma")]',
        ]
        for xpath in OTHER_METHOD_XPATHS:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                try:
                    el.click()
                except Exception:
                    ActionChains(self.driver).move_to_element(el).click().perform()
                print("[login] clicked 'Usar otro método'")
                break
            except Exception:
                continue

        time.sleep(2)
        self.take_screenshot("LOGIN_after_otro_metodo")

        # If a password field appears directly after otro_método, re-submit
        if self.is_element_visible(self.PASSWORD_INPUT, timeout=3):
            pwd = self.wait_for_element(self.PASSWORD_INPUT, timeout=5)
            self.react_set_value(pwd, password)
            time.sleep(0.5)
            for sel in self.SUBMIT_SELECTORS:
                try:
                    btn = self.wait_for_clickable(sel, timeout=3)
                    btn.click()
                    print("[login] re-submitted via password field after otro_método")
                    break
                except Exception:
                    continue

        # STOP HERE — leave the method-selection (or waiting) screen visible.
        # ensure_logged_in() will select a method and wait for approval.
        return True

    def login_empty_fields(self):
        self.driver.get(MBASIC_LOGIN)
        time.sleep(2)
        try:
            btn = self.wait_for_clickable(
                (By.CSS_SELECTOR, 'button[type="submit"]'), timeout=3
            )
            btn.click()
        except Exception:
            try:
                btn = self.wait_for_clickable(
                    (By.XPATH, '//*[@role="button" and contains(.,"Iniciar")]'),
                    timeout=3,
                )
                btn.click()
            except Exception:
                pass
        time.sleep(2)

    # ------------------------------------------------------------------
    # STATE DETECTION
    # ------------------------------------------------------------------

    def is_on_2fa_screen(self):
        """
        Returns True if Facebook is showing a 2FA/passkey/two-step-verification screen.
        Detects by URL first (reliable), then by visible text indicators.
        """
        url = self.driver.current_url
        if "two_step_verification" in url or "checkpoint" in url:
            return True
        INDICATORS = [
            "Confirma tu identidad",
            "Elige un método para confirmar",
            "desbloqueas tu dispositivo",
            "métodos de confirmación",
            "Llave de acceso",
            "Verifica tu identidad",
            "Verificación en dos pasos",
            "Autenticación de dos factores",
        ]
        for text in INDICATORS:
            if self.is_element_visible(
                (By.XPATH, f'//*[contains(text(),"{text}")]'), timeout=2
            ):
                return True
        return False

    def is_logged_in(self):
        url = self.driver.current_url
        NOT_LOGGED_IN_FRAGMENTS = (
            "checkpoint", "two_step_verification",
            "recover", "forgot", "identify",
        )
        if any(f in url for f in NOT_LOGGED_IN_FRAGMENTS):
            return False
        # /login (bare login form) is not logged in, but /login/save-device/
        # and similar post-auth subpaths ARE (Facebook shows them after successful auth)
        if "/login" in url and "save-device" not in url and "device-based" not in url:
            return False
        if "facebook.com" not in url:
            return False

        if "mbasic.facebook.com" in url:
            # mbasic serves the login form at / (root URL) — email input = not logged in
            if self.is_element_visible(self.EMAIL_INPUT, timeout=3):
                return False
            # 2FA / method-selection screen at mbasic/# is NOT a logged-in state
            if self.is_on_2fa_screen():
                return False
            return True

        # m.facebook.com: SSR may briefly show a login form before the feed renders.
        # Wait for a feed indicator first; only fall back to email-input check after.
        for locator in self.FEED_LOCATORS:
            if self.is_element_visible(locator, timeout=5):
                return True
        # Feed didn't appear — check for login form with a longer timeout
        if self.is_element_visible(self.EMAIL_INPUT, timeout=5):
            return False
        # On m.facebook.com without a login form → assume logged in
        if "m.facebook.com" in url:
            return True
        return False

    def get_error_message(self, timeout=5):
        for sel in self.ERROR_LOCATORS_MBASIC:
            try:
                if self.is_element_visible(sel, timeout=timeout):
                    el = self.driver.find_element(*sel)
                    text = el.text.strip()
                    return text if text else "error_detected"
            except Exception:
                continue
        return None

    def is_on_login_page(self):
        url = self.driver.current_url
        login_in_url = "/login" in url and "save-device" not in url and "device-based" not in url
        return login_in_url or self.is_element_visible(self.EMAIL_INPUT, timeout=3)

    # ------------------------------------------------------------------
    # RECOVERY
    # ------------------------------------------------------------------

    def go_to_recovery(self):
        self.driver.get(MBASIC_LOGIN)
        time.sleep(2)
        RECOVERY_XPATHS = [
            '//*[contains(text(),"Olvidaste tu contraseña")]',
            '//*[contains(text(),"¿Olvidaste")]',
            '//*[contains(text(),"Forgot")]',
        ]
        RECOVERY_CSS = [
            'a[href*="recover"]',
            'a[href*="forgot"]',
            'a[href*="identify"]',
        ]
        for xpath in RECOVERY_XPATHS:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                ActionChains(self.driver).move_to_element(el).pause(0.2).click().perform()
                time.sleep(3)
                return True
            except Exception:
                continue
        for css in RECOVERY_CSS:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, css))
                )
                ActionChains(self.driver).move_to_element(el).pause(0.2).click().perform()
                time.sleep(3)
                return True
            except Exception:
                continue
        return False

    def is_on_recovery_page(self):
        url = self.driver.current_url
        url_indicators = any(
            kw in url for kw in ("recover", "forgot", "identify", "reset", "find")
        )
        text_indicators = any([
            self.is_text_visible("Encuentra tu cuenta", timeout=3),
            self.is_text_visible("Find your account", timeout=2),
            self.is_text_visible("Elige tu cuenta", timeout=2),
            self.is_text_visible("Ingresa tu número", timeout=2),
            self.is_text_visible("Buscar cuenta", timeout=2),
        ])
        return url_indicators or text_indicators

    # ------------------------------------------------------------------
    # LOGOUT
    # ------------------------------------------------------------------

    def logout(self):
        """
        Logout via mbasic link (native click). Falls back to deleting all cookies
        if the UI link can't be clicked — reliable enough for test purposes.
        """
        self.driver.get(MBASIC_HOME)
        time.sleep(2)

        LOGOUT_XPATHS = [
            '//*[contains(text(),"Cerrar sesión")]',
            '//*[contains(text(),"Log Out")]',
            '//*[contains(text(),"Logout")]',
        ]
        LOGOUT_CSS = ['a[href*="logout"]']

        for xpath in LOGOUT_XPATHS:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                ActionChains(self.driver).move_to_element(el).pause(0.2).click().perform()
                time.sleep(2)
                self._confirm_logout()
                if not self.is_logged_in():
                    return True
            except Exception:
                continue

        for css in LOGOUT_CSS:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, css))
                )
                ActionChains(self.driver).move_to_element(el).pause(0.2).click().perform()
                time.sleep(2)
                self._confirm_logout()
                if not self.is_logged_in():
                    return True
            except Exception:
                continue

        # Fallback: use CDP to clear ALL browser cookies (cross-domain, includes .facebook.com)
        print("[logout] UI logout failed — clearing all cookies via CDP")
        try:
            self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        except Exception:
            self.driver.delete_all_cookies()
        from utils.cookie_manager import COOKIE_FILE
        if COOKIE_FILE.exists():
            COOKIE_FILE.unlink()
        self.driver.get(MBASIC_LOGIN)
        time.sleep(3)
        return True

    def _confirm_logout(self):
        CONFIRM_XPATHS = [
            '//*[contains(text(),"Cerrar sesión")]',
            '//*[contains(text(),"Log Out")]',
        ]
        CONFIRM_CSS = ['input[name="logout"]']
        for xpath in CONFIRM_XPATHS:
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                el.click()
                time.sleep(2)
                return True
            except Exception:
                continue
        for css in CONFIRM_CSS:
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, css))
                )
                el.click()
                time.sleep(2)
                return True
            except Exception:
                continue
        return False
