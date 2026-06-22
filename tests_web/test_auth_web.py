import time
import pytest

from pages_web.login_page_web import LoginPageWeb
from tests_web.helpers import get_env, ensure_logged_in, ensure_logged_out


# ---------------------------------------------------------------------------
# TC_AUTH_001 – Login con credenciales válidas (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.auth_web
def test_tc_auth_001_login_valid(web_driver):
    """
    Verifica que el usuario puede iniciar sesión en m.facebook.com
    con credenciales válidas y que se redirige al feed principal.
    """
    login = LoginPageWeb(web_driver)
    ensure_logged_out(web_driver)

    login.take_screenshot("TC_AUTH_001_WEB_formulario_login")

    login.login(get_env("FB_EMAIL"), get_env("FB_PASSWORD"))
    time.sleep(3)

    is_logged_in = login.is_logged_in()
    is_2fa = login.is_on_2fa_screen()

    # Valid credentials produce either an immediate login OR a 2FA/passkey challenge.
    # Both are positive outcomes — invalid credentials show an error instead.
    is_ok = is_logged_in or is_2fa

    login.take_screenshot("TC_AUTH_001_WEB_login_valido")

    if is_logged_in:
        from utils.cookie_manager import save_cookies
        save_cookies(web_driver)

    assert is_ok, (
        "TC_AUTH_001_WEB falló: tras enviar credenciales válidas no se obtuvo ni "
        "inicio de sesión ni pantalla de verificación adicional. "
        f"URL actual: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_AUTH_002 – Login con contraseña incorrecta (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.auth_web
def test_tc_auth_002_login_invalid_password(web_driver):
    """
    Verifica que m.facebook.com muestra un mensaje de error cuando
    la contraseña ingresada no coincide con la cuenta.
    """
    login = LoginPageWeb(web_driver)
    ensure_logged_out(web_driver)

    login.login(get_env("FB_EMAIL"), get_env("FB_INVALID_PASSWORD"))
    time.sleep(3)

    error = login.get_error_message(timeout=8)
    still_on_login = login.is_on_login_page()
    is_ok = error is not None or still_on_login

    login.take_screenshot("TC_AUTH_002_WEB_password_incorrecta")

    assert is_ok, (
        "TC_AUTH_002_WEB falló: no se detectó mensaje de error con contraseña incorrecta. "
        f"URL actual: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_AUTH_003 – Login con usuario no registrado (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.auth_web
def test_tc_auth_003_login_unknown_user(web_driver):
    """
    Verifica que m.facebook.com muestra un error de cuenta no encontrada
    cuando se ingresa un correo electrónico no registrado.
    """
    login = LoginPageWeb(web_driver)
    ensure_logged_out(web_driver)

    login.take_screenshot("TC_AUTH_003_WEB_formulario_login")

    login.login(get_env("FB_UNKNOWN_USER"), get_env("FB_PASSWORD"))
    time.sleep(3)

    error = login.get_error_message(timeout=8)
    still_on_login = login.is_on_login_page()
    is_ok = error is not None or still_on_login

    login.take_screenshot("TC_AUTH_003_WEB_usuario_no_registrado")

    assert is_ok, (
        "TC_AUTH_003_WEB falló: no se detectó error con usuario no registrado. "
        f"URL actual: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_AUTH_004 – Campos vacíos en login (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.auth_web
def test_tc_auth_004_empty_fields(web_driver):
    """
    Verifica que m.facebook.com no permite enviar el formulario de login
    con los campos de correo y contraseña en blanco, mostrando una
    validación o permaneciendo en la misma página.
    """
    login = LoginPageWeb(web_driver)
    ensure_logged_out(web_driver)

    login.take_screenshot("TC_AUTH_004_WEB_formulario_login")

    login.login_empty_fields()
    time.sleep(2)

    still_on_login = login.is_on_login_page()
    error = login.get_error_message(timeout=3)
    is_ok = still_on_login or error is not None

    login.take_screenshot("TC_AUTH_004_WEB_campos_vacios")

    assert is_ok, (
        "TC_AUTH_004_WEB falló: el formulario permitió avanzar con campos vacíos. "
        f"URL actual: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_AUTH_005 – Recuperación de cuenta (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.auth_web
def test_tc_auth_005_account_recovery(web_driver):
    """
    Verifica que el enlace '¿Olvidaste tu contraseña?' en el formulario
    de login de m.facebook.com redirige al flujo de recuperación de cuenta.
    """
    login = LoginPageWeb(web_driver)
    ensure_logged_out(web_driver)

    login.take_screenshot("TC_AUTH_005_WEB_formulario_login")

    navigated = login.go_to_recovery()
    time.sleep(2)

    is_ok = login.is_on_recovery_page()

    login.take_screenshot("TC_AUTH_005_WEB_recuperacion_cuenta")

    assert is_ok, (
        "TC_AUTH_005_WEB falló: no se llegó a la página de recuperación de contraseña. "
        f"navigated={navigated}, URL actual: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_AUTH_006 – Cierre de sesión (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.auth_web
def test_tc_auth_006_logout(web_driver):
    """
    Verifica que el usuario puede cerrar sesión en m.facebook.com y que
    el sistema redirige a la página de inicio de sesión.
    """
    login = LoginPageWeb(web_driver)
    result = ensure_logged_in(web_driver)

    login.take_screenshot("TC_AUTH_006_WEB_main_fb_antes_logout")

    login.logout()
    time.sleep(2)

    is_ok = not login.is_logged_in()

    login.take_screenshot("TC_AUTH_006_WEB_cierre_sesion")

    assert is_ok, (
        "TC_AUTH_006_WEB falló: la sesión no se cerró correctamente. "
        f"Estado de login previo: {result}, URL actual: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_AUTH_007 – Persistencia de sesión (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Requiere aprobación manual de 2FA en el teléfono; la URL two_step_verification expira antes de poder automatizarse.")
@pytest.mark.auth_web
def test_tc_auth_007_session_persistence(web_driver):
    """
    Verifica que la sesión de Facebook persiste en el browser web cuando
    el usuario navega a otro sitio y regresa a m.facebook.com.
    Las cookies de sesión deben mantener al usuario autenticado.
    """
    login = LoginPageWeb(web_driver)
    ensure_logged_in(web_driver)

    login.take_screenshot("TC_AUTH_007_WEB_sesion_activa")

    # Simular "salir" de Facebook navegando a otro dominio
    web_driver.get("https://www.google.com")
    time.sleep(1)

    # Regresar a Facebook (wait longer for SSR hydration to complete)
    web_driver.get("https://m.facebook.com")
    time.sleep(6)

    is_ok = login.is_logged_in()

    login.take_screenshot("TC_AUTH_007_WEB_persistencia_sesion")

    assert is_ok, (
        "TC_AUTH_007_WEB falló: la sesión no persistió tras navegar fuera de Facebook. "
        f"URL actual: {web_driver.current_url}"
    )
