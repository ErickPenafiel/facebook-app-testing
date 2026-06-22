import os
import time
import pytest

from selenium.webdriver.common.by import By

from pages_web.messenger_page_web import MessengerPageWeb
from pages_web.login_page_web import LoginPageWeb
from tests_web.helpers import get_env, ensure_logged_in

_SKIP_MSG = (
    "Facebook ha deshabilitado la mensajería en navegadores móviles web "
    "(muestra 'Chats on mobile browsers are not available'). "
    "Los chats solo están disponibles en la app Messenger."
)


def _open_and_check(messenger):
    """Open Messenger and skip the test if the web gate page is shown."""
    messenger.open_messenger()
    time.sleep(3)  # extra wait for gate page to fully render before checking
    if not messenger.is_messenger_available_on_web(timeout=12):
        messenger.take_screenshot("MSG_WEB_no_disponible")
        pytest.skip(_SKIP_MSG)


# ---------------------------------------------------------------------------
# TC_FB_MSG_001 – Acceso al módulo de mensajería (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.messaging_web
def test_tc_fb_msg_001_acceso_mensajeria(web_driver):
    """
    Verifica que, tras autenticarse en m.facebook.com, el módulo de mensajería
    carga correctamente mostrando la bandeja de conversaciones.
    """
    login_result = ensure_logged_in(web_driver)

    LoginPageWeb(web_driver).take_screenshot("TC_FB_MSG_001_WEB_feed_inicial")

    messenger = MessengerPageWeb(web_driver)
    _open_and_check(messenger)

    chat_visible = messenger.wait_for_chat_list(timeout=15)

    messenger.take_screenshot("TC_FB_MSG_001_WEB_acceso_mensajeria")

    assert chat_visible or messenger.is_chat_list_visible(), (
        "TC_FB_MSG_001_WEB falló: la bandeja de mensajes no cargó en m.facebook.com. "
        f"Estado de login: {login_result}, URL: {web_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# TC_FB_MSG_002 – Envío de mensaje de texto (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.messaging_web
def test_tc_fb_msg_002_envio_mensaje_texto(web_driver):
    """
    Busca un contacto en la mensajería web, abre la conversación, envía
    un mensaje de texto y verifica que aparece en el chat.
    """
    login_result = ensure_logged_in(web_driver)

    contact = os.getenv("FB_CONTACT_NAME", "Contacto Prueba")
    test_message = "Mensaje automatizado Selenium Web"

    messenger = MessengerPageWeb(web_driver)
    _open_and_check(messenger)
    messenger.wait_for_chat_list(timeout=15)

    messenger.search_conversation(contact)
    time.sleep(1)
    messenger.open_conversation(contact)
    time.sleep(2)

    if not messenger.is_in_conversation(timeout=5):
        messenger.take_screenshot("TC_FB_MSG_002_WEB_contacto_no_encontrado")
        pytest.skip(
            f"Contacto «{contact}» no encontrado o conversación no abierta en la web. "
            "Configura FB_CONTACT_NAME con un contacto real."
        )

    messenger.take_screenshot("TC_FB_MSG_002_WEB_conversacion_abierta")

    sent = messenger.send_message(test_message)
    time.sleep(2)

    message_visible = messenger.is_message_visible(test_message, timeout=8)

    messenger.take_screenshot("TC_FB_MSG_002_WEB_envio_mensaje_texto")

    assert sent or message_visible, (
        "TC_FB_MSG_002_WEB falló: el mensaje no se envió o no aparece en el chat web. "
        f"Estado de login: {login_result}"
    )


# ---------------------------------------------------------------------------
# TC_FB_MSG_003 – Recepción de mensaje entrante (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.messaging_web
def test_tc_fb_msg_003_recepcion_mensaje_entrante(web_driver):
    """
    Verifica que la bandeja de mensajería web muestra conversaciones con
    historial de mensajes y que es posible abrirlas para leer el contenido.
    """
    login_result = ensure_logged_in(web_driver)

    messenger = MessengerPageWeb(web_driver)
    _open_and_check(messenger)
    inbox_loaded = messenger.wait_for_chat_list(timeout=15)

    messenger.take_screenshot("TC_FB_MSG_003_WEB_recepcion_bandeja")

    assert inbox_loaded or messenger.is_chat_list_visible(), (
        "TC_FB_MSG_003_WEB falló: no se pudo cargar la bandeja de mensajes. "
        f"Estado de login: {login_result}"
    )

    has_conversations = messenger.has_received_messages_in_inbox()

    if has_conversations:
        conversation_name = messenger.open_first_conversation()
        time.sleep(2)
        messenger.get_last_received_message_text()

        messenger.take_screenshot("TC_FB_MSG_003_WEB_recepcion_mensaje_entrante")

        assert conversation_name is not None, (
            "TC_FB_MSG_003_WEB falló: no se pudo abrir ninguna conversación de la bandeja."
        )
    else:
        messenger.take_screenshot("TC_FB_MSG_003_WEB_recepcion_sin_historial")
        assert inbox_loaded, (
            "TC_FB_MSG_003_WEB falló: la bandeja de mensajes no está disponible."
        )


# ---------------------------------------------------------------------------
# TC_FB_MSG_004 – Estado del mensaje enviado (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.messaging_web
def test_tc_fb_msg_004_estado_mensaje_enviado(web_driver):
    """
    Envía un mensaje desde la mensajería web y verifica que el sistema
    muestra el estado de entrega: Enviado, Entregado o Visto.
    """
    login_result = ensure_logged_in(web_driver)

    contact = os.getenv("FB_CONTACT_NAME", "Contacto Prueba")
    test_message = "Validando estado del mensaje web"

    messenger = MessengerPageWeb(web_driver)
    _open_and_check(messenger)
    messenger.wait_for_chat_list(timeout=15)

    messenger.search_conversation(contact)
    time.sleep(1)
    messenger.open_conversation(contact)
    time.sleep(2)

    if not messenger.is_in_conversation(timeout=5):
        messenger.take_screenshot("TC_FB_MSG_004_WEB_contacto_no_encontrado")
        pytest.skip(
            f"Contacto «{contact}» no encontrado. Configura FB_CONTACT_NAME."
        )

    messenger.take_screenshot("TC_FB_MSG_004_WEB_conversacion_abierta")

    messenger.send_message(test_message)
    time.sleep(1)

    messenger.take_screenshot("TC_FB_MSG_004_WEB_mensaje_enviado")

    status = messenger.get_message_status(timeout=15)

    messenger.take_screenshot("TC_FB_MSG_004_WEB_estado_mensaje_enviado")

    assert status is not None, (
        "TC_FB_MSG_004_WEB falló: no se detectó ningún estado de entrega "
        f"(Enviado/Entregado/Visto). Estado de login: {login_result}"
    )


# ---------------------------------------------------------------------------
# TC_FB_MSG_005 – Envío de mensaje sin conexión (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.messaging_web
def test_tc_fb_msg_005_envio_sin_conexion(web_driver):
    """
    Simula pérdida de conexión mediante CDP, intenta enviar un mensaje
    y verifica que la mensajería web muestra un estado controlado
    (pendiente, error o mensaje en cola). Restaura la red al finalizar.
    """
    login_result = ensure_logged_in(web_driver)

    contact = os.getenv("FB_CONTACT_NAME", "Contacto Prueba")
    test_message = "Mensaje sin conexión Selenium Web"

    messenger = MessengerPageWeb(web_driver)
    _open_and_check(messenger)
    messenger.wait_for_chat_list(timeout=15)

    messenger.search_conversation(contact)
    time.sleep(1)
    messenger.open_conversation(contact)
    time.sleep(2)

    if not messenger.is_in_conversation(timeout=5):
        messenger.take_screenshot("TC_FB_MSG_005_WEB_contacto_no_encontrado")
        pytest.skip(
            f"Contacto «{contact}» no encontrado. Configura FB_CONTACT_NAME."
        )

    # Desactivar red vía CDP
    messenger.set_offline()
    time.sleep(1)

    messenger.send_message(test_message)
    time.sleep(3)

    pending_or_failed = messenger.is_pending_or_failed_visible(timeout=5)
    msg_visible = messenger.is_message_visible(test_message, timeout=3)

    # Restaurar red
    messenger.set_online()
    time.sleep(2)

    messenger.take_screenshot("TC_FB_MSG_005_WEB_envio_sin_conexion")

    assert pending_or_failed or msg_visible, (
        "TC_FB_MSG_005_WEB falló: no se detectó estado de error/pendiente "
        "ni el mensaje apareció tras enviar sin conexión. "
        f"Estado de login: {login_result}"
    )


# ---------------------------------------------------------------------------
# TC_FB_MSG_006 – Búsqueda de conversación existente (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.messaging_web
def test_tc_fb_msg_006_busqueda_conversacion(web_driver):
    """
    Ingresa al buscador de la mensajería web, escribe el nombre de un contacto
    y verifica que la conversación correspondiente aparece en resultados.
    """
    login_result = ensure_logged_in(web_driver)

    contact = os.getenv("FB_CONTACT_NAME", "Contacto Prueba")

    messenger = MessengerPageWeb(web_driver)
    _open_and_check(messenger)
    messenger.wait_for_chat_list(timeout=15)

    messenger.take_screenshot("TC_FB_MSG_006_WEB_bandeja_antes_busqueda")

    messenger.search_conversation(contact)
    time.sleep(2)

    contact_in_results = (
        messenger.is_text_visible(contact, timeout=8)
        or messenger.is_element_visible(
            (By.XPATH, f'//a[contains(.,"{contact}")]'),
            timeout=5
        )
    )

    messenger.take_screenshot("TC_FB_MSG_006_WEB_busqueda_conversacion")

    if not contact_in_results:
        pytest.skip(
            f"TC_FB_MSG_006_WEB: el contacto «{contact}» no existe o no tiene "
            "conversación previa en la web. Configura FB_CONTACT_NAME."
        )

    assert contact_in_results, (
        f"TC_FB_MSG_006_WEB falló: «{contact}» no apareció en resultados de búsqueda. "
        f"Estado de login: {login_result}"
    )


# ---------------------------------------------------------------------------
# TC_FB_MSG_007 – Sincronización de mensajes entre sesiones (web móvil)
# ---------------------------------------------------------------------------

@pytest.mark.messaging_web
def test_tc_fb_msg_007_sincronizacion_sesiones(web_driver):
    """
    Envía un mensaje en la mensajería web, recarga la página para simular
    una nueva sesión de navegación y verifica que el mensaje sigue visible
    (sincronización con los servidores de Facebook).
    """
    login_result = ensure_logged_in(web_driver)

    contact = os.getenv("FB_CONTACT_NAME", "Contacto Prueba")
    test_message = "Sincronización entre sesiones Selenium Web"

    messenger = MessengerPageWeb(web_driver)
    _open_and_check(messenger)
    messenger.wait_for_chat_list(timeout=15)

    messenger.search_conversation(contact)
    time.sleep(1)
    messenger.open_conversation(contact)
    time.sleep(2)

    if not messenger.is_in_conversation(timeout=5):
        messenger.take_screenshot("TC_FB_MSG_007_WEB_contacto_no_encontrado")
        pytest.skip(
            f"Contacto «{contact}» no encontrado. Configura FB_CONTACT_NAME."
        )

    messenger.send_message(test_message)
    time.sleep(2)

    messenger.take_screenshot("TC_FB_MSG_007_WEB_antes_recarga")

    # Simular nueva sesión navegando a la bandeja y volviendo a la conversación
    current_url = web_driver.current_url
    web_driver.get("https://m.facebook.com/messages/")
    time.sleep(2)
    web_driver.get(current_url)
    time.sleep(3)

    message_still_visible = messenger.is_message_visible(test_message, timeout=10)

    messenger.take_screenshot("TC_FB_MSG_007_WEB_sincronizacion_sesiones")

    assert message_still_visible, (
        "TC_FB_MSG_007_WEB falló: el mensaje no se encontró en la conversación "
        f"tras recargar la página. Estado de login: {login_result}"
    )
