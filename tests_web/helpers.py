import os
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

from pages_web.login_page_web import LoginPageWeb
from utils.cookie_manager import save_cookies, load_cookies


def get_env(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Variable de entorno requerida no configurada: {name}")
    return value


def _safe_is_logged_in(page):
    """Call is_logged_in() without crashing if the browser session died."""
    try:
        return page.is_logged_in()
    except WebDriverException:
        return False


def ensure_logged_in(driver, manual_2fa_wait=120):
    """
    Garantiza que hay una sesión de Facebook activa en el browser.

    Intenta en orden:
      1. Ya logueado (URL + indicadores de feed).
      2. Cookies guardadas de sesión anterior.
      3. Login completo con email + contraseña.
      4. Si Facebook pide 2FA, salta el test con instrucción de pre-autenticación.

    La espera activa de 2FA se eliminó porque el navegador colapsa después de ~38 s
    en la página two_step_verification con undetected-chromedriver.
    Para pre-autenticar ejecuta: uv run python tests_web/setup_session.py

    Retorna: 'logged_in'
    Salta el test si la autenticación no es posible sin interacción manual.
    """
    try:
        page = LoginPageWeb(driver)
    except WebDriverException:
        pytest.skip("Sesión del navegador inválida. Reinicia el runner.")

    if _safe_is_logged_in(page):
        return "logged_in"

    # Try loading saved session cookies
    if load_cookies(driver):
        try:
            driver.refresh()
            time.sleep(3)
        except WebDriverException:
            pass
        if _safe_is_logged_in(page):
            return "logged_in"

    # Full login flow
    try:
        page.login(get_env("FB_EMAIL"), get_env("FB_PASSWORD"))
        time.sleep(2)
    except WebDriverException as e:
        pytest.skip(f"El navegador se desconectó durante el login: {e}")

    if _safe_is_logged_in(page):
        save_cookies(driver)
        return "logged_in"

    try:
        url = driver.current_url
    except WebDriverException:
        pytest.skip("El navegador se cerró. Reinicia el runner.")

    if "checkpoint" in url:
        pytest.skip(
            "Facebook requiere verificación adicional (checkpoint). "
            "Completa la verificación manualmente y vuelve a ejecutar."
        )

    # 2FA detected — skip immediately to avoid crashing Chrome on the
    # two_step_verification page (38 s of CDP polling causes the session to die).
    # Pre-authenticate by running: uv run python tests_web/setup_session.py
    if page.is_on_2fa_screen():
        pytest.skip(
            "La cuenta requiere verificación 2FA que no puede completarse automáticamente. "
            "Pre-autenticate ejecutando: uv run python tests_web/setup_session.py"
        )

    return "timeout"


def ensure_logged_out(driver):
    """Garantiza que no hay sesión activa antes de un test de login."""
    try:
        page = LoginPageWeb(driver)
        if _safe_is_logged_in(page):
            page.logout()
            time.sleep(2)
        driver.get("https://mbasic.facebook.com/login")
        time.sleep(2)
    except WebDriverException:
        pass
