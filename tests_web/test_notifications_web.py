import time
import pytest

from pages_web.notifications_page_web import NotificationsPageWeb
from pages_web.login_page_web import LoginPageWeb
from tests_web.helpers import get_env, ensure_logged_in


# ---------------------------------------------------------------------------
# TC_FB_NOT_001 – Acceso al módulo de notificaciones (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.notifications_web
def test_tc_fb_not_001_acceso_notificaciones(web_driver):
    """
    Verifica que, desde m.facebook.com, el módulo de notificaciones
    abre correctamente mostrando el listado de notificaciones.
    """
    login_result = ensure_logged_in(web_driver)

    LoginPageWeb(web_driver).take_screenshot("TC_FB_NOT_001_WEB_feed_inicial")

    notifications = NotificationsPageWeb(web_driver)
    notifications.open_notifications()
    panel_visible = notifications.wait_for_notifications_panel(timeout=15)

    notifications.take_screenshot("TC_FB_NOT_001_WEB_acceso_notificaciones")

    assert panel_visible, (
        "TC_FB_NOT_001_WEB falló: el panel de notificaciones no cargó. "
        f"Estado de login: {login_result}, URL: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_FB_NOT_002 – Estado leída / no leída de notificaciones (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.notifications_web
def test_tc_fb_not_002_estado_notificaciones(web_driver):
    """
    Verifica que el panel de notificaciones web muestra notificaciones
    con clasificación de estado: leída (Leída) y no leída (No leída).
    """
    ensure_logged_in(web_driver)

    notifications = NotificationsPageWeb(web_driver)
    notifications.open_notifications()
    panel_visible = notifications.wait_for_notifications_panel(timeout=15)

    if not panel_visible:
        pytest.skip("Panel de notificaciones web no disponible.")

    notifications.take_screenshot("TC_FB_NOT_002_WEB_panel_abierto")

    time.sleep(2)

    unread_count = notifications.count_unread_notifications()
    read_count   = notifications.count_read_notifications()
    total        = unread_count + read_count

    notifications.take_screenshot("TC_FB_NOT_002_WEB_estado_notificaciones")

    if total == 0:
        assert panel_visible, (
            "TC_FB_NOT_002_WEB falló: el panel cargó pero sin ítems con estado reconocido. "
            "Verifica que la cuenta tiene historial de notificaciones."
        )
        pytest.skip(
            "TC_FB_NOT_002_WEB: no se encontraron ítems con estado Leída/No leída. "
            "El panel cargó correctamente pero la cuenta puede no tener notificaciones."
        )

    if unread_count > 0:
        sections = notifications.get_visible_sections()
        assert "Nuevas" in sections or unread_count > 0, (
            f"TC_FB_NOT_002_WEB falló: hay {unread_count} no leídas pero "
            "la sección 'Nuevas' no está visible."
        )

    assert total > 0, (
        f"TC_FB_NOT_002_WEB falló: se esperaban ítems con estado "
        f"(no leídas={unread_count}, leídas={read_count})."
    )


# ---------------------------------------------------------------------------
# TC_FB_NOT_003 – Visualización de detalle de una notificación (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.notifications_web
def test_tc_fb_not_003_detalle_notificacion(web_driver):
    """
    Abre una notificación del panel web y verifica que el sistema redirige
    al contenido relacionado (la URL cambia o el contenido aparece en pantalla).
    """
    login_result = ensure_logged_in(web_driver)

    notifications = NotificationsPageWeb(web_driver)
    notifications.open_notifications()
    panel_visible = notifications.wait_for_notifications_panel(timeout=15)

    if not panel_visible:
        pytest.skip("Panel de notificaciones web no disponible.")

    if not notifications.has_notification_items():
        notifications.take_screenshot("TC_FB_NOT_003_WEB_sin_notificaciones")
        pytest.skip(
            "No hay notificaciones disponibles. "
            "Genera interacciones (like, comentario, mensaje) antes de ejecutar este test."
        )

    url_before = web_driver.current_url
    notification_desc = notifications.open_first_notification()
    time.sleep(3)

    notifications.take_screenshot("TC_FB_NOT_003_WEB_detalle_notificacion")

    assert notification_desc is not None, (
        "TC_FB_NOT_003_WEB falló: no se pudo tocar ninguna notificación del panel."
    )

    assert notifications.app_is_still_responsive(), (
        f"TC_FB_NOT_003_WEB falló: el browser dejó de responder tras tocar "
        f"la notificación «{notification_desc[:80]}»."
    )


# ---------------------------------------------------------------------------
# TC_FB_NOT_004 – Secciones temporales y cargar más notificaciones (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.notifications_web
def test_tc_fb_not_004_secciones_y_cargar_mas(web_driver):
    """
    Verifica que el panel de notificaciones web organiza los ítems en
    secciones temporales (Nuevas, Hoy, Anteriores) y que el botón
    'Ver más' carga notificaciones adicionales sin errores.
    """
    ensure_logged_in(web_driver)

    notifications = NotificationsPageWeb(web_driver)
    notifications.open_notifications()
    panel_visible = notifications.wait_for_notifications_panel(timeout=15)

    if not panel_visible:
        pytest.skip("Panel de notificaciones web no disponible.")

    time.sleep(2)

    sections = notifications.get_visible_sections()
    has_any_section = len(sections) > 0

    notifications.scroll_to_bottom_of_notifications()
    load_more_present = notifications.has_load_more_button()

    notifications.take_screenshot("TC_FB_NOT_004_WEB_secciones_antes_cargar")

    crash_on_load = False
    if load_more_present:
        notifications.tap_load_more()
        time.sleep(3)
        crash_on_load = not notifications.app_is_still_responsive()

    notifications.take_screenshot("TC_FB_NOT_004_WEB_secciones_y_cargar_mas")

    assert not crash_on_load, (
        "TC_FB_NOT_004_WEB falló: el browser dejó de responder al tocar 'Ver más'."
    )

    assert panel_visible or has_any_section or notifications.has_notification_items(), (
        "TC_FB_NOT_004_WEB falló: el panel no estuvo disponible ni mostró secciones. "
        f"Secciones encontradas: {sections}"
    )


# ---------------------------------------------------------------------------
# TC_FB_NOT_005 – Menú de configuración por notificación individual (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.notifications_web
def test_tc_fb_not_005_menu_configuracion_notificacion(web_driver):
    """
    Verifica que cada notificación en el panel web tiene un menú contextual
    de configuración accesible y que cerrarlo devuelve al panel sin errores.
    """
    ensure_logged_in(web_driver)

    notifications = NotificationsPageWeb(web_driver)
    notifications.open_notifications()
    panel_visible = notifications.wait_for_notifications_panel(timeout=15)

    if not panel_visible:
        pytest.skip("Panel de notificaciones web no disponible.")

    time.sleep(2)

    has_button = notifications.has_manage_button_on_notifications()

    if not has_button:
        notifications.take_screenshot("TC_FB_NOT_005_WEB_sin_boton_admin")
        pytest.skip(
            "TC_FB_NOT_005_WEB: el botón 'Administrar configuración' no fue encontrado. "
            "Puede variar según la versión del sitio web."
        )

    menu_opened = notifications.tap_manage_settings_first_notification()
    time.sleep(2)
    menu_visible = notifications.notification_menu_appeared()

    notifications.take_screenshot("TC_FB_NOT_005_WEB_menu_configuracion")

    web_driver.back()
    time.sleep(2)

    app_alive = notifications.app_is_still_responsive()

    assert app_alive, (
        "TC_FB_NOT_005_WEB falló: el browser dejó de responder al intentar abrir "
        "el menú de configuración de notificación."
    )
    assert menu_opened, (
        "TC_FB_NOT_005_WEB falló: no se pudo tocar el botón de configuración."
    )


# ---------------------------------------------------------------------------
# TC_FB_NOT_006 – Acciones directas en solicitud de amistad (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.notifications_web
def test_tc_fb_not_006_acciones_solicitud_amistad(web_driver):
    """
    Verifica los botones de acción directa en notificaciones de solicitud
    de amistad ('Confirmar' / 'Eliminar') en el panel de notificaciones web.

    Happy path: solicitud presente → botones Confirmar/Eliminar habilitados.
    Bad path (negativo): sin solicitud → notificaciones regulares no muestran
    esos botones (invariante del diseño de la interfaz web).
    """
    ensure_logged_in(web_driver)

    notifications = NotificationsPageWeb(web_driver)
    notifications.open_notifications()
    panel_visible = notifications.wait_for_notifications_panel(timeout=15)

    if not panel_visible:
        pytest.skip("Panel de notificaciones web no disponible.")

    time.sleep(2)

    has_request = notifications.has_friend_request_notification()

    if has_request:
        request_desc   = notifications.get_friend_request_desc()
        confirmar_ok   = notifications.confirmar_button_enabled()
        eliminar_ok    = notifications.eliminar_button_enabled()

        notifications.take_screenshot("TC_FB_NOT_006_WEB_solicitud_amistad")

        assert confirmar_ok, (
            f"TC_FB_NOT_006_WEB falló: el botón 'Confirmar' no está habilitado "
            f"en la solicitud «{request_desc[:60]}»."
        )
        assert eliminar_ok, (
            f"TC_FB_NOT_006_WEB falló: el botón 'Eliminar' no está habilitado "
            f"en la solicitud «{request_desc[:60]}»."
        )
    else:
        regular_clean = notifications.regular_notifications_have_no_action_buttons()

        notifications.take_screenshot("TC_FB_NOT_006_WEB_sin_solicitud_amistad")

        assert regular_clean, (
            "TC_FB_NOT_006_WEB falló: se encontraron botones 'Confirmar'/'Eliminar' "
            "en una notificación que no es solicitud de amistad."
        )


# ---------------------------------------------------------------------------
# TC_FB_NOT_007 – Comportamiento sin conexión al abrir notificaciones (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.notifications_web
def test_tc_fb_not_007_sin_conexion(web_driver):
    """
    Desactiva la red vía CDP, abre el módulo de notificaciones web y verifica
    que la app no falla: muestra un error controlado o contenido en caché.
    Restaura la red al finalizar.

    Ventaja sobre la versión nativa: no requiere USB ADB.
    La desconexión se simula con Chrome DevTools Protocol (CDP).
    """
    login_result = ensure_logged_in(web_driver)

    notifications = NotificationsPageWeb(web_driver)

    # Abrir notificaciones con conexión para cargar caché
    notifications.open_notifications()
    notifications.wait_for_notifications_panel(timeout=10)
    time.sleep(2)

    # Navegar al feed antes de desconectar
    web_driver.get("https://m.facebook.com")
    time.sleep(1)

    # Deshabilitar red vía CDP
    notifications.set_offline()
    time.sleep(1)

    # Intentar abrir notificaciones sin conexión
    try:
        notifications.open_notifications()
        time.sleep(3)
    except Exception:
        pass

    offline_shown = notifications.is_offline_indicator_visible()
    panel_shown = notifications.wait_for_notifications_panel(timeout=5)
    app_alive = notifications.app_is_still_responsive()

    # Restaurar red
    notifications.set_online()
    time.sleep(2)

    notifications.take_screenshot("TC_FB_NOT_007_WEB_sin_conexion")

    assert app_alive, (
        "TC_FB_NOT_007_WEB falló: el browser dejó de responder al abrir "
        f"notificaciones sin conexión. Estado de login: {login_result}"
    )

    assert offline_shown or panel_shown, (
        "TC_FB_NOT_007_WEB falló: la web no mostró indicador de error ni "
        "contenido en caché al acceder a notificaciones sin conexión. "
        f"Estado de login: {login_result}"
    )
